import json
from pathlib import Path

from skill_deployment.repair import REPAIR_OPERATORS


ROOT = Path(__file__).resolve().parents[1]


def test_repair_policy_actions_have_typed_operator_support() -> None:
    policy = json.loads((ROOT / "revision" / "repair_policy.json").read_text(encoding="utf-8"))["repair_actions"]

    for feedback_type, action in policy.items():
        assert any(
            feedback_type in operator.feedback_types and operator.repair_action == action
            for operator in REPAIR_OPERATORS
        ), f"{feedback_type} -> {action} is not covered by a typed operator"
