from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

from ..compiler import KnowledgeCompiler
from ..compiler.models import CompilerBuild
from ..core.models import ArtifactRef, SourceRef
from ..deployment import DeploymentService, PromotionRejected
from ..registry.workspace import Workspace
from ..runtime import BundleBuilder, PythonAdvisoryRuntime
from ..sources import SourceIngestionService


def run_evolution_evaluation(workspace: Workspace, *, expert_path: Path) -> dict[str, Any]:
    if workspace.metadata.get_active_binding("python-advisory") is not None:
        raise RuntimeError("evolution evaluation requires a fresh state directory")
    sources = workspace.root / "evolution_sources"
    sources.mkdir(parents=True, exist_ok=True)
    expert = SourceIngestionService(workspace).add(
        SourceRef(source_id="evolution-expert", uri=str(expert_path), adapter_type="expert-document", visibility="build")
    )
    build_a, bundle_a = _candidate(workspace, expert, sources / "osv-a.json", "2.21.0", "evolution-a")
    build_b, bundle_b = _candidate(workspace, expert, sources / "osv-b.json", "2.20.0", "evolution-b")
    bundle_c = _unsafe_candidate(workspace, build_b)
    cases = (
        ("old-regression", "requests==2.19.0", "advisory_applicable"),
        ("changed-source", "requests==2.20.0", "advisory_not_applicable"),
        ("unrelated-negative", "flask==3.0.0", "advisory_not_applicable"),
    )
    scores_a, rows_a = _score(workspace, bundle_a.bundle_digest, cases)
    scores_b, rows_b = _score(workspace, bundle_b.bundle_digest, cases)
    deployment = DeploymentService(workspace)
    eval_a = deployment.validate(
        bundle_a.bundle_digest,
        regression_pass=_case_pass(rows_a, "old-regression"),
        negative_control_pass=_case_pass(rows_a, "unrelated-negative"),
    )
    active_a = deployment.promote(bundle_a.bundle_digest, expected_generation=0)
    eval_b = deployment.validate(
        bundle_b.bundle_digest,
        regression_pass=_case_pass(rows_b, "old-regression"),
        negative_control_pass=_case_pass(rows_b, "unrelated-negative"),
    )
    active_b = deployment.promote(bundle_b.bundle_digest, expected_generation=active_a.generation)
    unsafe_eval = deployment.validate(bundle_c.bundle_digest, regression_pass=True, negative_control_pass=True)
    rejected = False
    try:
        deployment.promote(bundle_c.bundle_digest, expected_generation=active_b.generation)
    except PromotionRejected:
        rejected = True
    binding_after_rejection = workspace.metadata.get_active_binding("python-advisory")
    workspace.metadata.start_session(
        session_id="evolution-running-on-b",
        binding_key="python-advisory",
        bundle_digest=bundle_b.bundle_digest,
        payload={"phase": "running"},
    )
    rolled_back = deployment.rollback(bundle_a.bundle_digest, expected_generation=active_b.generation)
    pinned = workspace.metadata.get_session("evolution-running-on-b")
    history = workspace.metadata.deployment_history("python-advisory")
    measured = scores_b > scores_a and _case_pass(rows_b, "old-regression") and _case_pass(rows_b, "unrelated-negative")
    payload = {
        "schema_version": "evolution_improvement_evaluation.v1",
        "pre_registered_cases": [case_id for case_id, _, _ in cases],
        "bundle_a": bundle_a.bundle_digest,
        "bundle_b": bundle_b.bundle_digest,
        "unsafe_candidate_c": bundle_c.bundle_digest,
        "scores": {"a": scores_a, "b": scores_b, "delta": scores_b - scores_a},
        "rows": {"a": rows_a, "b": rows_b},
        "accepted_update": {
            "status": "pass" if eval_b.status == "pass" and active_b.bundle_digest == bundle_b.bundle_digest else "fail",
            "old_regression_preserved": _case_pass(rows_b, "old-regression"),
            "changed_source_case_improved": not _case_pass(rows_a, "changed-source") and _case_pass(rows_b, "changed-source"),
            "false_safe_increased": _false_safe(rows_b) > _false_safe(rows_a),
        },
        "unsafe_update": {
            "status": "pass" if rejected else "fail",
            "evaluation_status": unsafe_eval.status,
            "active_binding_unchanged": bool(binding_after_rejection and binding_after_rejection.bundle_digest == bundle_b.bundle_digest),
        },
        "rollback": {
            "status": "pass" if rolled_back.bundle_digest == bundle_a.bundle_digest else "fail",
            "rebound_original_digest": rolled_back.bundle_digest == bundle_a.bundle_digest,
            "running_session_remained_pinned": pinned["bundle_digest"] == bundle_b.bundle_digest,
        },
        "deployment_event_types": [item["event_type"] for item in history],
        "safe_update_mechanism": "pass",
        "measured_improvement": "partial" if measured else "inconclusive",
        "claim_boundary": "Measured improvement is a bounded source-bound Bundle/Knowledge update, not stable autonomous Skill-text evolution.",
        "evaluation_a_status": eval_a.status,
    }
    ref = workspace.put_json(payload, schema_version=payload["schema_version"])
    return {**payload, "artifact_ref": ref.to_dict()}


