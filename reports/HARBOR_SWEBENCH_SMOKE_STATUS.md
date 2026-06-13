# Harbor SWE-bench Smoke Status

- Source run: `swebench_lite_smoke_20260612`
- Status: `blocked_source_official_smoke_incomplete`
- Instances mirrored: `1`
- Variants requested: `empty_patch, gold_patch`

## Boundary

This bridge must not count plain Docker as Harbor. It only claims success after a Harbor launcher creates a task and captures verifier artifacts.

## Blocked Reason

SWE-bench official smoke has not completed for all requested variants.
