from __future__ import annotations

from expert_skill_system.evaluation.osv_benchmark import build_public_osv_cases, evaluate_predictions


def _record() -> dict:
    return {
        "id": "PYSEC-TEST-1",
        "affected": [
            {
                "package": {"name": "example", "ecosystem": "PyPI"},
                "ranges": [{"type": "ECOSYSTEM", "events": [{"introduced": "0"}, {"fixed": "2.0.0"}]}],
                "versions": ["1.0.0", "1.9.0"],
            }
        ],
    }


def test_generator_separates_public_input_from_gold() -> None:
    benchmark = build_public_osv_cases([_record()])
    assert len(benchmark.inputs) >= 8
    assert all("expected_verdict" not in item for item in benchmark.inputs)
    assert all("expected_reason" not in item for item in benchmark.inputs)
    assert {item["expected_verdict"] for item in benchmark.gold} >= {
        "advisory_applicable",
        "advisory_not_applicable",
        "unresolved",
    }
    assert {item["case_kind"] for item in benchmark.inputs} >= {
        "affected",
        "fixed_boundary",
        "marker_unknown_control",
        "unsupported_syntax_control",
        "conflicting_duplicate_pin_control",
    }


def test_evaluator_preserves_false_safe_and_missing_predictions() -> None:
    benchmark = build_public_osv_cases([_record()])
    affected = next(item for item in benchmark.inputs if item["case_kind"] == "affected")
    result = evaluate_predictions(
        list(benchmark.inputs),
        list(benchmark.gold),
        [
            {
                "case_id": affected["case_id"],
                "verdict": "advisory_not_applicable",
                "reason_codes": ["VERSION_OUT_OF_RANGE"],
            }
        ],
    )
    assert result["false_safe_count"] == 1
    assert result["missing_prediction_count"] == len(benchmark.inputs) - 1
    assert result["passed_count"] == 0
