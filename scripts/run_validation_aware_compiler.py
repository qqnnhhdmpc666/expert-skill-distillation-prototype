from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from run_mvp_vertical_slice import RULES


OUT_DIR = Path("outputs/mvp_vertical_slice/validation_aware_compiler_001")
EXPECTED_RULES = ["R001", "R002", "R003", "R004", "R005", "R006"]
PREVIOUSLY_COVERED = ["R001", "R002", "R003", "R004"]
FAILURE_CRITICAL = ["R005", "R006"]
OPTIONAL_RULES = ["R007"]
OUTPUT_CONTRACT_RULES: list[str] = []

COMPRESSED_CHECKS = {
    "R001": "Auth method, roles/scopes, and auth-failure behavior.",
    "R002": "Request fields: required/default, type, range, length, enum.",
    "R003": "Stable error codes for validation, auth, permission, not found, duplicate, server.",
    "R004": "No tokens, secrets, stack traces, identity, or unnecessary personal data.",
    "R005": "Response envelope: code, message, request_id, data.",
    "R006": "Mutation idempotency or duplicate-submission handling.",
}


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def rule_by_id() -> dict[str, Any]:
    return {rule.rule_id: rule for rule in RULES}


def estimate_rule_tokens(rule_id: str) -> int:
    rule = rule_by_id()[rule_id]
    return max(1, round((len(rule.compact_check) + len(rule.rule_text)) / 4))


def estimate_compressed_rule_tokens(rule_id: str) -> int:
    return max(1, round(len(COMPRESSED_CHECKS[rule_id]) / 4))


def token_count(rule_ids: list[str], compressed: bool = False) -> int:
    estimator = estimate_compressed_rule_tokens if compressed else estimate_rule_tokens
    return sum(estimator(rule_id) for rule_id in rule_ids)


def build_budget() -> dict[str, Any]:
    costs = {rule.rule_id: estimate_rule_tokens(rule.rule_id) for rule in RULES}
    compact_v1_rule_cost = sum(costs[rule_id] for rule_id in PREVIOUSLY_COVERED)
    one_medium_rule_margin = min(costs[rule_id] for rule_id in FAILURE_CRITICAL)
    token_budget = compact_v1_rule_cost + one_medium_rule_margin
    return {
        "token_budget": token_budget,
        "budget_basis": "same as fixed_budget_compiler_001: compact_v1 rule cost plus one medium-rule margin",
        "compact_v1_rule_cost": compact_v1_rule_cost,
        "one_medium_rule_margin": one_medium_rule_margin,
        "required_original_rule_cost": token_count(EXPECTED_RULES),
        "required_compressed_rule_cost": token_count(EXPECTED_RULES, compressed=True),
        "rule_costs": costs,
        "compressed_rule_costs": {rule_id: estimate_compressed_rule_tokens(rule_id) for rule_id in EXPECTED_RULES},
    }


def validate_candidate(candidate: dict[str, Any], budget: int) -> dict[str, Any]:
    selected = set(candidate["selected_rule_ids"])
    required = set(PREVIOUSLY_COVERED) | set(FAILURE_CRITICAL) | set(OUTPUT_CONTRACT_RULES)
    missed = [rule_id for rule_id in EXPECTED_RULES if rule_id not in selected]
    missing_failure_critical = [rule_id for rule_id in FAILURE_CRITICAL if rule_id not in selected]
    lost_previously_covered = [rule_id for rule_id in PREVIOUSLY_COVERED if rule_id not in selected]
    missing_output_contract = [rule_id for rule_id in OUTPUT_CONTRACT_RULES if rule_id not in selected]
    over_budget = candidate["token_count"] > budget
    hard_missing = [rule_id for rule_id in required if rule_id not in selected]
    accepted = not hard_missing and not over_budget
    if candidate.get("status") == "infeasible_under_budget":
        decision = "infeasible"
    elif accepted:
        decision = "accept"
    elif over_budget:
        decision = "reject_over_budget"
    elif lost_previously_covered:
        decision = "reject_regression"
    elif missing_failure_critical:
        decision = "reject_missing_failure_critical"
    else:
        decision = "reject_constraint_violation"
    return {
        "candidate_id": candidate["candidate_id"],
        "status": candidate.get("status", "candidate"),
        "selected_rule_ids": candidate["selected_rule_ids"],
        "dropped_rule_ids": candidate["dropped_rule_ids"],
        "token_count": candidate["token_count"],
        "token_budget": budget,
        "over_budget": over_budget,
        "covered_rule_ids": [rule_id for rule_id in EXPECTED_RULES if rule_id in selected],
        "missed_rule_ids": missed,
        "missing_failure_critical_rules": missing_failure_critical,
        "lost_previously_covered_rules": lost_previously_covered,
        "missing_output_contract_rules": missing_output_contract,
        "hard_constraints_satisfied": not hard_missing and not over_budget,
        "validation_result": decision,
        "accepted": accepted,
        "explanation": candidate["explanation"],
    }


