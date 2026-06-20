from __future__ import annotations

import json
from pathlib import Path

from expert_skill_system.compiler import KnowledgeCompiler
from expert_skill_system.core.models import ArtifactRef, SourceRef
from expert_skill_system.registry.workspace import Workspace
from expert_skill_system.runtime import BundleBuilder, PythonAdvisoryRuntime
from expert_skill_system.sources import SourceIngestionService


def _expert(path: Path) -> Path:
    path.write_text(
        """# Procedure
- MUST PROCEDURE: Parse one exact pinned dependency version.
- MUST PROCEDURE: Query the frozen OSV advisory record and affected range.
- MUST CONSTRAINT: Return unresolved when required evidence is missing.
- MUST NOT CONSTRAINT: Claim exploitability from advisory applicability.
- [UNSUPPORTED] Treat every warning as exploitable.
""",
        encoding="utf-8",
    )
    return path


def _osv(path: Path, *, fixed: str) -> Path:
    path.write_text(
        json.dumps(
            {
                "vulns": [
                    {
                        "id": "PYSEC-TEST-1",
                        "affected": [
                            {
                                "package": {"ecosystem": "PyPI", "name": "requests"},
                                "ranges": [{"type": "ECOSYSTEM", "events": [{"introduced": "0"}, {"fixed": fixed}]}],
                            }
                        ],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    return path


def _bundle(tmp_path: Path, *, fixed: str = "2.32.0"):
    workspace = Workspace.open(tmp_path / ".eskill")
    ingestion = SourceIngestionService(workspace)
    expert = ingestion.add(
        SourceRef(
            source_id="expert",
            uri=str(_expert(tmp_path / "expert.md")),
            adapter_type="expert-document",
            visibility="build",
        )
    )
    osv = ingestion.add(
        SourceRef(
            source_id=f"osv-{fixed}",
            uri=str(_osv(tmp_path / f"osv-{fixed}.json", fixed=fixed)),
            adapter_type="osv-snapshot",
            visibility="build",
        )
    )
    build = KnowledgeCompiler(workspace).build(expert_snapshot=expert, structured_snapshots=(osv,))
    bundle = BundleBuilder(workspace).build(build)
    return workspace, expert, build, bundle


def _inputs(tmp_path: Path, requirement: str):
    requirements = tmp_path / f"requirements-{abs(hash(requirement))}.txt"
    environment = tmp_path / "environment.json"
    requirements.write_text(requirement + "\n", encoding="utf-8")
    environment.write_text(json.dumps({"python_version": "3.11", "sys_platform": "win32"}), encoding="utf-8")
    return requirements, environment


def test_snapshot_change_changes_bundle_but_not_skill_identity(tmp_path: Path) -> None:
    workspace, expert, build_a, bundle_a = _bundle(tmp_path, fixed="2.32.0")
    ingestion = SourceIngestionService(workspace)
    osv_b = ingestion.add(
        SourceRef(
            source_id="osv-b",
            uri=str(_osv(tmp_path / "osv-b.json", fixed="2.31.0")),
            adapter_type="osv-snapshot",
            visibility="build",
        )
    )
    build_b = KnowledgeCompiler(workspace).build(expert_snapshot=expert, structured_snapshots=(osv_b,))
    bundle_b = BundleBuilder(workspace).build(build_b)

    assert build_a.skill_ir_ref["digest"] == build_b.skill_ir_ref["digest"]
    assert build_a.knowledge_projection_ref["digest"] != build_b.knowledge_projection_ref["digest"]
    assert bundle_a.bundle_digest != bundle_b.bundle_digest


def test_runtime_records_applicable_out_of_range_missing_and_parse_error(tmp_path: Path) -> None:
    workspace, _, _, bundle = _bundle(tmp_path)
    workspace.metadata.change_binding(
        binding_key="python-advisory",
        target_digest=bundle.bundle_digest,
        expected_generation=0,
        event_type="promote",
    )
    runtime = PythonAdvisoryRuntime(workspace)

    requirements, environment = _inputs(tmp_path, "requests==2.31.0")
    applicable = runtime.run(requirements_path=requirements, environment_path=environment, advisory_id="PYSEC-TEST-1")
    assert applicable.execution_status == "completed"
    assert applicable.domain_outcome.decision.verdict == "advisory_applicable"
    assert applicable.domain_outcome.decision.reason_codes == ("VERSION_IN_RANGE",)

    requirements, environment = _inputs(tmp_path, "requests==2.32.0")
    fixed = runtime.run(requirements_path=requirements, environment_path=environment, advisory_id="PYSEC-TEST-1")
    assert fixed.domain_outcome.decision.verdict == "advisory_not_applicable"
    assert fixed.domain_outcome.decision.reason_codes == ("VERSION_OUT_OF_RANGE",)

    missing = runtime.run(requirements_path=requirements, environment_path=environment, advisory_id="PYSEC-MISSING")
    assert missing.execution_status == "completed"
    assert missing.domain_outcome.decision.verdict == "unresolved"
    assert missing.domain_outcome.decision.reason_codes == ("ADVISORY_NOT_FOUND",)

    requirements, environment = _inputs(tmp_path, "requests>=2")
    parse_error = runtime.run(requirements_path=requirements, environment_path=environment, advisory_id="PYSEC-TEST-1")
    assert parse_error.execution_status == "completed"
    assert parse_error.domain_outcome.task_status == "parse_error"
    assert parse_error.domain_outcome.parse_diagnostics

    requirements, environment = _inputs(tmp_path, "flask==3.0.0")
    absent = runtime.run(requirements_path=requirements, environment_path=environment, advisory_id="PYSEC-TEST-1")
    assert absent.domain_outcome.decision.reason_codes == ("PACKAGE_NOT_PRESENT",)

    requirements, environment = _inputs(tmp_path, 'requests==2.31.0; python_version < "3.0"')
    marker_false = runtime.run(requirements_path=requirements, environment_path=environment, advisory_id="PYSEC-TEST-1")
    assert marker_false.domain_outcome.decision.reason_codes == ("MARKER_FALSE",)

    requirements, environment = _inputs(tmp_path, "requests===legacy-build")
    unknown = runtime.run(requirements_path=requirements, environment_path=environment, advisory_id="PYSEC-TEST-1")
    assert unknown.domain_outcome.decision.verdict == "unresolved"
    assert unknown.domain_outcome.decision.reason_codes == ("VERSION_UNKNOWN",)


def test_session_trace_pins_bundle_and_contains_query_provenance(tmp_path: Path) -> None:
    workspace, _, _, bundle = _bundle(tmp_path)
    requirements, environment = _inputs(tmp_path, "requests==2.31.0")
    result = PythonAdvisoryRuntime(workspace).run(
        requirements_path=requirements,
        environment_path=environment,
        advisory_id="PYSEC-TEST-1",
        bundle_digest=bundle.bundle_digest,
    )
    session = workspace.metadata.get_session(result.session_id)
    trace_ref = ArtifactRef.from_dict(session["payload"]["trace_ref"])
    trace = workspace.artifacts.get_json(trace_ref)

    assert session["bundle_digest"] == bundle.bundle_digest
    assert trace["bundle_digest"] == bundle.bundle_digest
    assert trace["evidence_envelope"]["snapshot_digest"].startswith("sha256:")
    assert trace["evidence_envelope"]["query_contract_digest"].startswith("sha256:")
    assert trace["evidence_envelope"]["result_digest"].startswith("sha256:")


def test_corrupt_hard_dependency_is_runtime_failure_not_unresolved(tmp_path: Path) -> None:
    workspace, _, _, bundle = _bundle(tmp_path)
    dependency_ref = ArtifactRef.from_dict(bundle.manifest["dependency_manifest_ref"])
    dependencies = workspace.artifacts.get_json(dependency_ref)
    victim = ArtifactRef.from_dict(dependencies["hard_runtime_dependencies"][0])
    workspace.artifacts.path_for_digest(victim.digest).unlink()
    requirements, environment = _inputs(tmp_path, "requests==2.31.0")

    result = PythonAdvisoryRuntime(workspace).run(
        requirements_path=requirements,
        environment_path=environment,
        advisory_id="PYSEC-TEST-1",
        bundle_digest=bundle.bundle_digest,
    )

    assert result.execution_status == "runtime_failure"
    assert result.domain_outcome is None
    assert result.failure.category == "bundle_integrity"


def test_missing_knowledge_binding_blocks_without_memory_fallback(tmp_path: Path) -> None:
    workspace, _, _, bundle = _bundle(tmp_path)
    unbound_manifest = {**bundle.manifest, "knowledge_access_binding_refs": []}
    unbound_ref = workspace.put_json(unbound_manifest, schema_version="release_bundle.v1")
    requirements, environment = _inputs(tmp_path, "requests==2.31.0")

    result = PythonAdvisoryRuntime(workspace).run(
        requirements_path=requirements,
        environment_path=environment,
        advisory_id="PYSEC-TEST-1",
        bundle_digest=unbound_ref.digest,
    )

    assert result.execution_status == "blocked"
    assert result.failure.reason_codes == ("KNOWLEDGE_BINDING_UNAVAILABLE",)
    assert result.domain_outcome is None
