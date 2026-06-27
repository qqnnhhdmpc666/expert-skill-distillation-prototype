# Distillation Feedback Loop Comparison

## Summary

- baseline_bundle_digest: `sha256:76c52d01c3128cbbd33b58b9fab6e2dd38931a663c5b28ff6f26670a0c0d1fd0`
- revised_bundle_digest: `sha256:25ae1aae6af93ca15786948d65d81270ffa3eb693c19a8b0903e61ab45491a2c`
- baseline_pass_count: `1`
- revised_pass_count: `4`
- pass_count_delta: `3`
- unsupported_affected_decision_delta: `0`
- regression_count: `0`
- promotion_recommendation: `promote`

## Required Evidence

- baseline: `["dependency_declaration", "resolved_version", "import_use_site", "advisory_affected_range", "decision_evidence"]`
- revised: `["dependency_declaration", "resolved_version", "import_use_site", "advisory_affected_range", "decision_evidence"]`

This comparison is a bounded deterministic distillation-loop result. It does not prove compiler superiority or vulnerability discovery.
