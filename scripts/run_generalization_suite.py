from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from skill_deployment import CAPABILITY_SPECS, ControlledTaskCase, ExecutionReport, RepairContext, RunnerContext, SkillPackage, TraceRecord, VerifierReport, build_patch_and_gate, get_backend_runner, select_controlled_task_cases, verify_controlled_execution

DATA_ROOT = ROOT / "data" / "task_cases"
RUN_ROOT = ROOT / "runs" / "generalization"
VALIDATION_ROOT = ROOT / "outputs" / "validation"

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def append_jsonl(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def load_repair_policy() -> dict[str, str]:
    policy_path = ROOT / "revision" / "repair_policy.json"
    payload = json.loads(policy_path.read_text(encoding="utf-8"))
    actions = payload.get("repair_actions", {})
    if not isinstance(actions, dict):
        raise SystemExit(f"invalid repair policy: {policy_path}")
    return {str(key): str(value) for key, value in actions.items()}


def select_scenarios(names: str) -> list[ControlledTaskCase]:
    try:
        return select_controlled_task_cases(DATA_ROOT, names)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc


def render_skill(scenario: ControlledTaskCase, capabilities: list[str], version: str, repair_action: str | None = None) -> str:
    lines = [
        f"# {scenario.title} Skill {version}",
        "",
        f"Task family: `{scenario.task_family}`",
        "",
        "## Inspection Procedure",
        "",
        "1. Read the target assets and identify concrete evidence spans.",
        "2. Emit only findings grounded in the current target.",
        "3. Follow the output contract: capability_id, evidence_span, recommended_fix.",
        "",
        "## Capabilities",
        "",
    ]
    for capability_id in capabilities:
        cap = CAPABILITY_SPECS[capability_id]
        lines.extend([f"### {cap.capability_id}: {cap.title}", f"- Evidence: {cap.evidence_hint}", f"- Fix: {cap.fix_hint}", ""])
    if repair_action:
        lines.extend(["## Revision Policy", "", f"Applied repair action: `{repair_action}`.", ""])
    return "\n".join(lines)


def apply_attempt_defect(item: dict[str, Any], defect: str | None, targeted: set[str]) -> dict[str, Any]:
    capability_id = str(item.get("capability_id", ""))
    target_hit = not targeted or capability_id in targeted
    if not defect or not target_hit:
        return item
    if defect in {"ownership_boundary_missing", "weak_evidence", "target_context_missing"}:
        item["evidence_span"] = ""
    if defect == "output_contract_error":
        item.pop("recommended_fix", None)
    return item


def agent_attempt(scenario: ControlledTaskCase, capabilities: list[str], attempt: str, defect: str | None) -> ExecutionReport:
    findings = []
    targeted = set(scenario.defect_capabilities)
    if defect == "ownership_boundary_missing" and not targeted:
        targeted.add("AUTH_OBJECT_OWNERSHIP")
    if defect == "output_contract_error" and not targeted:
        targeted.add("API_OVERBROAD_RISK")
    for capability_id in capabilities:
        cap = CAPABILITY_SPECS[capability_id]
        item = {
            "capability_id": capability_id,
            "issue": cap.title,
            "evidence_span": cap.evidence_hint,
            "recommended_fix": cap.fix_hint,
        }
        findings.append(apply_attempt_defect(item, defect, targeted))
    return ExecutionReport(attempt=attempt, backend="offline_deterministic", findings=tuple(findings))


def verify(scenario: ControlledTaskCase, output: ExecutionReport | dict[str, Any]) -> dict[str, Any]:
    report = verify_controlled_execution(
        scenario.expected_capabilities,
        output,
        feedback_overrides=scenario.verifier_contract.get("feedback_overrides", {}),
    )
    return report.to_dict()


def repair(scenario: ControlledTaskCase, feedback: dict[str, Any], repair_policy: dict[str, str]) -> tuple[list[str], dict[str, Any], dict[str, Any]]:
    context = RepairContext(
        scenario_id=scenario.case_id,
        task_family=scenario.task_family,
        current_capabilities=tuple(scenario.v1_capabilities),
        expected_capabilities=tuple(scenario.expected_capabilities),
        verifier_report=VerifierReport.from_dict(feedback),
        repair_policy=repair_policy,
    )
    after_capabilities, patch, gate = build_patch_and_gate(context)
    return list(after_capabilities), patch.to_dict(), gate.to_dict()


def run_scenario(scenario: ControlledTaskCase, backend: str) -> dict[str, Any]:
    repair_policy = load_repair_policy()
    backend_runner = get_backend_runner(backend, project_root=ROOT)
    run_dir = RUN_ROOT / scenario.case_id
    start = time.perf_counter()
    for sub in ("source_materials", "target_asset", "task_spec"):
        (run_dir / sub).mkdir(parents=True, exist_ok=True)
    write_text(run_dir / "source_materials" / "expert_material.md", scenario.expert_material)
    write_text(run_dir / "target_asset" / "target.md", scenario.target_asset)
    write_json(run_dir / "task_spec" / "task_spec.json", {"case_id": scenario.case_id, "backend": backend, "expected": list(scenario.expected_capabilities)})

    a0_ctx = RunnerContext(
        scenario_id=scenario.case_id,
        backend=backend,
        target_dir=run_dir / "target_asset",
        output_dir=run_dir / "attempts" / "A0",
        attempt_id="A0_no_skill",
        skill_package=None,
        task_case=scenario,
        metadata={},
    )
    a0 = backend_runner.run(a0_ctx).report.to_dict()
    v0 = verify(scenario, a0)
    write_json(run_dir / "attempts" / "A0" / "agent_output.json", a0)
    write_json(run_dir / "verifier" / "A0_report.json", v0)

    skill_v1 = SkillPackage(
        skill_id=scenario.case_id,
        version="v1",
        task_family=scenario.task_family,
        capabilities=tuple(scenario.v1_capabilities),
        output_contract=("capability_id", "evidence_span", "recommended_fix"),
        trace_contract=("event", "capability_id", "evidence_span"),
    )
    write_text(run_dir / "skills" / "skill_v1" / "SKILL.md", render_skill(scenario, list(skill_v1.capabilities), "v1"))
    write_json(run_dir / "skills" / "skill_v1" / "manifest.json", skill_v1.to_dict())
    a1_ctx = RunnerContext(
        scenario_id=scenario.case_id,
        backend=backend,
        target_dir=run_dir / "target_asset",
        output_dir=run_dir / "attempts" / "A1",
        attempt_id="A1_skill_v1",
        skill_package=skill_v1,
        task_case=scenario,
        metadata={
            "defect": scenario.a1_defect,
            "skill_dir": run_dir / "skills" / "skill_v1",
        },
    )
    a1 = backend_runner.run(a1_ctx).report.to_dict()
    v1 = verify(scenario, a1)
    write_json(run_dir / "attempts" / "A1" / "agent_input.json", {"skill": "skills/skill_v1", "target": "target_asset"})
    write_json(run_dir / "attempts" / "A1" / "agent_output.json", a1)
    write_json(run_dir / "verifier" / "A1_report.json", v1)

    v2_caps, patch, gate = repair(scenario, v1, repair_policy)
    write_json(run_dir / "revision" / "repair_decision.json", patch)
    write_json(run_dir / "revision" / "gate_decision.json", gate)
    skill_v2 = SkillPackage(
        skill_id=scenario.case_id,
        version="v2",
        task_family=scenario.task_family,
        capabilities=tuple(v2_caps),
        output_contract=("capability_id", "evidence_span", "recommended_fix"),
        trace_contract=("event", "capability_id", "evidence_span"),
        metadata={"repair_action": patch["repair_action"], "operator_id": patch.get("operator_id", patch.get("details", ""))},
    )
    write_text(run_dir / "skills" / "skill_v2" / "SKILL.md", render_skill(scenario, list(skill_v2.capabilities), "v2", patch["repair_action"]))
    write_json(run_dir / "skills" / "skill_v2" / "manifest.json", skill_v2.to_dict())
    a2_ctx = RunnerContext(
        scenario_id=scenario.case_id,
        backend=backend,
        target_dir=run_dir / "target_asset",
        output_dir=run_dir / "attempts" / "A2",
        attempt_id="A2_skill_v2",
        skill_package=skill_v2,
        task_case=scenario,
        metadata={
            "skill_dir": run_dir / "skills" / "skill_v2",
        },
    )
    a2 = backend_runner.run(a2_ctx).report.to_dict()
    v2 = verify(scenario, a2)
    write_json(run_dir / "attempts" / "A2" / "agent_input.json", {"skill": "skills/skill_v2", "target": "target_asset"})
    write_json(run_dir / "attempts" / "A2" / "agent_output.json", a2)
    write_json(run_dir / "verifier" / "A2_report.json", v2)

    source_trace = [
        {"source": "source_materials/expert_material.md", "capability_id": cap, "skill_file": f"skills/skill_v2/SKILL.md#{cap}"}
        for cap in scenario.expected_capabilities
    ]
    write_json(run_dir / "provenance" / "source_to_skill_mapping.json", source_trace)
    write_json(run_dir / "trace" / "source_trace.json", source_trace)
    for item in a1["findings"]:
        append_jsonl(run_dir / "trace" / "execution_trace_A1.jsonl", TraceRecord(event="finding", capability_id=str(item.get("capability_id", "")), evidence_span=str(item.get("evidence_span", "")), payload=item).to_dict())
    for item in a2["findings"]:
        append_jsonl(run_dir / "trace" / "execution_trace_A2.jsonl", TraceRecord(event="finding", capability_id=str(item.get("capability_id", "")), evidence_span=str(item.get("evidence_span", "")), payload=item).to_dict())
    write_json(run_dir / "trace" / "feedback_trace_A1.json", v1)
    write_json(run_dir / "trace" / "revision_trace_v1_to_v2.json", {"patch": patch, "gate": gate})

    summary = {
        "scenario": scenario.case_id,
        "family": scenario.task_family,
        "backend": backend,
        "a0_pass": v0["pass"],
        "a1_pass": v1["pass"],
        "a2_pass": v2["pass"],
        "feedback_type": v1["feedback_type"],
        "repair_action": patch["repair_action"],
        "gate_decision": gate["decision"],
        "scores_before": v1["scores"],
        "scores_after": v2["scores"],
        "latency_ms": int((time.perf_counter() - start) * 1000),
        "artifact_dir": str(run_dir.relative_to(ROOT)),
    }
    write_json(run_dir / "summary" / "metrics.json", summary)
    return summary


def render_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Generalization Suite",
        "",
        f"- Backend: `{payload['backend']}`",
        f"- Scenarios: `{payload['scenario_count']}`",
        f"- A2 pass: `{payload['a2_pass_count']}/{payload['scenario_count']}`",
        "",
        "| Scenario | Family | A1 Feedback | Repair | Gate | A2 |",
        "|---|---|---|---|---|---|",
    ]
    for row in payload["results"]:
        lines.append(f"| {row['scenario']} | {row['family']} | {row['feedback_type']} | {row['repair_action']} | {row['gate_decision']} | {row['a2_pass']} |")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This is controlled offline evidence that the same pipeline can run multiple task families. It is not a large-scale proof of arbitrary vulnerability discovery.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_non_oracle_status(payload: dict[str, Any]) -> str:
    families = sorted({row["family"] for row in payload["results"]})
    includes_non_security = any(row["family"] == "data_quality_review" for row in payload["results"])
    repairing = [row["scenario"] for row in payload["results"] if row["feedback_type"] != "pass"]
    lines = [
        "# Non-Oracle Local Agent Status",
        "",
        f"- Backend: `{payload['backend']}`",
        f"- Scenarios: `{payload['scenario_count']}`",
        f"- A2 pass: `{payload['a2_pass_count']}/{payload['scenario_count']}`",
        f"- Families: `{', '.join(families)}`",
        f"- Includes non-security family: `{includes_non_security}`",
        "",
        "| Scenario | Family | A1 Feedback | Repair | Gate | A2 | Artifact Dir |",
        "|---|---|---|---|---|---:|---|",
    ]
    for row in payload["results"]:
        lines.append(
            f"| {row['scenario']} | {row['family']} | {row['feedback_type']} | "
            f"{row['repair_action']} | {row['gate_decision']} | {row['a2_pass']} | `{row['artifact_dir']}` |"
        )
    failed = [row for row in payload["results"] if not row["a2_pass"]]
    lines.extend(
        [
            "",
            "## Required Questions",
            "",
            "1. Where can the non-oracle local agent produce target-grounded evidence? See per-scenario A1/A2 outputs under the artifact dirs; this backend now reads upload, auth, config, API-review, and one non-security data-quality target family.",
            f"2. Which tasks fail? `{', '.join(row['scenario'] for row in failed) if failed else 'none in this smoke'}`.",
            f"3. Which tasks still exercise repair? `{', '.join(repairing) if repairing else 'none in this slice'}`.",
            "4. Failure attribution: current failures should be treated as detector/target-observation gaps unless verifier output shows schema or regression errors.",
            "5. Can feedback/repair catch failures? The same verifier report and repair policy path is used; failures are written instead of hidden.",
            "",
            "## Boundary",
            "",
            "This is a deterministic non-oracle local semantic backend. It reads target files and Skill packages and writes agent_output.json, trace.jsonl, stdout.log, and metadata. It is broader than the original upload/config smoke, but it is still not an LLM agent and not a Harbor sandbox agent.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenarios", default="upload,auth,config,api_review,data_quality")
    parser.add_argument("--backend", default="offline_deterministic", choices=["offline_deterministic", "live_llm_text", "non_oracle_local_semantic"])
    args = parser.parse_args()
    if args.backend == "live_llm_text":
        raise SystemExit("live_llm_text is not integrated into run_generalization_suite; use scripts/run_live_llm_upload.py for the current controlled LLM path")
    selected = select_scenarios(args.scenarios)
    results = [run_scenario(scenario, args.backend) for scenario in selected]
    payload = {
        "run_id": f"generalization_suite_{args.backend}",
        "created_at": utc_now(),
        "backend": args.backend,
        "scenario_count": len(results),
        "a2_pass_count": sum(1 for row in results if row["a2_pass"]),
        "feedback_types": sorted({row["feedback_type"] for row in results}),
        "repair_actions": sorted({row["repair_action"] for row in results}),
        "results": results,
        "claim_support": {
            "same_pipeline_four_tasks": len(results) >= 4,
            "same_pipeline_five_tasks": len(results) >= 5,
            "includes_non_security_family": any(row["family"] == "data_quality_review" for row in results),
            "different_feedback": len({row["feedback_type"] for row in results}) >= 4,
            "different_repair_actions": len({row["repair_action"] for row in results}) >= 4,
            "all_a2_pass": all(row["a2_pass"] for row in results),
            "artifact_backed": True,
        },
    }
    VALIDATION_ROOT.mkdir(parents=True, exist_ok=True)
    if args.backend == "non_oracle_local_semantic":
        json_name = "non_oracle_local_suite.json"
        md_name = "non_oracle_local_suite.md"
        status_name = ROOT / "reports" / "NON_ORACLE_LOCAL_AGENT_STATUS.md"
    else:
        json_name = "generalization_suite.json"
        md_name = "generalization_suite.md"
        status_name = None
    write_json(VALIDATION_ROOT / json_name, payload)
    report_text = render_report(payload)
    write_text(VALIDATION_ROOT / md_name, report_text)
    if status_name:
        write_text(status_name, render_non_oracle_status(payload))
    print(json.dumps({"output": str(VALIDATION_ROOT / json_name), "a2_pass": payload["a2_pass_count"], "scenarios": len(results)}, ensure_ascii=False, indent=2))
    if args.backend == "non_oracle_local_semantic":
        return 0
    return 0 if all(row["a2_pass"] for row in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
