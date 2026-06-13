from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src"
import sys

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from skill_deployment.repair import REPAIR_OPERATORS


OUT = ROOT / "outputs" / "validation"
REPORTS = ROOT / "reports"
POLICY_PATH = ROOT / "revision" / "repair_policy.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def load_policy() -> dict[str, str]:
    payload = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    actions = payload.get("repair_actions", {})
    return {str(key): str(value) for key, value in dict(actions).items()}


def main() -> int:
    policy = load_policy()
    operator_rows = []
    fallback_risks = []
    operator_by_action: dict[str, list[str]] = {}
    for operator in REPAIR_OPERATORS:
        operator_by_action.setdefault(operator.repair_action, []).append(operator.operator_id)

    for feedback_type, action in sorted(policy.items()):
        matched = [
            operator
            for operator in REPAIR_OPERATORS
            if feedback_type in operator.feedback_types and operator.repair_action == action
        ]
        covered_by_feedback_only = [
            operator
            for operator in REPAIR_OPERATORS
            if feedback_type in operator.feedback_types
        ]
        if matched:
            status = "aligned"
            note = "Policy action matches at least one typed operator."
        elif covered_by_feedback_only:
            status = "feedback_covered_action_mismatch"
            note = "Feedback type is covered, but the preferred action name differs from the operator repair_action."
            fallback_risks.append(feedback_type)
        elif action in operator_by_action:
            status = "action_exists_feedback_missing"
            note = "An operator with this action exists, but no operator currently declares this feedback type."
            fallback_risks.append(feedback_type)
        else:
            status = "unsupported"
            note = "No typed operator currently covers this feedback/action pair."
            fallback_risks.append(feedback_type)
        operator_rows.append(
            {
                "feedback_type": feedback_type,
                "preferred_action": action,
                "status": status,
                "matched_operator_ids": [operator.operator_id for operator in matched],
                "feedback_covered_operator_ids": [operator.operator_id for operator in covered_by_feedback_only],
                "note": note,
            }
        )

    payload = {
        "run_id": "repair_policy_alignment_001",
        "created_at": utc_now(),
        "policy_path": str(POLICY_PATH.relative_to(ROOT)).replace("\\", "/"),
        "operator_count": len(REPAIR_OPERATORS),
        "feedback_mapping_count": len(operator_rows),
        "rows": operator_rows,
        "fallback_risks": sorted(fallback_risks),
        "fully_aligned": not fallback_risks,
        "boundary": "This audit checks typed naming and coverage alignment, not whether the operator strategies are semantically optimal.",
    }
    write_json(OUT / "repair_policy_alignment.json", payload)
    write_text(
        REPORTS / "REPAIR_POLICY_OPERATOR_ALIGNMENT_STATUS.md",
        "\n".join(
            [
                "# Repair Policy / Operator Alignment Status",
                "",
                "## Result",
                "",
                f"- Feedback mappings: `{len(operator_rows)}`",
                f"- Typed operators: `{len(REPAIR_OPERATORS)}`",
                f"- Fully aligned: `{'YES' if payload['fully_aligned'] else 'NO'}`",
                f"- Fallback risk feedback types: `{', '.join(payload['fallback_risks']) or 'none'}`",
                "",
                "| Feedback Type | Preferred Action | Status | Matched Operators |",
                "|---|---|---|---|",
                *[
                    f"| {row['feedback_type']} | {row['preferred_action']} | {row['status']} | "
                    f"{', '.join(row['matched_operator_ids']) or 'none'} |"
                    for row in operator_rows
                ],
                "",
                "## What this means",
                "",
                "1. The repair policy and typed operator registry now use one consistent action vocabulary for the currently known feedback types.",
                "2. This reduces the chance of silent fallback behavior when a verifier emits a known feedback type.",
                "3. It does not prove the chosen operator is the best possible repair; it only proves the mapping is explicit and typed.",
                "",
                "## Boundary",
                "",
                "This is a naming-and-coverage audit. It is not a semantic optimality proof for the repair strategies themselves.",
                "",
            ]
        )
        + "\n",
    )
    print(json.dumps({"output": str(OUT / "repair_policy_alignment.json"), "fully_aligned": payload["fully_aligned"]}, ensure_ascii=False, indent=2))
    return 0 if payload["fully_aligned"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
