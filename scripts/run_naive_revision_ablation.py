from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


OUT_DIR = Path("outputs/mvp_vertical_slice/naive_revision_ablation_001")
COUNTERFACTUAL = Path("outputs/mvp_vertical_slice/counterfactual_patch_utility_001/per_failure_results.json")
ROLLBACK = Path("outputs/mvp_vertical_slice/rollback_gate_001/rollback_decision.json")
TRACE = Path("outputs/mvp_vertical_slice/selective_trace_compiler_001/summary.json")
REAL_EFFECT = Path("outputs/mvp_vertical_slice/real_effect_eval_001/summary.json")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def find_record(records: list[dict[str, Any]], failure_case: str, patch_variant: str) -> dict[str, Any]:
    matches = [row for row in records if row["failure_case"] == failure_case and row["patch_variant"] == patch_variant]
    if not matches:
        raise ValueError(f"missing record: {failure_case}/{patch_variant}")
    return matches[0]


def find_trace_variant(trace_summary: dict[str, Any], variant_id: str) -> dict[str, Any]:
    matches = [row for row in trace_summary["variants"] if row["variant_id"] == variant_id]
    if not matches:
        raise ValueError(f"missing trace variant: {variant_id}")
    return matches[0]


def find_effect_variant(real_effect: dict[str, Any], variant: str) -> dict[str, Any]:
    matches = [row for row in real_effect["per_variant_results"] if row["variant"] == variant]
    if not matches:
        raise ValueError(f"missing effect variant: {variant}")
    return matches[0]


def bool_score(value: Any) -> int:
    return 1 if bool(value) else 0


