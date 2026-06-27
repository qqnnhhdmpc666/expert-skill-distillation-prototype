# Distillation Feedback Loop Comparison

## Summary

- baseline_bundle_digest: `sha256:7d7b6cb8fa8eb7913140f80fd631f8dbb51ad2ae97fa6fd3c28db438bd2f11cc`
- revised_bundle_digest: `sha256:84e886640c688afe35ccdd2cf215e684ee726998bc93a5bb6fb110556c19b816`
- baseline_pass_count: `0`
- revised_pass_count: `4`
- pass_count_delta: `4`
- unsupported_affected_decision_delta: `-3`
- regression_count: `0`
- promotion_recommendation: `promote`

## Required Evidence

- baseline: `["dependency_declaration", "resolved_version", "advisory_affected_range", "decision_evidence"]`
- revised: `["dependency_declaration", "resolved_version", "import_use_site", "advisory_affected_range", "decision_evidence"]`

This comparison is a bounded deterministic distillation-loop result. It does not prove compiler superiority or vulnerability discovery.
