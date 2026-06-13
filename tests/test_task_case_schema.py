from pathlib import Path

from skill_deployment import LegacyHoldoutTaskCase, load_legacy_holdout_task_cases


def test_task_case_schema_loads_holdout_case() -> None:
    case = LegacyHoldoutTaskCase.from_directory(Path("data/api_review_holdout_cases/case003_auth_error_envelope"))

    assert case.case_id == "case003_auth_error_envelope"
    assert "R001" in case.expected_rule_ids
    assert "R006" in case.negative_rule_ids
    assert case.metadata["control_type"] == "mixed_rule"


def test_load_task_cases_loads_all_holdouts() -> None:
    cases = load_legacy_holdout_task_cases(Path("data/api_review_holdout_cases"))

    assert len(cases) >= 4
    assert {case.case_id for case in cases} >= {
        "case003_auth_error_envelope",
        "case006_clean_false_positive_control",
    }
