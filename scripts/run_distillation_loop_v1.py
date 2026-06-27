from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from expert_skill_system.compiler.repo_level_bundle_builder import (  # noqa: E402
    REPO_LEVEL_SKILL_ID,
    RepoLevelBundleBuilder,
)
from expert_skill_system.distillation.bundle_policy_diff import diff_runtime_policies  # noqa: E402
from expert_skill_system.distillation.distillation_report import (  # noqa: E402
    build_comparison_report,
    build_promotion_decision,
    render_comparison_markdown,
)
from expert_skill_system.distillation.failure_attribution import attribute_repo_level_run  # noqa: E402
from expert_skill_system.distillation.multi_defect_session import (  # noqa: E402
    MultiDefectCase,
    load_multi_defect_cases,
    write_variant_bundle_input,
)
from expert_skill_system.distillation.revision_planner import build_revision_plan  # noqa: E402
from expert_skill_system.evaluation.repo_eval_harness import run_repo_level_eval  # noqa: E402
from expert_skill_system.registry.workspace import Workspace  # noqa: E402
from expert_skill_system.runtime.release_bundle_policy import (  # noqa: E402
    load_bundle_runtime_policy_from_resolution,
    load_evidence_binding_plan_from_resolution,
    required_evidence_from_plan,
)
from expert_skill_system.runtime.release_bundle_resolver import resolve_release_bundle  # noqa: E402

REPORT_PATH = ROOT / "reports" / "DISTILLATION_FEEDBACK_LOOP_V1_STATUS.md"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run multi-defect expert distillation feedback loop v1.")
    parser.add_argument("--case-root", required=True)
    parser.add_argument("--state-dir", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)

    cases = load_multi_defect_cases(Path(args.case_root))
    state_root = Path(args.state_dir).resolve()
    output_root = Path(args.output).resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    rows = []
    for case in cases:
        rows.append(_run_case(case=case, state_root=state_root, output_root=output_root))
    aggregate = _build_aggregate(rows)
    _write_json(output_root / "v1_aggregate_report.json", aggregate)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(_render_aggregate_report(aggregate), encoding="utf-8")
    print(json.dumps({"status": aggregate["distillation_feedback_loop_v1"], "report": str(REPORT_PATH)}, indent=2))
    return 0 if aggregate["distillation_feedback_loop_v1"] == "pass" else 1