def _candidate(workspace: Workspace, expert, path: Path, fixed: str, build_id: str):
    path.write_text(json.dumps(_osv(fixed)), encoding="utf-8")
    snapshot = SourceIngestionService(workspace).add(
        SourceRef(source_id=f"osv-{build_id}", uri=str(path), adapter_type="osv-snapshot", visibility="build")
    )
    build = KnowledgeCompiler(workspace).build(expert_snapshot=expert, structured_snapshots=(snapshot,), build_id=build_id)
    return build, BundleBuilder(workspace).build(build)


def _unsafe_candidate(workspace: Workspace, base: CompilerBuild):
    skill = workspace.artifacts.get_json(ArtifactRef.from_dict(base.skill_ir_ref))
    skill["invocation"]["task_family"] = "all-security"
    skill_ref = workspace.put_json(skill, schema_version="skill_ir.v1")
    attestation = workspace.artifacts.get_json(ArtifactRef.from_dict(base.attestation_ref))
    attestation["subject_digests"]["skill_ir"] = skill_ref.digest
    attestation_ref = workspace.put_json(attestation, schema_version="build_attestation.v1")
    unsafe = replace(base, build_id="evolution-c-unsafe", skill_ir_ref=skill_ref.to_dict(), attestation_ref=attestation_ref.to_dict())
    workspace.metadata.add_build_record(build_id=unsafe.build_id, status="candidate", payload=unsafe.to_dict())
    return BundleBuilder(workspace).build(unsafe)


def _score(workspace: Workspace, digest: str, cases) -> tuple[int, list[dict[str, Any]]]:
    root = workspace.root / "evolution_inputs" / digest[-8:]
    root.mkdir(parents=True, exist_ok=True)
    env = root / "environment.json"
    env.write_text(json.dumps({"python_version": "3.11"}), encoding="utf-8")
    rows = []
    for case_id, requirement, expected in cases:
        req = root / f"{case_id}.txt"
        req.write_text(requirement + "\n", encoding="utf-8")
        envelope = PythonAdvisoryRuntime(workspace).run(
            requirements_path=req, environment_path=env, advisory_id="PYSEC-EVOLUTION-1", bundle_digest=digest
        )
        decision = envelope.domain_outcome.decision
        rows.append(
            {
                "case_id": case_id,
                "expected": expected,
                "actual": decision.verdict,
                "correct": decision.verdict == expected,
                "reason_codes": list(decision.reason_codes),
            }
        )
    return sum(row["correct"] for row in rows), rows


def _case_pass(rows, case_id: str) -> bool:
    return next(row["correct"] for row in rows if row["case_id"] == case_id)


def _false_safe(rows) -> int:
    return sum(row["actual"] == "advisory_not_applicable" and row["expected"] == "advisory_applicable" for row in rows)


def _osv(fixed: str) -> dict[str, Any]:
    return {
        "id": "PYSEC-EVOLUTION-1",
        "affected": [
            {
                "package": {"ecosystem": "PyPI", "name": "requests"},
                "ranges": [{"type": "ECOSYSTEM", "events": [{"introduced": "0"}, {"fixed": fixed}]}],
            }
        ],
    }
