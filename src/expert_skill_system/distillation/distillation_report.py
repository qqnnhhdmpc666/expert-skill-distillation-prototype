from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def build_comparison_report(
    *,
    baseline_summary: dict[str, Any],
    revised_summary: dict[str, Any],
    baseline_aggregate: dict[str, Any],
    revised_aggregate: dict[str, Any],
    failure_summary: dict[str, Any],
    seed_summary: dict[str, Any],
    baseline_required_evidence: list[str],
    revised_required_evidence: list[str],
) -> dict[str, Any]:
    baseline_unsupported = _unsupported_affected_count(baseline_aggregate)
    revised_unsupported = _unsupported_affected_count(revised_aggregate)
    regression_count = _regression_count(baseline_aggregate, revised_aggregate)
    return {
        "schema_version": "distillation_comparison_report.v1",
        "baseline": {
            "bundle_digest": baseline_summary.get("bundle_digest"),
            "pass_count": baseline_summary.get("pass_count"),
            "fail_count": baseline_summary.get("fail_count"),
            "failure_types": failure_summary.get("failure_types", {}),
            "unsupported_affected_decision_count": baseline_unsupported,
            "required_evidence": baseline_required_evidence,
        },
        "revised": {
            "bundle_digest": revised_summary.get("bundle_digest"),
            "pass_count": revised_summary.get("pass_count"),
            "fail_count": revised_summary.get("fail_count"),
            "unsupported_affected_decision_count": revised_unsupported,
            "required_evidence": revised_required_evidence,
        },
        "delta": {
            "pass_count_delta": int(revised_summary.get("pass_count", 0)) - int(baseline_summary.get("pass_count", 0)),
            "unsupported_affected_decision_delta": revised_unsupported - baseline_unsupported,
            "regression_count": regression_count,
        },
        "seeded_counterexamples": seed_summary,
        "promotion_recommendation": _promotion_recommendation(
            revised_summary=revised_summary,
            revised_aggregate=revised_aggregate,
            regression_count=regression_count,
            seed_summary=seed_summary,
            revised_unsupported=revised_unsupported,
            baseline_unsupported=baseline_unsupported,
        ),
    }


def build_promotion_decision(comparison: dict[str, Any]) -> dict[str, Any]:
    recommendation = comparison["promotion_recommendation"]
    accepted = recommendation == "promote"
    reason_codes = []
    if accepted:
        reason_codes.append("NO_REGRESSION_AND_SEEDED_COUNTEREXAMPLE_PASS")
    else:
        reason_codes.append("PROMOTION_CRITERIA_NOT_MET")
    return {
        "schema_version": "distillation_promotion_decision.v1",
        "decision": recommendation,
        "accepted": accepted,
        "reason_codes": reason_codes,
        "baseline_bundle_digest": comparison["baseline"]["bundle_digest"],
        "revised_bundle_digest": comparison["revised"]["bundle_digest"],
        "digest_changed": comparison["baseline"]["bundle_digest"] != comparison["revised"]["bundle_digest"],
    }


def render_comparison_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Distillation Feedback Loop Comparison",
        "",
        "## Summary",
        "",
        f"- baseline_bundle_digest: `{report['baseline']['bundle_digest']}`",
        f"- revised_bundle_digest: `{report['revised']['bundle_digest']}`",
        f"- baseline_pass_count: `{report['baseline']['pass_count']}`",
        f"- revised_pass_count: `{report['revised']['pass_count']}`",
        f"- pass_count_delta: `{report['delta']['pass_count_delta']}`",
        f"- unsupported_affected_decision_delta: `{report['delta']['unsupported_affected_decision_delta']}`",
        f"- regression_count: `{report['delta']['regression_count']}`",
        f"- promotion_recommendation: `{report['promotion_recommendation']}`",
        "",
        "## Required Evidence",
        "",
        f"- baseline: `{json.dumps(report['baseline']['required_evidence'])}`",
        f"- revised: `{json.dumps(report['revised']['required_evidence'])}`",
        "",
        "This comparison is a bounded deterministic distillation-loop result. It does not prove compiler superiority or vulnerability discovery.",
    ]
    return "\n".join(lines).rstrip() + "\n"


