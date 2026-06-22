from __future__ import annotations

import json
import time
from dataclasses import replace
from pathlib import Path
from typing import Any

from ..compiler import DirectToSkillIRBuilder, KnowledgeCompiler
from ..core.canonical import sha256_bytes, sha256_json
from ..core.models import ArtifactRef, SourceSnapshot
from ..registry.workspace import Workspace
from ..runtime import BundleBuilder, PythonAdvisoryRuntime

CONDITIONS = ("no_skill", "full_material", "direct_to_skill_ir", "compiler_distilled_skill")
PUBLIC_CONDITIONS = (*CONDITIONS, "human_authored_reference_skill")


def prepare_public_condition_comparison(workspace: Workspace, *, data_dir: Path) -> dict[str, Any]:
    """Freeze a condition-sensitive public held-out protocol without pretending to execute an AgentHost."""
    expert = _latest_snapshot(workspace, "expert-document")
    osv = _latest_snapshot(workspace, "osv-snapshot")
    direct = DirectToSkillIRBuilder(workspace).build(expert_snapshot=expert, build_id="public-comparison-direct")
    compiler = KnowledgeCompiler(workspace).build(
        expert_snapshot=expert, structured_snapshots=(osv,), build_id="public-comparison-compiler"
    )
    bundle = BundleBuilder(workspace).build(compiler)
    direct_skill = workspace.artifacts.get_json(ArtifactRef.from_dict(direct.skill_ir_ref))
    direct_agent_ref = workspace.put_bytes(
        BundleBuilder._compile_agent_artifact(direct_skill).encode("utf-8"),
        media_type="text/markdown",
        schema_version="agent_skill_artifact.v1",
    )
    compiler_agent_ref = bundle.manifest["agent_artifact_refs"][0]
    skill_ir_distinct = direct.skill_ir_ref["digest"] != compiler.skill_ir_ref["digest"]
    agent_artifact_distinct = direct_agent_ref.digest != compiler_agent_ref["digest"]
    inputs_path = data_dir / "inputs.jsonl"
    gold_path = data_dir / "gold.jsonl"
    all_inputs = [json.loads(line) for line in inputs_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    heldout = [item for item in all_inputs if item.get("split") == "heldout"]
    if not heldout:
        raise ValueError("public comparison requires at least one frozen held-out case")
    if any(any(key.startswith("expected_") for key in item) for item in heldout):
        raise ValueError("held-out AgentHost inputs contain evaluator-only fields")
    conditions = {
        "no_skill": {"status": "ready", "agent_input_refs": []},
        "full_material": {"status": "ready", "agent_input_refs": [expert.raw_artifact_ref]},
        "direct_to_skill_ir": {
            "status": "ready",
            "skill_ir_ref": direct.skill_ir_ref,
            "agent_input_refs": [direct_agent_ref.to_dict()],
        },
        "compiler_distilled_skill": {
            "status": "ready",
            "skill_ir_ref": compiler.skill_ir_ref,
            "knowledge_ir_ref": compiler.knowledge_ir_ref,
            "bundle_digest": bundle.bundle_digest,
            "agent_input_refs": [compiler_agent_ref],
        },
        "human_authored_reference_skill": {
            "status": "unavailable",
            "is_gold": False,
            "reason": "No independent human-authored reference Skill is available.",
            "agent_input_refs": [],
        },
    }
    payload = {
        "schema_version": "public_condition_sensitive_comparison.v1",
        "status": "prepared_but_blocked_identical_artifacts_and_no_agenthost",
        "execution_performed": False,
        "comparison_ready": False,
        "agent_host_status": "hard_blocked",
        "agent_host_reason": "Codex CLI did not produce a bounded schema-valid result within the qualification window.",
        "dataset_source": "frozen public OSV records",
        "heldout_case_count": len(heldout),
        "heldout_case_ids": [item["case_id"] for item in heldout],
        "heldout_input_digest": sha256_json(heldout),
        "full_input_manifest_digest": sha256_bytes(inputs_path.read_bytes()),
        "evaluator_gold_digest": sha256_bytes(gold_path.read_bytes()),
        "conditions": conditions,
        "condition_integrity": {
            "skill_ir_distinct": skill_ir_distinct,
            "agent_artifact_distinct": agent_artifact_distinct,
            "condition_content_identical": not skill_ir_distinct and not agent_artifact_distinct,
            "claim_allowed": False,
        },
        "shared_contract": {
            "same_agent_host": True,
            "same_task_budget": True,
            "same_osv_snapshot": osv.raw_artifact_ref["digest"],
            "same_evaluator": "public_osv_pair_evaluator.v2",
            "gold_hidden_from_agent": True,
        },
        "comparison_result": "not_run_identical_artifacts_and_agenthost_blocked",
        "blockers": [
            "DIRECT_AND_COMPILER_AGENT_ARTIFACTS_IDENTICAL",
            "QUALIFIED_AGENTHOST_UNAVAILABLE",
        ],
        "claim_boundary": "Identical condition artifacts and prepared inputs are not evidence of Compiler superiority or AgentHost effectiveness.",
    }
    ref = workspace.put_json(payload, schema_version=payload["schema_version"])
    return {**payload, "artifact_ref": ref.to_dict()}


def run_compiler_comparison(workspace: Workspace, *, data_dir: Path) -> dict[str, Any]:
    expert = _latest_snapshot(workspace, "expert-document")
    osv = _latest_snapshot(workspace, "osv-snapshot")
    direct_started = time.perf_counter()
    direct = DirectToSkillIRBuilder(workspace).build(expert_snapshot=expert, build_id="comparison-direct")
    direct_ms = round((time.perf_counter() - direct_started) * 1000, 3)
    compiler_started = time.perf_counter()
    compiler = KnowledgeCompiler(workspace).build(
        expert_snapshot=expert, structured_snapshots=(osv,), build_id="comparison-compiler"
    )
    compiler_ms = round((time.perf_counter() - compiler_started) * 1000, 3)
    bundle = BundleBuilder(workspace).build(compiler)
    cases_path = data_dir / "dev_cases" / "comparison_cases.jsonl"
    cases = [json.loads(line) for line in cases_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    environment = workspace.root / "comparison" / "environment.json"
    environment.parent.mkdir(parents=True, exist_ok=True)
    environment.write_text(json.dumps({"python_version": "3.11"}), encoding="utf-8")
    rows: list[dict[str, Any]] = []
    for condition in CONDITIONS:
        for case in cases:
            requirement_path = workspace.root / "comparison" / condition / f"{case['case_id']}.txt"
            requirement_path.parent.mkdir(parents=True, exist_ok=True)
            requirement_path.write_text(case["requirement"] + "\n", encoding="utf-8")
            started = time.perf_counter()
            envelope = PythonAdvisoryRuntime(workspace).run(
                requirements_path=requirement_path,
                environment_path=environment,
                advisory_id=case["advisory_id"],
                bundle_digest=bundle.bundle_digest,
            )
            elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
            decision = envelope.domain_outcome.decision if envelope.domain_outcome else None
            verdict = decision.verdict if decision else None
            reasons = list(decision.reason_codes) if decision else []
            rows.append(
                {
                    "condition": condition,
                    "case_id": case["case_id"],
                    "split": "dev",
                    "verdict": verdict,
                    "reason_codes": reasons,
                    "correct": verdict == case["expected_verdict"] and case["expected_reason"] in reasons,
                    "justified_unresolved": verdict == "unresolved" and bool(reasons),
                    "false_safe": verdict == "advisory_not_applicable" and case["expected_verdict"] == "advisory_applicable",
                    "evidence_complete": bool(decision and decision.evidence_refs),
                    "elapsed_ms": elapsed_ms,
                    "execution_adapter": "shared_reference_decision_backend",
                    "condition_artifact_consumed_by_agent": False,
                }
            )
    metrics = {condition: _aggregate([row for row in rows if row["condition"] == condition]) for condition in CONDITIONS}
    direct_attestation = workspace.artifacts.get_json(ArtifactRef.from_dict(direct.attestation_ref))
    compiler_attestation = workspace.artifacts.get_json(ArtifactRef.from_dict(compiler.attestation_ref))
    metrics["direct_to_skill_ir"].update(_structural(direct_attestation, direct_ms))
    metrics["compiler_distilled_skill"].update(_structural(compiler_attestation, compiler_ms))
    payload = {
        "schema_version": "compiler_vs_direct_evaluation.v1",
        "split": "dev",
        "case_manifest_digest": sha256_bytes(cases_path.read_bytes()),
        "resource_envelope": {
            "llm_calls_max": 0,
            "external_access_max": 0,
            "token_cost": None,
            "token_cost_reason": "deterministic V1 builders and evaluator",
        },
        "conditions": list(CONDITIONS),
        "metrics": metrics,
        "rows": rows,
        "compiler_superiority": "evaluated_on_dev_only",
        "comparison_result": "inconclusive",
        "reason": "The shared reference backend does not consume condition-specific Skill artifacts; task parity is plumbing evidence, not superiority.",
        "claim_boundary": "This validates staged architecture and dev instrumentation, not open-world extraction or AgentHost effectiveness.",
    }
    ref = workspace.put_json(payload, schema_version=payload["schema_version"])
    return {**payload, "artifact_ref": ref.to_dict()}


def _aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    count = len(rows)
    return {
        "case_count": count,
        "verdict_correctness": sum(row["correct"] for row in rows) / count,
        "justified_unresolved_count": sum(row["justified_unresolved"] for row in rows),
        "false_safe_rate": sum(row["false_safe"] for row in rows) / count,
        "evidence_completeness": sum(row["evidence_complete"] for row in rows) / count,
        "runtime_elapsed_ms": round(sum(row["elapsed_ms"] for row in rows), 3),
    }


def _structural(attestation: dict[str, Any], build_elapsed_ms: float) -> dict[str, Any]:
    findings = attestation.get("deterministic_findings", [])
    return {
        "unsupported_claim_count": sum(item.get("code") == "unsupported_claim" for item in findings),
        "scope_overreach_count": sum(item.get("code") == "scope_overreach" for item in findings),
        "missing_exception_count": sum(item.get("code") == "missing_exception" for item in findings),
        "build_elapsed_ms": build_elapsed_ms,
        "token_count": None,
        "cost": None,
    }


def _latest_snapshot(workspace: Workspace, adapter_type: str) -> SourceSnapshot:
    rows = [row for row in workspace.metadata.source_snapshots() if row["adapter_type"] == adapter_type]
    if not rows:
        raise RuntimeError(f"no registered {adapter_type} source")
    row = rows[-1]
    ref = workspace.metadata.artifact_ref(row["snapshot_digest"])
    snapshot = SourceSnapshot.from_dict(workspace.artifacts.get_json(ref))
    return replace(snapshot, metadata={**snapshot.metadata, "snapshot_ref": ref.to_dict()})
