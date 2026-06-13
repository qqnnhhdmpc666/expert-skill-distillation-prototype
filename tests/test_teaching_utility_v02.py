from __future__ import annotations

from pathlib import Path

from skill_deployment.teaching_utility_v02 import (
    PilotCase,
    build_repeat_plans,
    evaluate_review,
    select_query_case,
    update_active_candidates,
)


def test_build_repeat_plans_rotates_roles() -> None:
    plans = build_repeat_plans(Path("."))
    assert len(plans) == 3
    assert plans[0].api_review.generation.case_id != plans[1].api_review.generation.case_id
    assert plans[0].config_security.hidden.case_id != plans[1].config_security.hidden.case_id
    assert len(plans[0].api_review.query_pool) == 2
    assert len(plans[0].config_security.query_pool) == 2


def test_evaluate_review_clean_control_requires_no_findings() -> None:
    case = PilotCase(
        case_id="clean_config",
        domain="config_security",
        visible_files=(("config.md", "debug: false"),),
        expected_rule_ids=(),
        negative_rule_ids=("C001", "C002", "C003", "C004", "C005", "C006"),
        critical_rule_ids=(),
        metadata={},
        source_dir=".",
    )
    clean = evaluate_review(case, {"findings": []})
    noisy = evaluate_review(
        case,
        {
            "findings": [
                {
                    "rule_id": "C004",
                    "issue": "debug enabled",
                    "severity": "high",
                    "evidence": "debug: false",
                    "config_path": "debug",
                }
            ]
        },
    )
    assert clean["pass_at_1"] is True
    assert noisy["pass_at_1"] is False
    assert noisy["false_positive_rule_ids"] == ["C004"]


def test_active_selection_returns_candidate_artifacts() -> None:
    query_cases = (
        PilotCase(
            case_id="api_query",
            domain="api_review",
            visible_files=(("case.md", "POST endpoint lacks idempotency and stable error codes."),),
            expected_rule_ids=("R003", "R006"),
            negative_rule_ids=(),
            critical_rule_ids=(),
            metadata={},
            source_dir=".",
        ),
        PilotCase(
            case_id="config_query",
            domain="config_security",
            visible_files=(("config.md", "payment_token: sk_live_demo_value\naudit:\n  enabled: false"),),
            expected_rule_ids=("C001", "C006"),
            negative_rule_ids=(),
            critical_rule_ids=(),
            metadata={},
            source_dir=".",
        ),
    )
    generation_cases = query_cases
    source_lessons = [
        {"domain": "api_review", "pass_at_1": True, "score": 0.8, "focus_rules": ["R001", "R002"]},
        {"domain": "config_security", "pass_at_1": False, "score": 0.2, "focus_rules": ["C001"]},
    ]
    selection = select_query_case(
        "active_discriminative_evidence",
        query_cases=query_cases,
        generation_cases=generation_cases,
        source_lessons=source_lessons,
        selected_query_lessons=[],
        seed=123,
    )
    assert selection["method"] == "active_discriminative_evidence"
    assert selection["selected_case_id"] in {"api_query", "config_query"}
    assert len(selection["candidates"]) == 4
    assert len(selection["disagreement_matrix"]) == 2


def test_active_candidate_updates_remove_clean_false_positive_rules() -> None:
    case = PilotCase(
        case_id="clean_api",
        domain="api_review",
        visible_files=(("case.md", "login required; authorization documented; token is redacted in the response."),),
        expected_rule_ids=(),
        negative_rule_ids=("R001", "R002", "R003", "R004", "R005", "R006"),
        critical_rule_ids=(),
        metadata={},
        source_dir=".",
    )
    candidates = [
        {
            "candidate_id": "h0",
            "focus_domain": "cross_domain",
            "allowed_rules": ["R001", "R004"],
            "status": "active",
            "weight": 1.0,
            "update_notes": [],
        }
    ]
    query_run = {
        "evaluation": {
            "seen_rule_ids": [],
        }
    }
    updated = update_active_candidates(candidates=candidates, case=case, query_run=query_run)
    assert updated[0]["status"] in {"downweighted", "eliminated"}
    assert "R001" not in updated[0]["allowed_rules"]
    assert "R004" not in updated[0]["allowed_rules"]
