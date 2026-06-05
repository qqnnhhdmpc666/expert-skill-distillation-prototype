# Direct Summary Miss Analysis 001

## Purpose

Explain the only failed direct-summary holdout case and what it means for the core claim.

- failed_case_id: case004_validation_sensitive_idempotency
- missed_rule_ids: R006
- direct_summary_available_rule_ids: R001, R002, R003, R004, R005

## Missed Rule Analysis

### R006: idempotency

- failure_critical: True
- priority: medium
- long_tail: True
- salience: lower_than_auth_validation_error_sensitive_data
- requires_execution_feedback: True
- why_missed: The direct summary covers common API concerns but omits explicit idempotency / duplicate submission behavior.

## Patch Recovery

patched_compact includes R006 explicitly, so the mock case-aware agent emits the idempotency finding and the verifier marks the failed case as pass.

## Meaning For Core Claim

Direct summary is not weak: it covers most salient rules. Its only miss is R006, a medium-priority but deployment-critical idempotency/duplicate-submission rule that compact_v1 also missed. This supports the narrow claim that deployment feedback is useful for recovering residual failure-critical rules.

## Boundary

One failed case is explanatory, not statistical. More holdout cases are needed before claiming a general long-tail failure pattern.
