from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from expert_skill_system.compiler import KnowledgeCompiler
from expert_skill_system.compiler.models import CompilerBuild
from expert_skill_system.core.models import ArtifactRef, SourceRef
from expert_skill_system.deployment import DeploymentService, PromotionRejected
from expert_skill_system.registry.workspace import Workspace
from expert_skill_system.runtime import BundleBuilder, PythonAdvisoryRuntime
from expert_skill_system.sources import SourceIngestionService


def _write_expert(path: Path) -> Path:
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


def _write_osv(path: Path, fixed: str) -> Path:
    path.write_text(
        json.dumps(
            {
                "vulns": [
                    {
                        "id": "PYSEC-ROLLBACK-1",
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


def _candidate(workspace: Workspace, ingestion: SourceIngestionService, expert, path: Path, fixed: str, build_id: str):
    snapshot = ingestion.add(
        SourceRef(source_id=f"osv-{build_id}", uri=str(_write_osv(path, fixed)), adapter_type="osv-snapshot", visibility="build")
    )
    build = KnowledgeCompiler(workspace).build(
        expert_snapshot=expert, structured_snapshots=(snapshot,), build_id=build_id
    )
    return build, BundleBuilder(workspace).build(build)


def _unsafe_candidate(workspace: Workspace, base_build: CompilerBuild) -> tuple[CompilerBuild, object]:
    skill = workspace.artifacts.get_json(ArtifactRef.from_dict(base_build.skill_ir_ref))
    skill["invocation"]["task_family"] = "all-security"
    unsafe_skill_ref = workspace.put_json(skill, schema_version="skill_ir.v1")
    original_attestation = workspace.artifacts.get_json(ArtifactRef.from_dict(base_build.attestation_ref))
    original_attestation["subject_digests"]["skill_ir"] = unsafe_skill_ref.digest
    unsafe_attestation_ref = workspace.put_json(original_attestation, schema_version="build_attestation.v1")
    unsafe_build = replace(
        base_build,
        build_id="candidate-c-unsafe",
        skill_ir_ref=unsafe_skill_ref.to_dict(),
        attestation_ref=unsafe_attestation_ref.to_dict(),
    )
    workspace.metadata.add_build_record(build_id=unsafe_build.build_id, status="candidate", payload=unsafe_build.to_dict())
    return unsafe_build, BundleBuilder(workspace).build(unsafe_build)


def test_promotion_rejection_and_explicit_full_bundle_rollback(tmp_path: Path) -> None:
    workspace = Workspace.open(tmp_path / ".eskill")
    ingestion = SourceIngestionService(workspace)
    expert = ingestion.add(
        SourceRef(
            source_id="expert",
            uri=str(_write_expert(tmp_path / "expert.md")),
            adapter_type="expert-document",
            visibility="build",
        )
    )
    build_a, bundle_a = _candidate(workspace, ingestion, expert, tmp_path / "osv-a.json", "2.32.0", "candidate-a")
    build_b, bundle_b = _candidate(workspace, ingestion, expert, tmp_path / "osv-b.json", "2.31.0", "candidate-b")
    _, bundle_c = _unsafe_candidate(workspace, build_b)
    deployment = DeploymentService(workspace)

    assert deployment.validate(bundle_a.bundle_digest, regression_pass=True, negative_control_pass=True).status == "pass"
    active_a = deployment.promote(bundle_a.bundle_digest, expected_generation=0)
    assert active_a.generation == 1
    assert deployment.validate(bundle_b.bundle_digest, regression_pass=True, negative_control_pass=True).status == "pass"
    active_b = deployment.promote(bundle_b.bundle_digest, expected_generation=1)
    assert active_b.bundle_digest == bundle_b.bundle_digest

    unsafe_evaluation = deployment.validate(bundle_c.bundle_digest, regression_pass=True, negative_control_pass=True)
    assert unsafe_evaluation.status == "fail"
    assert any(item["check"] == "scope_containment" and item["status"] == "fail" for item in unsafe_evaluation.checks)
    with pytest.raises(PromotionRejected):
        deployment.promote(bundle_c.bundle_digest, expected_generation=2)
    assert workspace.metadata.get_active_binding("python-advisory").bundle_digest == bundle_b.bundle_digest

    workspace.metadata.start_session(
        session_id="running-on-b",
        binding_key="python-advisory",
        bundle_digest=bundle_b.bundle_digest,
        payload={"phase": "running"},
    )
    rolled_back = deployment.rollback(bundle_a.bundle_digest, expected_generation=2)
    assert rolled_back.generation == 3
    assert rolled_back.bundle_digest == bundle_a.bundle_digest
    assert workspace.metadata.get_session("running-on-b")["bundle_digest"] == bundle_b.bundle_digest

    requirements = tmp_path / "requirements.txt"
    environment = tmp_path / "environment.json"
    requirements.write_text("requests==2.31.0\n", encoding="utf-8")
    environment.write_text(json.dumps({"python_version": "3.11"}), encoding="utf-8")
    new_session = PythonAdvisoryRuntime(workspace).run(
        requirements_path=requirements,
        environment_path=environment,
        advisory_id="PYSEC-ROLLBACK-1",
    )
    assert new_session.bundle_digest == bundle_a.bundle_digest
    assert new_session.domain_outcome.decision.verdict == "advisory_applicable"

    history = workspace.metadata.deployment_history("python-advisory")
    assert [item["event_type"] for item in history] == ["promote", "promote", "reject", "rollback"]
    assert all(item["to_digest"] != bundle_c.bundle_digest for item in history if item["event_type"] in {"promote", "rollback"})
    assert history[-1]["to_digest"] == bundle_a.bundle_digest
    assert build_a.skill_ir_ref["digest"] == build_b.skill_ir_ref["digest"]