def render_status_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Distillation Feedback Loop Status",
        "",
        f"- distillation_feedback_loop: `{payload['distillation_feedback_loop']}`",
        f"- baseline_bundle_build: `{payload['baseline_bundle_build']}`",
        f"- failure_attribution: `{payload['failure_attribution']}`",
        f"- revision_planner: `{payload['revision_planner']}`",
        f"- revised_bundle_build: `{payload['revised_bundle_build']}`",
        f"- comparison_report: `{payload['comparison_report']}`",
        f"- promotion_decision: `{payload['promotion_decision']}`",
        f"- task_count: `{payload['task_count']}`",
        f"- baseline_pass_count: `{payload['baseline_pass_count']}`",
        f"- revised_pass_count: `{payload['revised_pass_count']}`",
        f"- seeded_counterexample_pass: `{payload['seeded_counterexample_pass']}`",
        "",
        "## Required Acceptance Fields",
        "",
        f"- baseline_policy_required_evidence: `{json.dumps(payload['baseline_policy_required_evidence'])}`",
        f"- revised_policy_required_evidence: `{json.dumps(payload['revised_policy_required_evidence'])}`",
        f"- baseline_failed_task_ids: `{json.dumps(payload['baseline_failed_task_ids'])}`",
        f"- failure_attribution_types: `{json.dumps(payload['failure_attribution_types'])}`",
        f"- revision_targets: `{json.dumps(payload['revision_targets'])}`",
        f"- baseline_bundle_digest: `{payload['baseline_bundle_digest']}`",
        f"- revised_bundle_digest: `{payload['revised_bundle_digest']}`",
        f"- digest_changed: `{payload['digest_changed']}`",
        "",
        "## Claim Boundary",
        "",
        "- This is a bounded deterministic expert distillation feedback loop.",
        "- It does not claim compiler superiority, mature AgentHost effectiveness, vulnerability discovery, official benchmark performance, or production readiness.",
    ]
    return "\n".join(lines).rstrip() + "\n"


def _promotion_recommendation(
    *,
    revised_summary: dict[str, Any],
    revised_aggregate: dict[str, Any],
    regression_count: int,
    seed_summary: dict[str, Any],
    revised_unsupported: int,
    baseline_unsupported: int,
) -> str:
    if int(revised_summary.get("fail_count", 0)) != 0:
        return "reject"
    if regression_count:
        return "reject"
    if not seed_summary.get("revised_seeded_counterexample_pass"):
        return "reject"
    if revised_unsupported > baseline_unsupported:
        return "reject"
    if int(revised_aggregate.get("hidden_gold_leakage_failures", 0)) != 0:
        return "reject"
    if int(revised_aggregate.get("evidence_resolution_failures", 0)) != 0:
        return "reject"
    return "promote"


def _unsupported_affected_count(aggregate: dict[str, Any]) -> int:
    count = 0
    for row in aggregate.get("task_results", []):
        prediction_path = Path(row["prediction_path"])
        if not prediction_path.exists():
            continue
        prediction = json.loads(prediction_path.read_text(encoding="utf-8"))
        evidence_types = {item.get("evidence_type") for item in prediction.get("evidence", []) if isinstance(item, dict)}
        if prediction.get("decision") == "dependency_used_and_affected" and "import_use_site" not in evidence_types:
            count += 1
    return count


def _regression_count(baseline_aggregate: dict[str, Any], revised_aggregate: dict[str, Any]) -> int:
    baseline_by_id = {row["task_id"]: row for row in baseline_aggregate.get("task_results", [])}
    count = 0
    for row in revised_aggregate.get("task_results", []):
        old = baseline_by_id.get(row["task_id"])
        if old and old.get("verifier_pass") is True and row.get("verifier_pass") is not True:
            count += 1
    return count
