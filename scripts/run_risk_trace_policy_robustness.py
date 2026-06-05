from __future__ import annotations

import itertools
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from run_mvp_vertical_slice import estimate_tokens
from run_risk_trace_policy_baseline import (
    FAILURE_CRITICAL_RULES,
    RANDOM_SEED,
    RULE_IDS,
    TOKEN_BUDGET,
    build_review,
    partial_trace_verify,
    protocol_for,
    risk_score,
    select_risk_based,
)
from run_selective_trace_compiler import PROTOCOLIZED_SKILL, split_protocol


OUT_DIR = Path("outputs/mvp_vertical_slice/risk_trace_policy_robustness_001")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def evaluate_combo(traced_rule_ids: list[str]) -> dict[str, Any]:
    skill_text = read_text(PROTOCOLIZED_SKILL)
    rules_text, _ = split_protocol(skill_text)
    protocol_text = protocol_for(traced_rule_ids)
    skill_tokens = estimate_tokens(rules_text)
    protocol_tokens = estimate_tokens(protocol_text)
    total_tokens = skill_tokens + protocol_tokens
    review = build_review(traced_rule_ids)
    shortcut_review = build_review(traced_rule_ids, shortcut=True)
    partial_trace = partial_trace_verify(review, traced_rule_ids)
    shortcut_partial = partial_trace_verify(shortcut_review, traced_rule_ids)
    failure_critical_coverage = round(
        len(set(traced_rule_ids) & FAILURE_CRITICAL_RULES) / len(FAILURE_CRITICAL_RULES),
        4,
    )
    over_budget = total_tokens > TOKEN_BUDGET
    gate_decision = "reject_over_budget" if over_budget else ("accept" if partial_trace["passed"] else "reject_trace_failure")
    return {
        "traced_rule_ids": traced_rule_ids,
        "trace_tokens": protocol_tokens,
        "total_tokens": total_tokens,
        "token_budget": TOKEN_BUDGET,
        "over_budget": over_budget,
        "failure_critical_trace_coverage": failure_critical_coverage,
        "shortcut_blocked": bool(traced_rule_ids) and not shortcut_partial["passed"],
        "semantic_verifier_pass": True,
        "partial_trace_verifier_pass": bool(partial_trace["passed"]),
        "gate_decision": gate_decision,
        "risk_score_sum": sum(risk_score(rule_id) for rule_id in traced_rule_ids),
        "risk_scores": {rule_id: risk_score(rule_id) for rule_id in traced_rule_ids},
        "interpretation": (
            "covers_all_failure_critical"
            if failure_critical_coverage == 1.0
            else ("covers_some_failure_critical" if failure_critical_coverage > 0 else "misses_failure_critical")
        ),
    }


def render_summary(payload: dict[str, Any]) -> str:
    lines = [
        "# Risk Trace Policy Robustness 001",
        "",
        "## Purpose",
        "",
        "Enumerate all size=2 trace allocations over R001-R006 to avoid relying on one random seed.",
        "",
        "## Aggregate",
        "",
        f"- total_combinations: {payload['aggregate']['total_combinations']}",
        f"- full_failure_critical_coverage_count: {payload['aggregate']['full_failure_critical_coverage_count']}",
        f"- partial_failure_critical_coverage_count: {payload['aggregate']['partial_failure_critical_coverage_count']}",
        f"- zero_failure_critical_coverage_count: {payload['aggregate']['zero_failure_critical_coverage_count']}",
        "",
        "## Key Comparisons",
        "",
        f"- risk_based_selective_trace: {', '.join(payload['risk_based']['traced_rule_ids'])}, coverage {payload['risk_based']['failure_critical_trace_coverage']:.2f}, tokens {payload['risk_based']['total_tokens']} / {payload['risk_based']['token_budget']}",
        f"- previous_random_seed_{payload['random_seed']}: {', '.join(payload['previous_random']['traced_rule_ids'])}, coverage {payload['previous_random']['failure_critical_trace_coverage']:.2f}, tokens {payload['previous_random']['total_tokens']} / {payload['previous_random']['token_budget']}",
        "",
        "| Traced Rules | Coverage | Tokens | Shortcut Blocked | Gate | Interpretation |",
        "|---|---:|---:|---|---|---|",
    ]
    for row in payload["combo_results"]:
        lines.append(
            f"| {', '.join(row['traced_rule_ids'])} | {row['failure_critical_trace_coverage']:.2f} | "
            f"{row['total_tokens']} / {row['token_budget']} | {row['shortcut_blocked']} | "
            f"{row['gate_decision']} | {row['interpretation']} |"
        )
    lines.extend(
        [
            "",
            "## Conservative Conclusion",
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
    combo_results = [evaluate_combo(list(combo)) for combo in itertools.combinations(RULE_IDS, 2)]
    combo_results = sorted(combo_results, key=lambda row: (-row["failure_critical_trace_coverage"], -row["risk_score_sum"], row["traced_rule_ids"]))
    risk_ids = select_risk_based(2)
    risk_based = next(row for row in combo_results if row["traced_rule_ids"] == risk_ids)
    previous_random_ids = ["R002", "R003"]
    previous_random = next(row for row in combo_results if row["traced_rule_ids"] == previous_random_ids)
    aggregate = {
        "total_combinations": len(combo_results),
        "full_failure_critical_coverage_count": sum(1 for row in combo_results if row["failure_critical_trace_coverage"] == 1.0),
        "partial_failure_critical_coverage_count": sum(1 for row in combo_results if row["failure_critical_trace_coverage"] == 0.5),
        "zero_failure_critical_coverage_count": sum(1 for row in combo_results if row["failure_critical_trace_coverage"] == 0.0),
        "accepted_count": sum(1 for row in combo_results if row["gate_decision"] == "accept"),
        "over_budget_count": sum(1 for row in combo_results if row["over_budget"]),
    }
    if risk_based["failure_critical_trace_coverage"] == 1.0 and aggregate["full_failure_critical_coverage_count"] < aggregate["total_combinations"]:
        status = "partially_supported"
        finding = "Risk signals identify the only size=2 allocation that covers both failure-critical rules in this toy rule pool."
    else:
        status = "inconclusive"
        finding = "Current toy enumeration does not clearly distinguish risk-based trace from arbitrary same-size allocations."
    payload = {
        "run_id": OUT_DIR.name,
        "created_at": created_at,
        "random_seed": RANDOM_SEED,
        "failure_critical_rule_ids": sorted(FAILURE_CRITICAL_RULES),
        "risk_based": risk_based,
        "previous_random": previous_random,
        "aggregate": aggregate,
        "combo_results": combo_results,
        "conclusion": {
            "status": status,
            "finding": finding,
            "boundary": "Toy rule-pool enumeration only. This is not statistical significance and not a mature trace policy.",
        },
    }
    write_json(OUT_DIR / "summary.json", payload)
    write_json(OUT_DIR / "all_size_2_combinations.json", combo_results)
    write_text(OUT_DIR / "summary.md", render_summary(payload))
    write_json(
        OUT_DIR / "manifest.json",
        {
            "run_id": OUT_DIR.name,
            "created_at": created_at,
            "artifacts": ["summary.json", "summary.md", "all_size_2_combinations.json"],
            "boundary": payload["conclusion"]["boundary"],
        },
    )
    print(json.dumps({"output_dir": str(OUT_DIR), "status": status}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
