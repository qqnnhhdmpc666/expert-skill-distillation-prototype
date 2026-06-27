from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any

from ..compiler import KnowledgeCompiler
from ..compiler.repo_level_bundle_builder import RepoLevelBundleBuilder
from ..core.models import ArtifactRef, SourceRef, SourceSnapshot, utc_now
from ..deployment import DeploymentService
from ..evaluation.repo_eval_harness import run_repo_level_eval
from ..registry.workspace import Workspace
from ..runtime import BundleBuilder, PythonAdvisoryRuntime
from ..runtime.release_bundle_resolver import resolve_release_bundle
from ..sources import SourceIngestionService
from .lifecycle_report import (
    build_aggregate_report,
    build_bundle_matrix,
    build_claim_boundary_matrix,
    render_aggregate_report,
    write_lifecycle_outputs,
)
from .skill_family_registry import load_skill_family_registry


def run_skill_family_lifecycle(
    *,
    family_registry: Path,
    families: list[str],
    output_dir: Path,
) -> dict[str, Any]:
    registry = load_skill_family_registry(family_registry)
    selected = registry.by_family(families)
    output_dir.mkdir(parents=True, exist_ok=True)
    family_builds: list[dict[str, Any]] = []
    active_bindings: list[dict[str, Any]] = []
    eval_runs: list[dict[str, Any]] = []
    for spec in selected:
        family_dir = output_dir / "families" / spec.skill_family
        family_dir.mkdir(parents=True, exist_ok=True)
        if spec.family_type == "python_advisory":
            build_row, binding_row, eval_row = _run_python_advisory_family(spec, family_dir)
        elif spec.family_type == "repo_level_dependency_use_triage":
            build_row, binding_row, eval_row = _run_repo_level_family(spec, family_dir)
        else:
            raise ValueError(f"unsupported family_type: {spec.family_type}")
        build_row["evaluation_status"] = eval_row["evaluation_status"]
        family_builds.append(build_row)
        active_bindings.append(binding_row)
        eval_runs.append(eval_row)
    bundle_matrix = build_bundle_matrix(family_builds)
    claim_boundary_matrix = build_claim_boundary_matrix(
        family_builds=family_builds,
        eval_runs=eval_runs,
        global_blocked_claims=list(registry.global_blocked_claims),
    )
    aggregate = build_aggregate_report(
        family_builds=family_builds,
        active_bindings=active_bindings,
        eval_runs=eval_runs,
        bundle_matrix=bundle_matrix,
        claim_boundary_matrix=claim_boundary_matrix,
        output_dir=output_dir,
    )
    manifest = {
        "schema_version": "multi_skill_family_lifecycle_manifest.v1",
        "created_at": utc_now(),
        "family_registry": str(family_registry),
        "requested_families": families,
        "selected_families": [spec.to_dict() for spec in selected],
        "output_dir": str(output_dir),
    }
    artifacts = {
        "lifecycle_manifest.json": manifest,
        "family_builds.json": {"schema_version": "family_builds.v1", "families": family_builds},
        "active_bindings.json": {"schema_version": "family_active_bindings.v1", "bindings": active_bindings},
        "eval_runs.jsonl": eval_runs,
        "bundle_matrix.json": bundle_matrix,
        "claim_boundary_matrix.json": claim_boundary_matrix,
        "aggregate_lifecycle_report.json": aggregate,
        "aggregate_lifecycle_report.md": render_aggregate_report(aggregate, family_builds, eval_runs),
    }
    write_lifecycle_outputs(output_dir, artifacts)
    return aggregate


