from __future__ import annotations

from pathlib import Path

from scripts.compare_promotion_mechanisms import criteria_results
from scripts.run_artifact_backed_promotion_challenge_set import build_cases as build_artifact_backed_cases
from scripts.run_artifact_backed_promotion_challenge_set import evaluate as evaluate_artifact_backed
from scripts.run_promotion_mechanism_challenge_set import evaluate
from scripts.run_metamorphic_stress import build_cases
from skill_deployment.qualification import build_skill_qualification_cards


ROOT = Path(__file__).resolve().parents[1]


def test_qgse_scores_above_simple_promotion_baselines() -> None:
    cards = build_skill_qualification_cards(ROOT)["cards"]
    qgse = criteria_results("qgse_protocol", cards)
    reward = criteria_results("reward_delta_only", cards)
    gate = criteria_results("gate_only", cards)
    weighted = criteria_results("weighted_validity_score", cards)
    assert qgse["score"] > reward["score"]
    assert qgse["score"] > gate["score"]
    assert qgse["score"] > weighted["score"]


def test_minimal_metamorphic_stress_relations_hold() -> None:
    cases = build_cases()
    assert len(cases) == 4
    assert all(case["control_passed"] for case in cases)


def test_challenge_set_prefers_qgse_pareto_candidate() -> None:
    payload = evaluate()
    assert payload["best_on_challenge_set"] == "qgse_pareto_protocol"
    rows = {row["mechanism"]: row for row in payload["mechanisms"]}
    assert rows["qgse_pareto_protocol"]["false_promotion_count"] == 0
    assert rows["qgse_pareto_protocol"]["scope_error_count"] == 0
    assert rows["reward_delta_only"]["false_promotion_count"] > 0


def test_artifact_backed_challenge_set_keeps_scope_safe() -> None:
    rows = {row["mechanism"]: row for row in evaluate_artifact_backed(build_artifact_backed_cases())}
    assert rows["qgse_protocol"]["risk_score_lower_is_better"] == 0
    assert rows["qgse_pareto_protocol"]["risk_score_lower_is_better"] == 0
    assert rows["gate_only"]["false_promotion_count"] > 0
