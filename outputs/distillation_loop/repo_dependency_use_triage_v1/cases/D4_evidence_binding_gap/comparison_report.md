# Distillation Feedback Loop Comparison

## Summary

- baseline_bundle_digest: `sha256:c7206312e35fbae03be5e4c3ea90c6323e4421ba757b611b744af99b631adf8b`
- revised_bundle_digest: `sha256:9fe97d3e39b8b17067908d3ae564b4cd6c223d4eb6b47af339c0e212b9a5d66a`
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
