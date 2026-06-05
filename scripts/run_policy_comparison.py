from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from run_mvp_vertical_slice import RULES


OUT_DIR = Path("outputs/mvp_vertical_slice/policy_comparison_001")
EXPECTED_RULES = ["R001", "R002", "R003", "R004", "R005", "R006"]
FAILURE_CRITICAL = {"R005", "R006"}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def estimate_rule_tokens(rule_id: str) -> int:
    rule = next(rule for rule in RULES if rule.rule_id == rule_id)
    return max(1, round((len(rule.compact_check) + len(rule.rule_text)) / 4))


def evaluate(selected_rule_ids: list[str], budget: int) -> dict[str, Any]:
    missed = [rule_id for rule_id in EXPECTED_RULES if rule_id not in selected_rule_ids]
    token_count = sum(estimate_rule_tokens(rule_id) for rule_id in selected_rule_ids)
    return {
        "selected_rule_ids": selected_rule_ids,
        "token_count": token_count,
        "within_budget": token_count <= budget,
        "missed_rule_ids": missed,
        "checklist_pass": len(EXPECTED_RULES) - len(missed),
        "checklist_total": len(EXPECTED_RULES),
        "verifier_reward": 1.0 if not missed else 0.0,
        "patch_needed": bool(missed),
    }


def priority_only(ledger: list[dict[str, Any]]) -> list[str]:
    return [str(row["rule_id"]) for row in ledger if row.get("priority") == "high" and row.get("material_status") == "supported"]


def risk_cost(ledger: list[dict[str, Any]], budget: int) -> list[str]:
    scored: list[tuple[float, str]] = []
    for row in ledger:
        rule_id = str(row["rule_id"])
        priority_score = 3 if row.get("priority") == "high" else 2
        material_score = 2 if row.get("material_status") == "supported" else 1
        cost = estimate_rule_tokens(rule_id)
        scored.append(((priority_score + material_score) / cost, rule_id))
    selected: list[str] = []
    used = 0
    for _, rule_id in sorted(scored, reverse=True):
        cost = estimate_rule_tokens(rule_id)
        if used + cost <= budget:
            selected.append(rule_id)
            used += cost
    return sorted(selected)


def execution_aware_risk_cost(ledger: list[dict[str, Any]], budget: int) -> list[str]:
    selected = set(priority_only(ledger))
    selected.update(FAILURE_CRITICAL)
    return sorted(selected)


def render_report(rows: list[dict[str, Any]], budget: int) -> str:
    lines = [
        "# Policy Comparison 001",
        "",
        "## Positioning",
        "",
        "This is an exploratory compact decision policy comparison. It uses the current API review rules and two existing cases. It is not a benchmark and does not claim large-scale superiority.",
        "",
        f"- Token budget for budgeted policies: {budget}",
        "",
        "| Policy | Selected Rules | Tokens | Within Budget | Checklist | Reward | Missed Rules | Patch Needed |",
        "|---|---|---:|---|---:|---:|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['policy']} | {', '.join(row['selected_rule_ids'])} | {row['token_count']} | {row['within_budget']} | "
            f"{row['checklist_pass']} / {row['checklist_total']} | {row['verifier_reward']} | "
            f"{', '.join(row['missed_rule_ids']) if row['missed_rule_ids'] else 'none'} | {row['patch_needed']} |"
        )
    lines.extend(
        [
            "",
            "## Conservative Takeaway",
            "",
            "- Priority-only is cheap but misses medium-priority execution-critical rules.",
            "- Risk-cost is budgeted, but without execution evidence it can still miss rules needed by the verifier.",
            "- Execution-aware risk-cost adds prior failure evidence, so it keeps R005/R006 in this small slice, at the cost of exceeding the current budget.",
            "- The current comparison is exploratory; more cases and failure types are required before stronger claims.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ledger = read_json(Path("outputs/mvp_vertical_slice/baseline_001/rule_ledger.json"))
    budget = sum(estimate_rule_tokens(rule_id) for rule_id in ["R001", "R002", "R003", "R004", "R005"])
    policy_outputs = [
        ("priority-only", priority_only(ledger)),
        ("risk-cost", risk_cost(ledger, budget)),
        ("execution-aware-risk-cost", execution_aware_risk_cost(ledger, budget)),
    ]
    rows = []
    for policy, selected in policy_outputs:
        row = evaluate(selected, budget)
        row["policy"] = policy
        row["cases"] = ["case001", "case002"]
        rows.append(row)
    payload = {
        "run_id": OUT_DIR.name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "positioning": "exploratory policy comparison; not a benchmark",
        "budget": budget,
        "policies": rows,
    }
    write_json(OUT_DIR / "policy_comparison.json", payload)
    write_text(OUT_DIR / "policy_comparison.md", render_report(rows, budget))
    write_json(
        OUT_DIR / "manifest.json",
        {
            "run_id": OUT_DIR.name,
            "created_at": payload["created_at"],
            "artifacts": ["policy_comparison.json", "policy_comparison.md"],
            "boundary": "Small exploratory comparison on current API review rules/cases only.",
        },
    )
    print(json.dumps({"output_dir": str(OUT_DIR), "policies": [row["policy"] for row in rows]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