def _run_case(*, case: MultiDefectCase, state_root: Path, output_root: Path) -> dict[str, Any]:
    state_dir = state_root / case.defect_id
    output_dir = output_root / "cases" / case.defect_id
    output_dir.mkdir(parents=True, exist_ok=True)
    workspace = Workspace.open(state_dir)
    builder = RepoLevelBundleBuilder(workspace)
    _write_json(
        output_dir / "distillation_case_manifest.json",
        {
            "schema_version": "distillation_v1_case_manifest.v1",
            "defect_id": case.defect_id,
            "state_dir": str(state_dir),
            "output_dir": str(output_dir),
            "claim_boundary": case.config["claim_boundary"],
        },
    )

    baseline_dir = output_dir / "baseline_bundle"
    baseline_input = write_variant_bundle_input(
        case=case,
        output_dir=baseline_dir,
        expert_material=case.expert_material_v0,
        evidence_policy=case.baseline_policy,
    )
    baseline_result = builder.build(
        data_dir=baseline_input,
        skill_family=REPO_LEVEL_SKILL_ID,
        promote=True,
        variant=case.config["baseline_variant"],
        evidence_policy=case.baseline_policy,
    )
    _write_json(baseline_dir / "build_result.json", baseline_result.to_dict())
    baseline_policy = _resolved_policy(
        state_dir=state_dir,
        bundle_digest=baseline_result.bundle_digest,
        out_dir=baseline_dir,
    )
    baseline_summary = run_repo_level_eval(
        task_registry=case.task_registry,
        output_dir=output_dir / "baseline_run",
        state_dir=state_dir,
        bundle_digest=baseline_result.bundle_digest,
        binding_key=REPO_LEVEL_SKILL_ID,
        condition=f"{case.defect_id}_baseline",
        fail_on_partial_bundle=True,
    )
    baseline_aggregate = _read_json(output_dir / "baseline_run" / "aggregate_report.json")
    attribution_records, failure_summary = attribute_repo_level_run(output_dir / "baseline_run")
    _write_jsonl(output_dir / "failure_attribution.jsonl", attribution_records)
    _write_json(output_dir / "failure_summary.json", failure_summary)

    revision_plan, revised_material = build_revision_plan(
        expert_material_v0=case.expert_material_v0,
        expected_evidence_policy=case.expected_repair_policy,
        failure_summary=failure_summary,
    )
    _write_json(output_dir / "revision_plan.json", revision_plan)
    (output_dir / "revised_expert_material.md").write_text(revised_material, encoding="utf-8")

    revised_dir = output_dir / "revised_bundle"
    revised_input = write_variant_bundle_input(
        case=case,
        output_dir=revised_dir,
        expert_material=revised_material,
        evidence_policy=case.expected_repair_policy,
    )
    revised_result = builder.build(
        data_dir=revised_input,
        skill_family=REPO_LEVEL_SKILL_ID,
        promote=False,
        variant=case.config["revised_variant"],
        evidence_policy=case.expected_repair_policy,
    )
    _write_json(revised_dir / "build_result.json", revised_result.to_dict())
    revised_policy = _resolved_policy(
        state_dir=state_dir,
        bundle_digest=revised_result.bundle_digest,
        out_dir=revised_dir,
    )
    revised_summary = run_repo_level_eval(
        task_registry=case.task_registry,
        output_dir=output_dir / "revised_run",
        state_dir=state_dir,
        bundle_digest=revised_result.bundle_digest,
        binding_key=REPO_LEVEL_SKILL_ID,
        condition=f"{case.defect_id}_revised",
        fail_on_partial_bundle=True,
    )
    revised_aggregate = _read_json(output_dir / "revised_run" / "aggregate_report.json")
    policy_diff = diff_runtime_policies(case.baseline_policy, case.expected_repair_policy)
    _write_json(output_dir / "bundle_policy_diff.json", policy_diff)
    seed_summary = _evaluate_seeded_counterexamples(
        seed_cases=case.seed_failure_cases,
        baseline_policy=case.baseline_policy,
        revised_policy=case.expected_repair_policy,
    )
    comparison = build_comparison_report(
        baseline_summary=baseline_summary,
        revised_summary=revised_summary,
        baseline_aggregate=baseline_aggregate,
        revised_aggregate=revised_aggregate,
        failure_summary=failure_summary,
        seed_summary=seed_summary,
        baseline_required_evidence=required_evidence_from_plan(baseline_policy["evidence_binding_plan"]),
        revised_required_evidence=required_evidence_from_plan(revised_policy["evidence_binding_plan"]),
    )
    _write_json(output_dir / "comparison_report.json", comparison)
    (output_dir / "comparison_report.md").write_text(render_comparison_markdown(comparison), encoding="utf-8")

    promotion = build_promotion_decision(comparison)
    expected_match = _expected_attribution_matched(case.expected_attribution, attribution_records)
    if promotion["accepted"] and not expected_match:
        promotion["decision"] = "reject"
        promotion["accepted"] = False
        promotion["reason_codes"] = ["EXPECTED_ATTRIBUTION_NOT_OBSERVED"]
    if promotion["accepted"]:
        current = workspace.metadata.get_active_binding(REPO_LEVEL_SKILL_ID)
        active = workspace.metadata.change_binding(
            binding_key=REPO_LEVEL_SKILL_ID,
            target_digest=revised_result.bundle_digest,
            expected_generation=current.generation if current else 0,
            event_type="promote",
            reason_codes=("DISTILLATION_FEEDBACK_LOOP_V1_PASS",),
        )
        promotion["active_binding_generation"] = active.generation
    else:
        event = workspace.metadata.record_rejection(
            binding_key=REPO_LEVEL_SKILL_ID,
            candidate_digest=revised_result.bundle_digest,
            reason_codes=tuple(promotion["reason_codes"]),
        )
        promotion["rejection_event_id"] = event.event_id
    promotion["active_binding_state_dir"] = str(state_dir)
    _write_json(output_dir / "promotion_decision.json", promotion)

    row = {
        "schema_version": "distillation_v1_case_result.v1",
        "defect_id": case.defect_id,
        "baseline_bundle_digest": baseline_result.bundle_digest,
        "revised_bundle_digest": revised_result.bundle_digest,
        "digest_changed": baseline_result.bundle_digest != revised_result.bundle_digest,
        "baseline_pass_count": baseline_summary["pass_count"],
        "revised_pass_count": revised_summary["pass_count"],
        "baseline_failed_task_ids": failure_summary.get("failed_task_ids", []),
        "failure_attribution_types": sorted(failure_summary.get("failure_types", {})),
        "revision_targets": revision_plan["revision_targets"],
        "repair_type": revision_plan["repair_type"],
        "policy_diff": policy_diff,
        "expected_attribution_matched": expected_match,
        "seeded_counterexample_pass": seed_summary["revised_seeded_counterexample_pass"],
        "promotion_decision": promotion["decision"],
        "case_output_dir": str(output_dir),
    }
    _write_json(output_dir / "case_result.json", row)
    return row


