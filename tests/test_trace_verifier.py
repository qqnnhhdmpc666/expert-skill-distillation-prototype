from skill_deployment.trace import check_rule_application_trace


def test_trace_verifier_passes_for_traced_rule() -> None:
    review = {
        "findings": [{"id": "F1", "rule_id": "R005", "issue": "x", "severity": "medium", "evidence": "y"}],
        "rule_applications": [
            {
                "rule_id": "R005",
                "applicable": True,
                "trigger_condition_found": "missing request_id",
                "evidence_span": "response has code/message/data",
                "finding_id": "F1",
                "confidence": "medium",
            }
        ],
    }

    result = check_rule_application_trace(review, {"R005"})

    assert result.passed is True
    assert result.missing_trace_rule_ids == ()


def test_trace_verifier_fails_when_trace_missing() -> None:
    review = {
        "findings": [{"id": "F1", "rule_id": "R005", "issue": "x", "severity": "medium", "evidence": "y"}],
        "rule_applications": [],
    }

    result = check_rule_application_trace(review, {"R005"})

    assert result.passed is False
    assert result.missing_trace_rule_ids == ("R005",)