def render_skill(candidate: dict[str, Any]) -> str:
    rules = rule_by_id()
    compressed = bool(candidate.get("compressed"))
    lines = [
        f"# Validation-Aware Compact Skill - {candidate['candidate_id']}",
        "",
        candidate["explanation"],
        "",
        "## Checklist",
        "",
    ]
    for rule_id in candidate["selected_rule_ids"]:
        text = COMPRESSED_CHECKS[rule_id] if compressed else rules[rule_id].compact_check
        lines.append(f"- [{rule_id}] {text}")
    lines.extend(
        [
            "",
            "## Output Format",
            "",
            "Return JSON only. Each finding must include `rule_id`, `severity`, `message`, and `evidence`.",
            "",
        ]
    )
    return "\n".join(lines)


def candidate_payload(
    candidate_id: str,
    selected: list[str],
    budget: int,
    explanation: str,
    compressed: bool = False,
    status: str = "candidate",
) -> dict[str, Any]:
    selected_set = set(selected)
    return {
        "candidate_id": candidate_id,
        "status": status,
        "selected_rule_ids": selected,
        "dropped_rule_ids": [rule.rule_id for rule in RULES if rule.rule_id not in selected_set],
        "token_count": token_count(selected, compressed=compressed) if selected else 0,
        "over_budget": (token_count(selected, compressed=compressed) if selected else 0) > budget,
        "compressed": compressed,
        "explanation": explanation,
    }


def build_candidates(budget: int, budget_info: dict[str, Any]) -> list[dict[str, Any]]:
    naive = candidate_payload(
        "candidate_A_naive_execution_aware",
        ["R001", "R002", "R004", "R005", "R006"],
        budget,
        "Naive execution-aware fixed-budget selection from fixed_budget_compiler_001. It recovers R005/R006 but drops R003.",
    )
    preserve_first = candidate_payload(
        "candidate_B_preserve_covered_first",
        EXPECTED_RULES,
        budget,
        "Preserve all previously covered R001-R004 and add failure-critical R005/R006 with original wording.",
    )
    compressed = candidate_payload(
        "candidate_C_compressed_required_rules",
        EXPECTED_RULES,
        budget,
        "Preserve R001-R006 by using compressed checklist wording. This is success with compressed wording, not natural success of the original selector.",
        compressed=True,
    )
    infeasible = candidate_payload(
        "candidate_D_infeasible_original_wording",
        [],
        budget,
        "Original R001-R006 wording cannot fit the current budget; required original rule cost exceeds the token budget.",
        status="infeasible_under_budget",
    )
    infeasible.update(
        {
            "required_rule_ids": EXPECTED_RULES,
            "required_original_rule_cost": budget_info["required_original_rule_cost"],
            "token_budget": budget,
            "possible_resolution": [
                "increase budget",
                "compress rule wording",
                "merge rules",
                "relax preservation constraint",
            ],
        }
    )
    return [naive, preserve_first, compressed, infeasible]


def render_summary(payload: dict[str, Any]) -> str:
    lines = [
        "# Validation-Aware Compiler 001",
        "",
        "## Positioning",
        "",
        "This is M2.1: validation-aware fixed-budget recompilation. It links the fixed-budget compiler and rollback gate findings.",
        "",
        "It is a toy mechanism probe, not a general compiler claim.",
        "",
        "## Hard Constraints",
        "",
        f"- Must include failure-critical rules: {', '.join(FAILURE_CRITICAL)}",
        f"- Must preserve previously covered rules: {', '.join(PREVIOUSLY_COVERED)}",
        f"- Must not exceed budget: {payload['compiler_config']['budget']['token_budget']}",
        "",
        "## Candidate Results",
        "",
        "| Candidate | Status | Tokens | Validation | Covered | Missed | Explanation |",
        "|---|---|---:|---|---|---|---|",
    ]
    for row in payload["validation_results"]:
        lines.append(
            f"| {row['candidate_id']} | {row['status']} | {row['token_count']} / {row['token_budget']} | "
            f"{row['validation_result']} | {', '.join(row['covered_rule_ids']) or 'none'} | "
            f"{', '.join(row['missed_rule_ids']) or 'none'} | {row['explanation']} |"
        )
    lines.extend(
        [
            "",
            "## Conclusion",
            "",
            f"- Status: {payload['summary']['conclusion_status']}",
            f"- Finding: {payload['summary']['finding']}",
            f"- Boundary: {payload['summary']['boundary']}",
            "",
        ]
    )
    return "\n".join(lines)


