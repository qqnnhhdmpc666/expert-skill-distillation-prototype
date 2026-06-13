# Software Patch Review Installed Runtime v1

This installed runtime is bounded to software patch review and external SWE-bench smoke plumbing.

## Capability Groups

### software_patch_review
- task_families: `software_patch_review`
- capabilities:
  - `PATCH_TEST_FAILURE_REPRO`
  - `PATCH_MINIMAL_CODE_CHANGE`
  - `PATCH_REGRESSION_VALIDATION`

### out_of_scope_guard
- task_families: `none`
- capabilities:
  - none

## Output Contract

- `capability_id`
- `evidence_span`
- `recommended_fix`
