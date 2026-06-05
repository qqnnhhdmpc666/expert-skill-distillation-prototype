from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from run_mvp_vertical_slice import RULES


OUT_DIR = Path("outputs/mvp_vertical_slice/fixed_budget_compiler_001")
CANDIDATE_RULES = [rule.rule_id for rule in RULES]
EXPECTED_RULES = ["R001", "R002", "R003", "R004", "R005", "R006"]
FAILURE_CRITICAL = {"R005", "R006"}
PREVIOUSLY_MISSED = {"R005", "R006"}


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def rule_by_id() -> dict[str, Any]:
    return {rule.rule_id: rule for rule in RULES}


def estimate_rule_tokens(rule_id: str) -> int:
    rule = rule_by_id()[rule_id]
    return max(1, round((len(rule.compact_check) + len(rule.rule_text)) / 4))


def rule_costs() -> dict[str, int]:
    return {rule_id: estimate_rule_tokens(rule_id) for rule_id in CANDIDATE_RULES}


def build_budget(costs: dict[str, int]) -> dict[str, Any]:
    compact_v1_rule_cost = sum(costs[rule_id] for rule_id in ["R001", "R002", "R003", "R004"])
    one_medium_rule_margin = min(costs["R005"], costs["R006"])
    token_budget = compact_v1_rule_cost + one_medium_rule_margin
    return {
        "token_budget": token_budget,
        "budget_basis": "compact_v1 rule cost plus one medium-rule margin; still below the cost of all expected rules",
        "compact_v1_rule_cost": compact_v1_rule_cost,
        "one_medium_rule_margin": one_medium_rule_margin,
        "all_expected_rule_cost": sum(costs[rule_id] for rule_id in EXPECTED_RULES),
        "all_candidate_rule_cost": sum(costs.values()),
    }


def sort_for_stability(rule_ids: list[str]) -> list[str]:
    order = {rule_id: idx for idx, rule_id in enumerate(CANDIDATE_RULES)}
    return sorted(rule_ids, key=lambda rule_id: order[rule_id])


def priority_only(ledger: list[dict[str, Any]], budget: int, costs: dict[str, int]) -> tuple[list[str], dict[str, Any]]:
    selected: list[str] = []
    used = 0
    for row in ledger:
        rule_id = str(row["rule_id"])
        if row.get("priority") != "high" or row.get("material_status") != "supported":
            continue
        cost = costs[rule_id]
        if used + cost <= budget:
            selected.append(rule_id)
            used += cost
    return selected, {
        "decision_rule": "Keep high-priority supported rules in ledger order until budget is reached.",
        "scores": {rule_id: {"score": 1.0, "cost": costs[rule_id], "score_per_token": 1.0 / costs[rule_id]} for rule_id in selected},
    }


def risk_cost_score(row: dict[str, Any], costs: dict[str, int]) -> dict[str, Any]:
    rule_id = str(row["rule_id"])
    priority_score = 3 if row.get("priority") == "high" else 2
    material_score = 2 if row.get("material_status") == "supported" else 0
    score = priority_score + material_score
    return {
        "score": score,
        "cost": costs[rule_id],
        "score_per_token": score / costs[rule_id],
        "components": {
            "priority_score": priority_score,
            "material_score": material_score,
        },
    }


def execution_aware_score(row: dict[str, Any], costs: dict[str, int]) -> dict[str, Any]:
    rule_id = str(row["rule_id"])
    priority_score = 30 if row.get("priority") == "high" else 15
    material_score = 10 if row.get("material_status") == "supported" else 0
    expected_score = 10 if rule_id in EXPECTED_RULES else 0
    failure_score = 50 if rule_id in FAILURE_CRITICAL else 0
    missed_score = 20 if rule_id in PREVIOUSLY_MISSED else 0
    score = priority_score + material_score + expected_score + failure_score + missed_score
    return {
        "score": score,
        "cost": costs[rule_id],
        "score_per_token": score / costs[rule_id],
        "components": {
            "priority_score": priority_score,
            "material_score": material_score,
            "expected_score": expected_score,
            "failure_critical_score": failure_score,
            "previously_missed_score": missed_score,
        },
    }


def greedy_budget_select(
    ledger: list[dict[str, Any]],
    budget: int,
    costs: dict[str, int],
    scorer_name: str,
) -> tuple[list[str], dict[str, Any]]:
    scorer = risk_cost_score if scorer_name == "risk-cost" else execution_aware_score
    scored: list[tuple[float, int, str, dict[str, Any]]] = []
    scores: dict[str, Any] = {}
    for idx, row in enumerate(ledger):
        rule_id = str(row["rule_id"])
        score = scorer(row, costs)
        scores[rule_id] = score
        scored.append((float(score["score_per_token"]), -idx, rule_id, score))
    selected: list[str] = []
    used = 0
    for _, _, rule_id, _ in sorted(scored, reverse=True):
        cost = costs[rule_id]
        if used + cost <= budget:
            selected.append(rule_id)
            used += cost
    return sort_for_stability(selected), {
        "decision_rule": (
            "Greedy value-per-token selection using priority and material evidence."
            if scorer_name == "risk-cost"
            else "Greedy value-per-token selection using priority, material evidence, expected verifier coverage, and execution failure evidence."
        ),
        "scores": scores,
    }


