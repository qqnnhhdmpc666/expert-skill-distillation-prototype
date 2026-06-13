from skill_deployment import ExecutionReport, verify_controlled_execution


def test_verify_controlled_execution_detects_output_contract_error() -> None:
    report = verify_controlled_execution(
        ("API_SCHEMA_CONTRACT",),
        ExecutionReport(
            attempt="A1",
            backend="offline_deterministic",
            findings=(
                {
                    "capability_id": "API_SCHEMA_CONTRACT",
                    "issue": "Strict report schema",
                    "evidence_span": "agent output omits evidence_span or uses free-form prose",
                    "recommended_fix": "",
                },
            ),
        ),
    )

    assert report.passed is False
    assert report.feedback_type == "output_contract_error"
    assert report.schema_errors == ("API_SCHEMA_CONTRACT.recommended_fix",)


def test_verify_controlled_execution_honors_weak_evidence_override() -> None:
    report = verify_controlled_execution(
        ("DATA_TEMPORAL_SPLIT_GUARD",),
        {"findings": [{"capability_id": "DATA_TEMPORAL_SPLIT_GUARD", "issue": "Temporal split guard", "evidence_span": "", "recommended_fix": "quote offending row ids"}]},
        feedback_overrides={"weak_evidence": "target_context_missing"},
    )

    assert report.passed is False
    assert report.feedback_type == "target_context_missing"
    assert report.weak_evidence_capabilities == ("DATA_TEMPORAL_SPLIT_GUARD",)


def test_verify_controlled_execution_detects_unsupported_evidence_when_target_text_is_provided() -> None:
    report = verify_controlled_execution(
        ("UPLOAD_TYPE_MAGIC",),
        {
            "findings": [
                {
                    "capability_id": "UPLOAD_TYPE_MAGIC",
                    "issue": "Upload type validation",
                    "evidence_span": "filename.endswith without MIME validation",
                    "recommended_fix": "Validate MIME and magic bytes.",
                }
            ]
        },
        target_text="app.py: upload() checks content_type only.",
    )

    assert report.passed is False
    assert report.feedback_type == "unsupported_evidence"
    assert report.unsupported_evidence_capabilities == ("UPLOAD_TYPE_MAGIC",)


def test_verify_controlled_execution_keeps_legacy_behavior_without_target_text() -> None:
    report = verify_controlled_execution(
        ("UPLOAD_TYPE_MAGIC",),
        {
            "findings": [
                {
                    "capability_id": "UPLOAD_TYPE_MAGIC",
                    "issue": "Upload type validation",
                    "evidence_span": "filename.endswith without MIME validation",
                    "recommended_fix": "Validate MIME and magic bytes.",
                }
            ]
        },
    )

    assert report.passed is True
    assert report.feedback_type == "pass"
