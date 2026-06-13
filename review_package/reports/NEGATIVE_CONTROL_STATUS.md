# Negative Control Status

## Result

- Cases: `2`
- Controls passed: `2/2`
- Overall: `PASS`

| Case | Expected | Control Passed | Key Feedback |
|---|---|---:|---|
| upload_security_negative | fail | True | unsupported_evidence |
| config_security_false_positive_control | always_append_fail_typed_empty_pass | True | false_positive_risk |

## Required Questions

- Does the system mis-PASS no-evidence issues? No. The upload negative control is rejected as unsupported evidence.
- Can the verifier reject unsupported findings? Yes. It checks that `evidence_span` is present in the target text.
- Can the gate block false positive / regression? In this controlled check, the append-style config output is rejected and the empty typed output is accepted only because the expected issue set is empty.

## Boundary

These controls are small deterministic checks. They improve confidence that the verifier can reject unsupported evidence and false positives, but they are not a broad adversarial benchmark.
