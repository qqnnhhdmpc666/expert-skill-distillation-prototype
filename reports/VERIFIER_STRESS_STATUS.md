# Verifier Stress Status

## Result

- Checks: `3`
- Passed: `3/3`
- Overall: `PASS`

| Check | Purpose | Result | Feedback | Unsupported Evidence |
|---|---|---:|---|---|
| upload_live_llm_strict_target_match | A valid upload report should still pass when strict target-text evidence binding is enabled. | pass | pass | none |
| upload_report_against_swapped_data_quality_target | The same upload report should fail when evaluated against the wrong target asset. | pass | unsupported_evidence | UPLOAD_TYPE_MAGIC, UPLOAD_PATH_ISOLATION, UPLOAD_AUDIT_RETENTION |
| synthetic_bad_upload_evidence | A non-empty but non-matching evidence span should be rejected by the shared verifier when strict target binding is enabled. | pass | missing_capability | UPLOAD_TYPE_MAGIC |

## What improved

1. The shared verifier can now perform optional strict target-text evidence binding.
2. A valid upload report still passes against the correct target text.
3. The same report fails against a swapped non-security target, reducing the chance of accidental target/report mismatch passing silently.
4. A non-empty but fabricated evidence span is now caught by the shared verifier under strict mode.

## Boundary

This strengthens verifier credibility, but it is still substring-level evidence binding. It is not deep semantic grounding and is not yet enabled by default in every legacy artifact path.

