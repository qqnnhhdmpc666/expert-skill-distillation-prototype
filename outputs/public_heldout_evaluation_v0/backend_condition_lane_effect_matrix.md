# Public Held-Out Backend Condition Lane Effect Matrix

| lane | backend | condition | status | task_count | executed | pass | fail | not_counted | claim_counted | note |
|---|---|---|---|---:|---:|---:|---:|---:|---|---|
| `repo_level_dependency_use` | `deterministic_reference` | `no_skill` | `executed` | 1 | 1 | 1 | 0 | 0 | `True` | deterministic verifier counted |
| `repo_level_dependency_use` | `deterministic_reference` | `distillation_loop_v1_bundle` | `executed` | 1 | 1 | 1 | 0 | 0 | `True` | deterministic verifier counted |
| `repo_level_dependency_use` | `mini_swe_agent` | `no_skill` | `executed` | 1 | 1 | 0 | 0 | 1 | `False` | mini_swe_agent framework smoke; output is not schema-valid prediction |
| `repo_level_dependency_use` | `mini_swe_agent` | `distillation_loop_v1_bundle` | `executed` | 1 | 1 | 0 | 0 | 1 | `False` | mini_swe_agent framework smoke; output is not schema-valid prediction |
| `swe_bench_micro` | `deterministic_reference` | `no_skill` | `blocked` | 1 | 0 | 0 | 0 | 1 | `False` | SWE-bench compatibility probe only; official harness performance not claimed |
| `swe_bench_micro` | `deterministic_reference` | `distillation_loop_v1_bundle` | `blocked` | 1 | 0 | 0 | 0 | 1 | `False` | SWE-bench compatibility probe only; official harness performance not claimed |
| `swe_bench_micro` | `mini_swe_agent` | `no_skill` | `blocked` | 1 | 0 | 0 | 0 | 1 | `False` | SWE-bench compatibility probe only; official harness performance not claimed |
| `swe_bench_micro` | `mini_swe_agent` | `distillation_loop_v1_bundle` | `blocked` | 1 | 0 | 0 | 0 | 1 | `False` | SWE-bench compatibility probe only; official harness performance not claimed |
