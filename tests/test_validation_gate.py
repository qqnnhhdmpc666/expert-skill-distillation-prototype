from skill_deployment.gate import evaluate_validation_gate


def test_validation_gate_accepts_valid_candidate() -> None:
    result = evaluate_validation_gate(
        selected_rule_ids={"R001", "R002"},
        required_rule_ids={"R001", "R002"},
        token_count=100,
        token_budget=120,
    )

    assert result.accepted is True
    assert result.decision == "accept"


def test_validation_gate_rejects_regression_before_acceptance() -> None:
    result = evaluate_validation_gate(
        selected_rule_ids={"R001", "R002"},
        required_rule_ids={"R001", "R002"},
        token_count=100,
        token_budget=120,
        regression_detected=True,
    )

    assert result.accepted is False
    assert result.decision == "reject_regression"


def test_validation_gate_rejects_over_budget() -> None:
    result = evaluate_validation_gate(
        selected_rule_ids={"R001", "R002"},
        required_rule_ids={"R001", "R002"},
        token_count=130,
        token_budget=120,
    )

    assert result.accepted is False
    assert result.decision == "reject_over_budget"