def _run_python_advisory_family(spec: Any, family_dir: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    workspace = Workspace.open(Path(spec.default_state_dir))
    root = Path(spec.data_dir or "data/v1_walking_skeleton").resolve()
    ingestion = SourceIngestionService(workspace)
    expert = ingestion.add(
        SourceRef(
            source_id="expert-python-advisory-review",
            uri=str(root / "expert_spec" / "python_advisory_review.md"),
            adapter_type="expert-document",
            visibility="build",
            metadata={"source_url": "locally-authored-v1-specification", "license": "project-license"},
        )
    )
    osv = ingestion.add(
        SourceRef(
            source_id="osv-pysec-2018-28",
            uri=str(root / "osv" / "PYSEC-2018-28.json"),
            adapter_type="osv-snapshot",
            visibility="build",
            metadata={"source_url": "https://api.osv.dev/v1/vulns/PYSEC-2018-28"},
        )
    )
    latest_expert = _latest_snapshot(workspace, "expert-document", fallback=expert)
    latest_osv = _latest_snapshot(workspace, "osv-snapshot", fallback=osv)
    build = KnowledgeCompiler(workspace).build(expert_snapshot=latest_expert, structured_snapshots=(latest_osv,))
    bundle = BundleBuilder(workspace).build(build)
    workspace.metadata.add_build_record(
        build_id=build.build_id,
        status="candidate",
        payload=build.to_dict(),
        candidate_bundle_digest=bundle.bundle_digest,
    )
    deployment = DeploymentService(workspace)
    attestation = deployment.validate(bundle.bundle_digest, regression_pass=True, negative_control_pass=True)
    active = workspace.metadata.get_active_binding(spec.binding_key)
    if active is None:
        active = deployment.promote(bundle.bundle_digest, expected_generation=0)
    elif active.bundle_digest != bundle.bundle_digest:
        active = deployment.promote(bundle.bundle_digest, expected_generation=active.generation)
    envelope = PythonAdvisoryRuntime(workspace).run(
        requirements_path=root / "runtime_inputs" / "requirements.txt",
        environment_path=root / "runtime_inputs" / "environment.json",
        advisory_id="PYSEC-2018-28",
    )
    resolution = resolve_release_bundle(state_dir=Path(spec.default_state_dir), use_active_binding=True, binding_key=spec.binding_key)
    build_row = _family_build_row(
        spec=spec,
        resolution=resolution,
        active_generation=active.generation,
        build_status="pass" if attestation.status == "pass" else "partial",
        evidence_requirements=_evidence_requirements(workspace, resolution),
        evidence_paths=[str(family_dir / "python_advisory_runtime_smoke.json")],
    )
    eval_row = {
        "schema_version": "family_eval_run.v1",
        "skill_family": spec.skill_family,
        "evaluation_status": "partial_no_family_eval_harness",
        "runtime_smoke_status": "pass" if envelope.execution_status == "completed" else envelope.execution_status,
        "reason": "python-advisory has a deterministic runtime smoke but no repo-level-style family eval harness in this orchestration step",
        "evidence_paths": [str(family_dir / "python_advisory_runtime_smoke.json")],
    }
    _write_json(family_dir / "build_result.json", build_row)
    _write_json(
        family_dir / "python_advisory_runtime_smoke.json",
        {
            "schema_version": "python_advisory_family_runtime_smoke.v1",
            "execution_status": envelope.execution_status,
            "bundle_digest": bundle.bundle_digest,
            "attestation_status": attestation.status,
            "active_binding": active.to_dict(),
        },
    )
    return build_row, _active_binding_row(spec, active.bundle_digest, active.generation), eval_row


def _run_repo_level_family(spec: Any, family_dir: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    workspace = Workspace.open(Path(spec.default_state_dir))
    result = RepoLevelBundleBuilder(workspace).build(
        data_dir=Path(spec.data_dir or "data/repo_level_bundle"),
        skill_family=spec.skill_family,
        promote=True,
    )
    # Keep the lifecycle nesting shallow enough for Windows path limits while
    # preserving the harness' own task/trajectory artifact layout.
    eval_dir = family_dir / "eval"
    summary = run_repo_level_eval(
        task_registry=Path(spec.task_registry or "data/repo_security_tasks/registry.json"),
        output_dir=eval_dir,
        state_dir=Path(spec.default_state_dir),
        use_active_binding=True,
        binding_key=spec.binding_key,
    )
    resolution = resolve_release_bundle(state_dir=Path(spec.default_state_dir), use_active_binding=True, binding_key=spec.binding_key)
    build_row = _family_build_row(
        spec=spec,
        resolution=resolution,
        active_generation=result.active_binding_generation,
        build_status=result.status,
        evidence_requirements=_evidence_requirements(workspace, resolution),
        evidence_paths=[str(family_dir / "build_result.json"), str(eval_dir / "run_summary.json")],
    )
    eval_row = {
        "schema_version": "family_eval_run.v1",
        "skill_family": spec.skill_family,
        "evaluation_status": "pass" if summary["fail_count"] == 0 else "failed",
        "task_count": summary["task_count"],
        "pass_count": summary["pass_count"],
        "fail_count": summary["fail_count"],
        "bundle_attachment_mode": summary["bundle_attachment_mode"],
        "skill_family_from_harness": summary.get("skill_family"),
        "evidence_paths": [str(eval_dir / "run_summary.json"), str(eval_dir / "aggregate_report.json")],
    }
    _write_json(family_dir / "build_result.json", result.to_dict())
    return build_row, _active_binding_row(spec, result.bundle_digest, result.active_binding_generation), eval_row


def _family_build_row(
    *,
    spec: Any,
    resolution: dict[str, Any],
    active_generation: int | None,
    build_status: str,
    evidence_requirements: list[str],
    evidence_paths: list[str],
) -> dict[str, Any]:
    return {
        "schema_version": "family_build.v1",
        "skill_family": spec.skill_family,
        "bundle_manifest_skill_family": resolution.get("skill_family"),
        "builder": spec.builder_entrypoint,
        "family_type": spec.family_type,
        "state_dir": spec.default_state_dir,
        "binding_key": spec.binding_key,
        "bundle_digest": resolution.get("bundle_digest"),
        "skill_digest": resolution.get("skill_digest"),
        "skill_artifact_digest": resolution.get("skill_artifact_digest"),
        "knowledge_projection_digest": resolution.get("knowledge_projection_digest"),
        "knowledge_access_binding_digest": resolution.get("knowledge_access_binding_digest"),
        "provider_policy_digest": resolution.get("provider_policy_digest"),
        "active_binding_generation": active_generation,
        "build_status": build_status,
        "evaluation_status": "pending",
        "evidence_requirements": evidence_requirements,
        "claim_boundary": {
            "allowed_claims": list(spec.claim_scope),
            "blocked_claims": list(spec.blocked_claims),
        },
        "evidence_paths": evidence_paths,
    }


def _active_binding_row(spec: Any, bundle_digest: str, generation: int | None) -> dict[str, Any]:
    return {
        "schema_version": "family_active_binding.v1",
        "skill_family": spec.skill_family,
        "binding_key": spec.binding_key,
        "bundle_digest": bundle_digest,
        "active_binding_generation": generation,
    }


def _evidence_requirements(workspace: Workspace, resolution: dict[str, Any]) -> list[str]:
    manifest = resolution.get("bundle_manifest") or {}
    skill_refs = manifest.get("skill_ir_refs", [])
    if not skill_refs:
        return []
    skill = workspace.artifacts.get_json(ArtifactRef.from_dict(skill_refs[0]))
    return [
        str(item.get("semantic_requirement"))
        for item in skill.get("knowledge_requirements", [])
        if item.get("semantic_requirement")
    ]


def _latest_snapshot(workspace: Workspace, adapter_type: str, *, fallback: SourceSnapshot) -> SourceSnapshot:
    candidates = [item for item in workspace.metadata.source_snapshots() if item["adapter_type"] == adapter_type]
    if not candidates:
        return fallback
    row = candidates[-1]
    ref = workspace.metadata.artifact_ref(row["snapshot_digest"])
    snapshot = SourceSnapshot.from_dict(workspace.artifacts.get_json(ref))
    return replace(snapshot, metadata={**snapshot.metadata, "snapshot_ref": ref.to_dict()})


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    import json

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