def render_infeasible_report(budget_info: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Infeasible Report",
            "",
            "Original required rules cannot fit the fixed budget.",
            "",
            f"- Token budget: {budget_info['token_budget']}",
            f"- Required original rule cost: {budget_info['required_original_rule_cost']}",
            "",
            "Possible resolutions:",
            "",
            "- Increase budget.",
            "- Compress rule wording.",
            "- Merge related rules.",
            "- Relax preservation constraints.",
            "",
        ]
    )


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    candidate_dir = OUT_DIR / "candidate_skills"
    created_at = datetime.now(timezone.utc).isoformat()
    budget_info = build_budget()
    budget = int(budget_info["token_budget"])
    candidates = build_candidates(budget, budget_info)
    validation_results = [validate_candidate(candidate, budget) for candidate in candidates]
    accepted = [row for row in validation_results if row["accepted"]]
    accepted_candidate = accepted[0] if accepted else None
    conclusion_status = "partially_supported" if accepted_candidate else "inconclusive"
    finding = (
        "Validation-aware fixed-budget recompilation succeeds only when compressed wording is allowed; original wording is infeasible under the current budget."
        if accepted_candidate
        else "No candidate satisfies validation constraints under the current budget."
    )
    boundary = (
        "Toy API-review rules only. Success with compressed wording should not be read as proof of a general compact compiler."
        if accepted_candidate
        else "The current budget or rule granularity is insufficient; this is a negative/inconclusive result, not a hidden success."
    )
    compiler_config = {
        "run_id": OUT_DIR.name,
        "created_at": created_at,
        "positioning": "M2.1 validation-aware fixed-budget compact compiler; method-discovery slice only",
        "hard_constraints": {
            "must_include_failure_critical_rules": FAILURE_CRITICAL,
            "must_preserve_previously_covered_rules": PREVIOUSLY_COVERED,
            "must_include_output_contract_rules": OUTPUT_CONTRACT_RULES,
            "must_not_exceed_budget": True,
        },
        "soft_objectives": [
            "minimize token count",
            "maximize risk/evidence/execution score",
            "prefer supported rules",
            "avoid unsupported or irrelevant rules",
        ],
        "budget": budget_info,
    }
    payload = {
        "run_id": OUT_DIR.name,
        "created_at": created_at,
        "compiler_config": compiler_config,
        "candidates": candidates,
        "validation_results": validation_results,
        "summary": {
            "conclusion_status": conclusion_status,
            "accepted_candidate_id": accepted_candidate["candidate_id"] if accepted_candidate else None,
            "finding": finding,
            "boundary": boundary,
        },
    }
    for candidate in candidates:
        if candidate["selected_rule_ids"]:
            write_text(candidate_dir / f"{candidate['candidate_id']}.md", render_skill(candidate))
    write_json(OUT_DIR / "compiler_config.json", compiler_config)
    write_json(OUT_DIR / "candidates.json", candidates)
    write_json(OUT_DIR / "validation_results.json", validation_results)
    write_json(OUT_DIR / "summary.json", payload["summary"] | {"run_id": OUT_DIR.name, "created_at": created_at})
    write_text(OUT_DIR / "summary.md", render_summary(payload))
    write_text(OUT_DIR / "infeasible_report.md", render_infeasible_report(budget_info))
    if accepted_candidate:
        skill_path = candidate_dir / f"{accepted_candidate['candidate_id']}.md"
        write_text(OUT_DIR / "accepted_candidate.md", skill_path.read_text(encoding="utf-8"))
    write_json(
        OUT_DIR / "manifest.json",
        {
            "run_id": OUT_DIR.name,
            "created_at": created_at,
            "artifacts": [
                "manifest.json",
                "compiler_config.json",
                "candidates.json",
                "validation_results.json",
                "accepted_candidate.md" if accepted_candidate else "infeasible_report.md",
                "infeasible_report.md",
                "summary.json",
                "summary.md",
                "candidate_skills/",
            ],
            "boundary": boundary,
        },
    )
    print(
        json.dumps(
            {
                "output_dir": str(OUT_DIR),
                "conclusion_status": conclusion_status,
                "accepted_candidate_id": accepted_candidate["candidate_id"] if accepted_candidate else None,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