def _resolved_policy(*, state_dir: Path, bundle_digest: str, out_dir: Path) -> dict[str, Any]:
    resolved = resolve_release_bundle(
        state_dir=state_dir,
        bundle_digest=bundle_digest,
        binding_key=REPO_LEVEL_SKILL_ID,
        fail_on_partial_bundle=True,
    )
    evidence_plan = load_evidence_binding_plan_from_resolution(resolved)
    bundle_policy = load_bundle_runtime_policy_from_resolution(resolved)
    if evidence_plan is None or bundle_policy is None:
        raise RuntimeError("resolved bundle did not expose runtime policy")
    _write_json(out_dir / "evidence_binding_plan.json", evidence_plan)
    _write_json(out_dir / "runtime_bundle_policy.json", bundle_policy)
    return bundle_policy


def _evaluate_seeded_counterexamples(
    *,
    seed_cases: list[dict[str, Any]],
    baseline_policy: dict[str, Any],
    revised_policy: dict[str, Any],
) -> dict[str, Any]:
    rows = []
    baseline_exposed = False
    revised_pass = True
    for seed in seed_cases:
        baseline_decision = _decision_from_policy(seed["facts"], baseline_policy)
        revised_decision = _decision_from_policy(seed["facts"], revised_policy)
        baseline_seed_exposed = baseline_decision == seed["unsafe_decision"]
        revised_seed_pass = revised_decision in set(seed["expected_revised_decisions"])
        baseline_exposed = baseline_exposed or baseline_seed_exposed
        revised_pass = revised_pass and revised_seed_pass
        rows.append(
            {
                "seed_id": seed["seed_id"],
                "baseline_decision": baseline_decision,
                "revised_decision": revised_decision,
                "baseline_seed_exposed": baseline_seed_exposed,
                "revised_seed_pass": revised_seed_pass,
                "violated_policy": seed["violated_policy"],
            }
        )
    return {
        "schema_version": "distillation_seeded_counterexample_summary.v1",
        "seed_count": len(seed_cases),
        "baseline_seeded_counterexample_exposed": baseline_exposed,
        "revised_seeded_counterexample_pass": revised_pass,
        "rows": rows,
    }


