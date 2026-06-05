from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from run_mvp_vertical_slice import RULES


OUT_DIR = Path("outputs/mvp_vertical_slice/rollback_gate_001")
BASELINE_SELECTED = ["R001", "R002", "R003", "R004"]
PATCH_SELECTED = ["R001", "R002", "R004", "R005", "R006"]
ORIGINAL_AFFECTED_RULES = ["R005", "R006"]
PREVIOUSLY_COVERED_HOLDOUT_RULES = ["R001", "R002", "R003", "R004"]
FAILURE_CRITICAL = {"R005", "R006"}


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def estimate_rule_tokens(rule_id: str) -> int:
    rule = {rule.rule_id: rule for rule in RULES}[rule_id]
    return max(1, round((len(rule.compact_check) + len(rule.rule_text)) / 4))


def token_count(rule_ids: list[str]) -> int:
    return sum(estimate_rule_tokens(rule_id) for rule_id in rule_ids)


def evaluate_rules(rule_ids: list[str], expected_rule_ids: list[str]) -> dict[str, Any]:
    missed = [rule_id for rule_id in expected_rule_ids if rule_id not in rule_ids]
    return {
        "selected_rule_ids": rule_ids,
        "expected_rule_ids": expected_rule_ids,
        "missed_rule_ids": missed,
        "checklist_pass": len(expected_rule_ids) - len(missed),
        "checklist_total": len(expected_rule_ids),
        "verifier_reward": 1.0 if not missed else 0.0,
    }