def render_summary(payload: dict[str, Any]) -> str:
    lines = [
        "# Naive Revision Ablation 001",
        "",
        "## Purpose",
        "",
        "Pressure-test whether the proposed expert-skill deployment revision story is more than generic feedback repair.",
        "This is a diagnostic ablation over existing artifacts, not a benchmark.",
        "",
        "## Strategy Comparison",
        "",
        "| Strategy | Missing Rule | Output Format | Regression Safety | Trace Budget | Main Cost / Failure | Interpretation |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in payload["strategy_results"]:
        lines.append(
            f"| {row['strategy']} | {row['missing_rule_result']} | {row['output_format_result']} | "
            f"{row['regression_safety_result']} | {row['trace_budget_result']} | {row['main_cost_or_failure']} | "
            f"{row['interpretation']} |"
        )
    lines.extend(
        [
            "",
            "## Diagnostic Scores",
            "",
        ]
    )
    for row in payload["strategy_scores"]:
        lines.append(
            f"- {row['strategy']}: resolved_axes={row['resolved_axes']}/{row['total_axes']}, "
            f"hard_failures={row['hard_failures']}, notes={row['notes']}"
        )
    lines.extend(
        [
            "",
            "## Conclusion",
            "",
            f"- Status: {payload['conclusion']['status']}",
            f"- Finding: {payload['conclusion']['finding']}",
            f"- Boundary: {payload['conclusion']['boundary']}",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    created_at = datetime.now(timezone.utc).isoformat()
    records = read_json(COUNTERFACTUAL)
    rollback = read_json(ROLLBACK)
    trace_summary = read_json(TRACE)
    real_effect = read_json(REAL_EFFECT)

    missing_no = find_record(records, "missing_rule", "no_patch")
    missing_wrong_contract = find_record(records, "missing_rule", "wrong_type_patch")
    missing_append = find_record(records, "missing_rule", "compiler_patch")
    missing_full = find_record(records, "missing_rule", "full_skill_or_oracle_patch")
    format_no = find_record(records, "output_format_error", "no_patch")
    format_append = find_record(records, "output_format_error", "wrong_missing_rule_patch")
    format_contract = find_record(records, "output_format_error", "output_contract_patch")
    format_full = find_record(records, "output_format_error", "full_contract_patch")

    no_trace = find_trace_variant(trace_summary, "A_no_trace")
    full_trace = find_trace_variant(trace_summary, "B_full_trace")
    selective_trace = find_trace_variant(trace_summary, "C_selective_trace_failure_critical")
    patched_effect = find_effect_variant(real_effect, "patched_compact")
    selective_effect = find_effect_variant(real_effect, "patched_compact_selective_trace")
    full_effect = find_effect_variant(real_effect, "full_skill")

    rollback_decision = rollback["decision"]
    rollback_safe = rollback_decision == "reject_and_rollback"

    strategy_results = [
        {
            "strategy": "no_revision",
            "missing_rule_result": f"resolved={missing_no['failure_resolved']}",
            "output_format_result": f"resolved={format_no['failure_resolved']}",
            "regression_safety_result": "not_applicable",
            "trace_budget_result": "not_applicable",
            "resolved_axes": 0,
            "hard_failures": 2,
            "main_cost_or_failure": "keeps observed deployment failures",
            "interpretation": "useful as lower bound only",
            "source_artifacts": ["counterfactual_patch_utility_001"],
        },
        {
            "strategy": "always_append_domain_rules",
            "missing_rule_result": f"resolved={missing_append['failure_resolved']}",
            "output_format_result": f"resolved={format_append['failure_resolved']}",
            "regression_safety_result": "not_checked",
            "trace_budget_result": "not_checked",
            "resolved_axes": bool_score(missing_append["failure_resolved"]) + bool_score(format_append["failure_resolved"]),
            "hard_failures": 1,
            "main_cost_or_failure": "fixes missing rules but does not fix output-contract failures",
            "interpretation": "too generic; failure type matters",
            "source_artifacts": ["counterfactual_patch_utility_001"],
        },
        {
            "strategy": "always_rewrite_output_contract",
            "missing_rule_result": f"resolved={missing_wrong_contract['failure_resolved']}",
            "output_format_result": f"resolved={format_contract['failure_resolved']}",
            "regression_safety_result": "not_checked",
            "trace_budget_result": "not_checked",
            "resolved_axes": bool_score(missing_wrong_contract["failure_resolved"]) + bool_score(format_contract["failure_resolved"]),
            "hard_failures": 1,
            "main_cost_or_failure": "fixes format failure but does not recover missing domain rules",
            "interpretation": "too generic; failure type matters",
            "source_artifacts": ["counterfactual_patch_utility_001"],
        },
        {
            "strategy": "always_regenerate_full_skill",
            "missing_rule_result": f"resolved={missing_full['failure_resolved']}",
            "output_format_result": f"resolved={format_full['failure_resolved']}",
            "regression_safety_result": "not_targeted",
            "trace_budget_result": "not_targeted",
            "resolved_axes": 2,
            "hard_failures": 0,
            "main_cost_or_failure": f"works as upper bound but avg tokens={full_effect['avg_total_tokens']}",
            "interpretation": "strong but expensive and weakly diagnostic",
            "source_artifacts": ["counterfactual_patch_utility_001", "real_effect_eval_001"],
        },
        {
            "strategy": "accept_if_current_failure_fixed",
            "missing_rule_result": "can_resolve_current_failure",
            "output_format_result": "not_targeted",
            "regression_safety_result": f"unsafe; gate observed {rollback_decision}",
            "trace_budget_result": "not_checked",
            "resolved_axes": 1,
            "hard_failures": 1,
            "main_cost_or_failure": "can promote a patch that regresses previously covered rules",
            "interpretation": "current-failure success is insufficient for deployment promotion",
            "source_artifacts": ["rollback_gate_001"],
        },
        {
            "strategy": "always_full_trace",
            "missing_rule_result": "not_a_patch_strategy",
            "output_format_result": "not_a_patch_strategy",
            "regression_safety_result": "traceable",
            "trace_budget_result": f"over_budget={full_trace['over_budget']} total={full_trace['total_tokens']}/{full_trace['token_budget']}",
            "resolved_axes": bool_score(full_trace["shortcut_blocked"]),
            "hard_failures": bool_score(full_trace["over_budget"]),
            "main_cost_or_failure": "blocks shortcut but exceeds the trace budget",
            "interpretation": "useful upper bound; not deployable under current budget",
            "source_artifacts": ["selective_trace_compiler_001"],
        },
        {
            "strategy": "type_specific_operator_plus_gate_and_selective_trace",
            "missing_rule_result": f"resolved={missing_append['failure_resolved']}",
            "output_format_result": f"resolved={format_contract['failure_resolved']}",
            "regression_safety_result": f"safe_gate={rollback_safe}",
            "trace_budget_result": (
                f"selective_trace over_budget={selective_trace['over_budget']} "
                f"shortcut_blocked={selective_trace['shortcut_blocked']} total={selective_trace['total_tokens']}/{selective_trace['token_budget']}"
            ),
            "resolved_axes": (
                bool_score(missing_append["failure_resolved"]) + bool_score(format_contract["failure_resolved"]) + bool_score(rollback_safe) + bool_score(selective_trace["shortcut_blocked"] and not selective_trace["over_budget"])
            ),
            "hard_failures": 0,
            "main_cost_or_failure": f"avg tokens with selective trace={selective_effect['avg_total_tokens']}; still toy and rule-family-specific",
            "interpretation": "currently best-supported narrow mechanism combination",
            "source_artifacts": [
                "counterfactual_patch_utility_001",
                "rollback_gate_001",
                "selective_trace_compiler_001",
                "real_effect_eval_001",
            ],
        },
    ]

    strategy_scores = [
        {
            "strategy": row["strategy"],
            "resolved_axes": row["resolved_axes"],
            "total_axes": 4,
            "hard_failures": row["hard_failures"],
            "notes": row["interpretation"],
        }
        for row in strategy_results
    ]

    payload = {
        "run_id": OUT_DIR.name,
        "created_at": created_at,
        "positioning": "diagnostic ablation over existing artifacts; not a benchmark",
        "ablation_question": (
            "Are generic strategies such as always append, always regenerate, or always full trace sufficient, "
            "or does the current evidence favor feedback-type-specific operators plus deployment gates?"
        ),
        "strategy_results": strategy_results,
        "strategy_scores": strategy_scores,
        "key_observations": {
            "always_append_failure": "resolves missing_rule but not output_format_error",
            "always_contract_failure": "resolves output_format_error but not missing_rule",
            "always_full_regenerate_tradeoff": f"resolves tested failures but uses full_skill avg tokens {full_effect['avg_total_tokens']}",
            "always_full_trace_tradeoff": f"blocks shortcut but costs {full_trace['total_tokens']}/{full_trace['token_budget']} tokens and is rejected",
            "type_specific_combo": "resolves tested failure types, keeps rollback safety, and uses selective trace under budget in toy slices",
        },
        "conclusion": {
            "status": "partially_supported",
            "finding": (
                "Existing toy artifacts support the claim that generic revision strategies are not enough to explain all observed constraints: "
                "always-append and always-contract each fail one failure type, current-failure-only acceptance can regress, and full trace is over budget. "
                "The best current narrow mechanism is type-specific revision plus deployment promotion gate plus selective trace."
            ),
            "boundary": (
                "This reuses existing controlled artifacts and is not a statistically valid ablation. Full regeneration remains a strong upper bound, "
                "so future work must show the targeted strategy transfers beyond this rule family."
            ),
        },
    }
    write_json(OUT_DIR / "summary.json", payload)
    write_json(OUT_DIR / "strategy_results.json", strategy_results)
    write_text(OUT_DIR / "summary.md", render_summary(payload))
    write_json(
        OUT_DIR / "manifest.json",
        {
            "run_id": OUT_DIR.name,
            "created_at": created_at,
            "artifacts": ["summary.json", "summary.md", "strategy_results.json", "manifest.json"],
            "source_artifacts": [str(COUNTERFACTUAL), str(ROLLBACK), str(TRACE), str(REAL_EFFECT)],
            "boundary": payload["conclusion"]["boundary"],
        },
    )
    print(json.dumps({"output_dir": str(OUT_DIR), "status": payload["conclusion"]["status"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