def _decision_from_policy(facts: dict[str, Any], policy: dict[str, Any]) -> str:
    if not facts.get("dependency_declared"):
        return "dependency_not_declared"
    if not facts.get("resolved_version"):
        return "unresolved"
    knowledge_policy = dict(policy.get("knowledge_projection_policy", {"allowed_advisory_fields": ["affected_ranges"]}))
    allowed_advisory_fields = set(knowledge_policy.get("allowed_advisory_fields", ["affected_ranges"]))
    if "affected_ranges" not in allowed_advisory_fields:
        return "unresolved"
    required_evidence = set(policy.get("required_evidence", []))
    candidates = dict(policy.get("candidate_path_overrides", {}))
    import_candidates_missing = "import_use_site" in candidates and candidates["import_use_site"] == []
    if "import_use_site" in required_evidence and (not facts.get("import_use_site_present") or import_candidates_missing):
        return "dependency_present_not_used"
    decision_policy = dict(policy.get("decision_policy", {"version_range_comparison_required": True}))
    if decision_policy.get("version_range_comparison_required") is False:
        return "dependency_used_and_affected"
    if facts.get("version_in_affected_range"):
        return "dependency_used_and_affected"
    return "dependency_used_not_affected"


def _expected_attribution_matched(expected: dict[str, Any], records: list[dict[str, Any]]) -> bool:
    return any(
        record.get("failure_type") == expected.get("failure_type")
        and record.get("repair_target") == expected.get("repair_target")
        and record.get("violated_policy") == expected.get("violated_policy")
        for record in records
    )


def _build_aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    required_pass = all(
        row["promotion_decision"] == "promote"
        and row["digest_changed"]
        and row["expected_attribution_matched"]
        and row["seeded_counterexample_pass"]
        for row in rows
    )
    return {
        "schema_version": "distillation_feedback_loop_v1_status.v1",
        "distillation_feedback_loop_v1": "pass" if required_pass else "partial",
        "defect_count": len(rows),
        "promoted_count": sum(1 for row in rows if row["promotion_decision"] == "promote"),
        "defect_ids": [row["defect_id"] for row in rows],
        "failure_attribution_types": sorted({item for row in rows for item in row["failure_attribution_types"]}),
        "revision_targets": sorted({item for row in rows for item in row["revision_targets"]}),
        "case_results": rows,
        "claim_boundary": {
            "compiler_superiority": "not_evaluated",
            "mature_agenthost_effectiveness": "not_evaluated",
            "general_vulnerability_discovery": "not_claimed",
            "official_public_benchmark_performance": "not_claimed",
            "production_readiness": "not_claimed",
        },
    }


def _render_aggregate_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Distillation Feedback Loop v1 Status",
        "",
        f"- distillation_feedback_loop_v1: `{payload['distillation_feedback_loop_v1']}`",
        f"- defect_count: `{payload['defect_count']}`",
        f"- promoted_count: `{payload['promoted_count']}`",
        f"- failure_attribution_types: `{json.dumps(payload['failure_attribution_types'])}`",
        f"- revision_targets: `{json.dumps(payload['revision_targets'])}`",
        "",
        "| defect_id | baseline_pass | revised_pass | attribution | targets | promotion |",
        "|---|---:|---:|---|---|---|",
    ]
    for row in payload["case_results"]:
        lines.append(
            "| "
            + f"`{row['defect_id']}` | `{row['baseline_pass_count']}` | `{row['revised_pass_count']}` | "
            + f"`{json.dumps(row['failure_attribution_types'])}` | `{json.dumps(row['revision_targets'])}` | `{row['promotion_decision']}` |"
        )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "- compiler_superiority: `not_evaluated`",
            "- mature_agenthost_effectiveness: `not_evaluated`",
            "- general_vulnerability_discovery: `not_claimed`",
            "- official_public_benchmark_performance: `not_claimed`",
            "- production_readiness: `not_claimed`",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