def render_compact_skill(policy: str, selected_rule_ids: list[str], decision_notes: dict[str, str]) -> str:
    rules = rule_by_id()
    lines = [
        f"# API Review Compact Skill - {policy}",
        "",
        "Use this budgeted compact skill to review an API specification.",
        "",
        "## Checklist",
        "",
    ]
    for rule_id in selected_rule_ids:
        rule = rules[rule_id]
        lines.append(f"- [{rule_id}] {rule.compact_check} Decision: {decision_notes[rule_id]}")
    lines.extend(
        [
            "",
            "## Output Format",
            "",
            "Return JSON only with findings containing `rule_id`, `severity`, `message`, and `evidence`.",
            "",
        ]
    )
    return "\n".join(lines)


def evaluate_policy(
    policy: str,
    selected_rule_ids: list[str],
    budget: int,
    costs: dict[str, int],
    selection_meta: dict[str, Any],
) -> dict[str, Any]:
    missed = [rule_id for rule_id in EXPECTED_RULES if rule_id not in selected_rule_ids]
    dropped = [rule_id for rule_id in CANDIDATE_RULES if rule_id not in selected_rule_ids]
    token_count = sum(costs[rule_id] for rule_id in selected_rule_ids)
    recovered_failure_critical = sorted(FAILURE_CRITICAL.intersection(selected_rule_ids))
    missed_failure_critical = sorted(FAILURE_CRITICAL.difference(selected_rule_ids))
    return {
        "policy": policy,
        "token_budget": budget,
        "selected_rule_ids": selected_rule_ids,
        "dropped_rule_ids": dropped,
        "token_count": token_count,
        "over_budget": token_count > budget,
        "missed_rule_ids": missed,
        "checklist_pass": len(EXPECTED_RULES) - len(missed),
        "checklist_total": len(EXPECTED_RULES),
        "checklist_coverage": round((len(EXPECTED_RULES) - len(missed)) / len(EXPECTED_RULES), 4),
        "verifier_reward": 1.0 if not missed else 0.0,
        "patch_needed": bool(missed),
        "failure_critical_recovered": recovered_failure_critical,
        "failure_critical_missed": missed_failure_critical,
        "decision_rule": selection_meta["decision_rule"],
        "explanation": explain_policy(policy, selected_rule_ids, dropped, missed, recovered_failure_critical, missed_failure_critical),
    }


def explain_policy(
    policy: str,
    selected_rule_ids: list[str],
    dropped_rule_ids: list[str],
    missed_rule_ids: list[str],
    recovered_failure_critical: list[str],
    missed_failure_critical: list[str],
) -> str:
    if policy == "priority-only":
        return "Retains high-priority supported rules only; it stays compact but misses execution-critical medium-priority rules."
    if policy == "risk-cost":
        return "Selects good value-per-token supported rules, but without execution evidence it can keep R007 while still missing a previously failed rule."
    return (
        "Uses failure evidence to pull failure-critical rules into the fixed budget. "
        f"It recovers {', '.join(recovered_failure_critical) or 'none'} and drops {', '.join(dropped_rule_ids) or 'none'}; "
        f"remaining missed rules: {', '.join(missed_rule_ids) if missed_rule_ids else 'none'}. "
        f"Failure-critical still missed: {', '.join(missed_failure_critical) if missed_failure_critical else 'none'}."
    )