def render_report(payload: dict[str, Any]) -> str:
    gate = payload["validation_gate"]
    decision = payload["rollback_decision"]
    lines = [
        "# Rollback Gate 001",
        "",
        "## Positioning",
        "",
        "This is a toy validation-gated revision slice. It checks whether a patch that resolves the original affected rules should still be rejected when it creates a regression.",
        "",
        "It is not a mature rollback system or a benchmark.",
        "",
        "## Patch Proposal",
        "",
        f"- Patch action: {payload['patch_proposal']['patch_action']}",
        f"- Proposed rules: {', '.join(payload['patch_proposal']['selected_rule_ids'])}",
        f"- Token count: {payload['patch_proposal']['token_count']} / budget {payload['patch_proposal']['token_budget']}",
        "",
        "## Gate Result",
        "",
        f"- Resolves original affected rules: {gate['resolves_original_failure']}",
        f"- Regression detected: {gate['regression_detected']}",
        f"- Lost previously covered rules: {', '.join(gate['lost_previously_covered_rules']) if gate['lost_previously_covered_rules'] else 'none'}",
        f"- Over budget: {gate['over_budget']}",
        f"- Broke failure-critical rules: {gate['broke_failure_critical_rules']}",
        "",
        "## Rollback Decision",
        "",
        f"- Decision: {decision['decision']}",
        f"- Reason: {decision['reason']}",
        "",
        "## Conservative Takeaway",
        "",
        "The proposed patch correctly includes R005/R006, but it drops R003, which had been covered by compact v1 and is treated as a holdout regression in this toy gate. This supports the need for a validation gate, but only as a small mechanism probe.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    created_at = datetime.now(timezone.utc).isoformat()
    token_budget = 237
    baseline_tokens = token_count(BASELINE_SELECTED)
    patch_tokens = token_count(PATCH_SELECTED)
    lost_previously_covered = [rule_id for rule_id in PREVIOUSLY_COVERED_HOLDOUT_RULES if rule_id not in PATCH_SELECTED]
    original_missing_after_patch = [rule_id for rule_id in ORIGINAL_AFFECTED_RULES if rule_id not in PATCH_SELECTED]
    failure_critical_missing = sorted(FAILURE_CRITICAL.difference(PATCH_SELECTED))
    resolves_original_failure = not original_missing_after_patch
    regression_detected = bool(lost_previously_covered)
    over_budget = patch_tokens > token_budget
    broke_failure_critical = bool(failure_critical_missing)

    patch_proposal = {
        "patch_id": "rollback-gate-toy-P001",
        "patch_action": "patch_failure_rules_under_budget",
        "original_failure_type": "missing_rule",
        "affected_rule_ids": ORIGINAL_AFFECTED_RULES,
        "selected_rule_ids": PATCH_SELECTED,
        "dropped_rule_ids": [rule_id for rule_id in BASELINE_SELECTED if rule_id not in PATCH_SELECTED],
        "token_budget": token_budget,
        "token_count": patch_tokens,
        "notes": "This patch fixes the originally affected R005/R006 by evicting R003 to stay under budget.",
    }
    before_after = {
        "before": {
            "selected_rule_ids": BASELINE_SELECTED,
            "token_count": baseline_tokens,
            "original_failure_eval": evaluate_rules(BASELINE_SELECTED, ORIGINAL_AFFECTED_RULES),
            "holdout_eval": evaluate_rules(BASELINE_SELECTED, PREVIOUSLY_COVERED_HOLDOUT_RULES),
        },
        "after_patch": {
            "selected_rule_ids": PATCH_SELECTED,
            "token_count": patch_tokens,
            "original_failure_eval": evaluate_rules(PATCH_SELECTED, ORIGINAL_AFFECTED_RULES),
            "holdout_eval": evaluate_rules(PATCH_SELECTED, PREVIOUSLY_COVERED_HOLDOUT_RULES),
        },
    }
    validation_gate = {
        "gate_id": "rollback_gate_v0",
        "checks": [
            "resolves_original_failure",
            "no_holdout_regression",
            "within_token_budget",
            "preserves_failure_critical_rules",
        ],
        "resolves_original_failure": resolves_original_failure,
        "regression_detected": regression_detected,
        "lost_previously_covered_rules": lost_previously_covered,
        "over_budget": over_budget,
        "broke_failure_critical_rules": broke_failure_critical,
        "failure_critical_missing": failure_critical_missing,
        "accepted": resolves_original_failure and not regression_detected and not over_budget and not broke_failure_critical,
    }
    rollback_decision = {
        "decision": "reject_and_rollback" if not validation_gate["accepted"] else "accept_patch",
        "rollback_to": "compact_v1_baseline" if not validation_gate["accepted"] else None,
        "reason": (
            "Patch resolves R005/R006 but drops R003, causing a holdout regression; rollback keeps the previous compact skill."
            if not validation_gate["accepted"]
            else "Patch passed all validation checks."
        ),
    }
    payload = {
        "run_id": OUT_DIR.name,
        "created_at": created_at,
        "positioning": "toy rollback/validation-gated revision slice; not a benchmark",
        "patch_proposal": patch_proposal,
        "validation_gate": validation_gate,
        "rollback_decision": rollback_decision,
        "before_after_comparison": before_after,
        "boundary": "This slice only shows that a patch can be rejected for regression despite resolving the original affected rules.",
    }
    write_json(OUT_DIR / "patch_proposal.json", patch_proposal)
    write_json(OUT_DIR / "validation_gate.json", validation_gate)
    write_json(OUT_DIR / "rollback_decision.json", rollback_decision)
    write_json(OUT_DIR / "before_after_comparison.json", before_after)
    write_text(OUT_DIR / "rollback_report.md", render_report(payload))
    write_json(
        OUT_DIR / "manifest.json",
        {
            "run_id": OUT_DIR.name,
            "created_at": created_at,
            "artifacts": [
                "patch_proposal.json",
                "validation_gate.json",
                "rollback_decision.json",
                "before_after_comparison.json",
                "rollback_report.md",
            ],
            "boundary": payload["boundary"],
        },
    )
    print(json.dumps({"output_dir": str(OUT_DIR), "decision": rollback_decision["decision"], "accepted": validation_gate["accepted"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
