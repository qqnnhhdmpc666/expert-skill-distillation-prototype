from __future__ import annotations

from pathlib import Path

from skill_deployment.qualification import build_skill_qualification_cards


ROOT = Path(__file__).resolve().parents[1]


def cards_by_id() -> dict[str, dict]:
    payload = build_skill_qualification_cards(ROOT)
    return {card["card_id"]: card for card in payload["cards"]}


def test_successful_harbor_upload_promotes_only_to_sandboxed_scope() -> None:
    cards = cards_by_id()
    card = cards["harbor_llm_upload_repair_loop"]
    assert card["card_type"] == "RevisionQualificationCard"
    assert card["qualification_decision"] == "promote_with_scope_limit"
    assert card["promotion_level"] == "L4_PROMOTE_SANDBOXED_WITH_SCOPE_LIMIT"
    assert "controlled" in card["claim_scope"].lower()
    assert card["gates"]["integrity_gate"]["status"] == "pass"
    assert card["gates"]["behavior_gate"]["status"] == "pass"


def test_local_config_failure_is_quarantined_not_promoted() -> None:
    cards = cards_by_id()
    card = cards["live_llm_config_security_repair_loop"]
    assert card["qualification_decision"] == "quarantine"
    assert card["promotion_level"] == "L0_NON_PROMOTABLE"
    assert card["gates"]["behavior_gate"]["failure_origin"] == "skill_to_execution_gap"


def test_api_noop_repair_is_rejected_by_integrity_gate() -> None:
    cards = cards_by_id()
    card = cards["live_llm_api_review_repair_loop"]
    assert card["qualification_decision"] == "reject"
    assert card["promotion_level"] == "L0_NON_PROMOTABLE"
    assert card["gates"]["integrity_gate"]["status"] == "fail"
    assert card["gates"]["integrity_gate"]["failure_origin"] == "repair_operator_noop_or_patch_application_failure"


def test_support_cards_are_not_revision_promotion_cards() -> None:
    cards = cards_by_id()
    card = cards["negative_control_robustness_support"]
    assert card["card_type"] == "EvidenceSupportCard"
    assert "promotion_level" not in card
    assert card["support_level"].startswith("supports_")