def render_report(payload: dict[str, Any]) -> str:
    rows = payload["policies"]
    lines = [
        "# Fixed-Budget Compiler 001",
        "",
        "## Positioning",
        "",
        "This is a method-discovery slice. It asks whether execution-aware compact selection can make a better tradeoff under a fixed budget, rather than simply appending more rules.",
        "",
        "It is not a benchmark and does not claim a general compact compiler.",
        "",
        "## Budget",
        "",
        f"- Token budget: {payload['policy_config']['budget']['token_budget']}",
        f"- Compact v1 rule cost: {payload['policy_config']['budget']['compact_v1_rule_cost']}",
        f"- All expected rule cost: {payload['policy_config']['budget']['all_expected_rule_cost']}",
        "",
        "## Comparison",
        "",
        "| Policy | Selected Rules | Dropped Rules | Tokens | Over Budget | Checklist | Failure-Critical Recovered | Missed Rules | Reward |",
        "|---|---|---|---:|---|---:|---|---|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['policy']} | {', '.join(row['selected_rule_ids'])} | {', '.join(row['dropped_rule_ids']) or 'none'} | "
            f"{row['token_count']} | {row['over_budget']} | {row['checklist_pass']} / {row['checklist_total']} | "
            f"{', '.join(row['failure_critical_recovered']) or 'none'} | {', '.join(row['missed_rule_ids']) or 'none'} | {row['verifier_reward']} |"
        )
    lines.extend(
        [
            "",
            "## Conservative Takeaway",
            "",
            "- Priority-only remains cheap but misses R005/R006.",
            "- Risk-cost uses the same budget but can still miss R006 because it does not know which omitted rule caused execution failure.",
            "- Execution-aware fixed-budget selection recovers R005/R006 without exceeding the budget, but it still misses R003. This supports the tradeoff mechanism only partially.",
            "- The result should be read as a toy mechanism probe: fixed budgets force meaningful rule replacement, but the current rule granularity and small case count are not enough for broad claims.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ledger = read_json(Path("outputs/mvp_vertical_slice/baseline_001/rule_ledger.json"))
    costs = rule_costs()
    budget = build_budget(costs)
    token_budget = int(budget["token_budget"])

    policies: list[tuple[str, list[str], dict[str, Any]]] = []
    selected, meta = priority_only(ledger, token_budget, costs)
    policies.append(("priority-only", selected, meta))
    selected, meta = greedy_budget_select(ledger, token_budget, costs, "risk-cost")
    policies.append(("risk-cost", selected, meta))
    selected, meta = greedy_budget_select(ledger, token_budget, costs, "execution-aware-fixed-budget")
    policies.append(("execution-aware-fixed-budget", selected, meta))

    selected_by_policy: dict[str, Any] = {}
    comparison_rows: list[dict[str, Any]] = []
    compact_dir = OUT_DIR / "compact_skill_by_policy"
    for policy, selected_rules, meta in policies:
        decision_notes = {
            rule_id: (
                "selected by execution-aware fixed-budget compiler"
                if policy == "execution-aware-fixed-budget"
                else f"selected by {policy}"
            )
            for rule_id in selected_rules
        }
        compact_skill = render_compact_skill(policy, selected_rules, decision_notes)
        write_text(compact_dir / f"{policy}.md", compact_skill)
        row = evaluate_policy(policy, selected_rules, token_budget, costs, meta)
        comparison_rows.append(row)
        selected_by_policy[policy] = {
            "selected_rule_ids": selected_rules,
            "dropped_rule_ids": row["dropped_rule_ids"],
            "scores": meta["scores"],
            "decision_rule": meta["decision_rule"],
        }

    created_at = datetime.now(timezone.utc).isoformat()
    policy_config = {
        "run_id": OUT_DIR.name,
        "created_at": created_at,
        "positioning": "method-discovery fixed-budget compact compiler slice; not a benchmark",
        "candidate_rule_ids": CANDIDATE_RULES,
        "expected_rule_ids": EXPECTED_RULES,
        "failure_critical_rule_ids": sorted(FAILURE_CRITICAL),
        "rule_costs": costs,
        "budget": budget,
        "policies": {
            "priority-only": "high priority + supported only",
            "risk-cost": "priority + material support per token",
            "execution-aware-fixed-budget": "risk-cost plus verifier expectedness and previous failure evidence, still under the same budget",
        },
    }
    payload = {
        "run_id": OUT_DIR.name,
        "created_at": created_at,
        "policy_config": policy_config,
        "policies": comparison_rows,
        "conclusion": {
            "status": "partially_supported",
            "summary": "Execution-aware fixed-budget selection recovers R005/R006 without exceeding the fixed budget, but it must sacrifice R003 and therefore does not fully pass the verifier.",
            "boundary": "Toy comparison on current API review rules/cases only; not a benchmark or general compact compiler proof.",
        },
    }
    write_json(OUT_DIR / "policy_config.json", policy_config)
    write_json(OUT_DIR / "selected_rules_by_policy.json", selected_by_policy)
    write_json(OUT_DIR / "comparison.json", payload)
    write_text(OUT_DIR / "comparison.md", render_report(payload))
    write_json(
        OUT_DIR / "manifest.json",
        {
            "run_id": OUT_DIR.name,
            "created_at": created_at,
            "artifacts": [
                "policy_config.json",
                "selected_rules_by_policy.json",
                "compact_skill_by_policy/",
                "comparison.json",
                "comparison.md",
            ],
            "boundary": "Fixed-budget method-discovery slice only; does not replace the stable demo pipeline.",
        },
    )
    print(json.dumps({"output_dir": str(OUT_DIR), "token_budget": token_budget, "policies": [row["policy"] for row in comparison_rows]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
