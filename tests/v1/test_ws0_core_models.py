from __future__ import annotations

import pytest

from expert_skill_system.core.models import DomainDecision, DomainOutcome, ExecutionEnvelope, FailureDetail

BUNDLE = "sha256:" + "a" * 64


def test_execution_envelope_roundtrip_distinguishes_completed_and_failure() -> None:
    outcome = DomainOutcome(
        decision=DomainDecision(
            dependency_name="requests",
            normalized_name="requests",
            resolved_version="2.19.0",
            advisory_id="PYSEC-2018-28",
            verdict="advisory_applicable",
            reason_codes=("VERSION_IN_RANGE",),
        )
    )
    completed = ExecutionEnvelope(domain_outcome=outcome, session_id="s1", bundle_digest=BUNDLE)
    assert ExecutionEnvelope.from_dict(completed.to_dict()) == completed

    failed = ExecutionEnvelope(
        execution_status="runtime_failure",
        failure=FailureDetail(category="bundle_corrupt", reason_codes=("CLOSURE_MISMATCH",)),
        session_id="s2",
        bundle_digest=BUNDLE,
    )
    assert ExecutionEnvelope.from_dict(failed.to_dict()) == failed


def test_strict_models_reject_unknown_fields_and_invalid_state() -> None:
    with pytest.raises(ValueError, match="unknown fields"):
        ExecutionEnvelope.from_dict(
            {
                "schema_version": "execution_envelope.v1",
                "execution_status": "completed",
                "domain_outcome": None,
                "failure": None,
                "session_id": "s1",
                "bundle_digest": BUNDLE,
                "surprise": True,
            }
        )
    with pytest.raises(ValueError, match="completed execution"):
        ExecutionEnvelope(session_id="s1", bundle_digest=BUNDLE)

