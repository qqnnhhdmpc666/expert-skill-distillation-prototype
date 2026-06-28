# Backend Condition Lane Matrix

| backend | condition | lane | execution_status | task_count | pass_count | fail_count | not_counted_count | bundle_injected | trajectory_available | verifier_available | claim_counted |
|---|---|---|---|---:|---:|---:|---:|---|---|---|---|
| `deterministic_reference` | `no_skill` | `repo_level_dependency_use` | `executed` | 1 | 1 | 0 | 0 | `False` | `True` | `True` | `True` |
| `deterministic_reference` | `distillation_loop_v1_bundle` | `repo_level_dependency_use` | `executed` | 1 | 1 | 0 | 0 | `True` | `True` | `True` | `True` |
| `real_agent` | `no_skill` | `repo_level_dependency_use` | `executed` | 1 | 1 | 0 | 0 | `False` | `True` | `True` | `True` |
| `real_agent` | `distillation_loop_v1_bundle` | `repo_level_dependency_use` | `executed` | 1 | 1 | 0 | 0 | `True` | `True` | `True` | `True` |
| `deterministic_reference` | `no_skill` | `swe_bench_compatibility` | `dry_run` | 1 | 0 | 0 | 1 | `False` | `True` | `True` | `False` |
| `deterministic_reference` | `distillation_loop_v1_bundle` | `swe_bench_compatibility` | `dry_run` | 1 | 0 | 0 | 1 | `True` | `True` | `True` | `False` |
| `real_agent` | `no_skill` | `swe_bench_compatibility` | `executed` | 1 | 1 | 0 | 0 | `False` | `True` | `True` | `True` |
| `real_agent` | `distillation_loop_v1_bundle` | `swe_bench_compatibility` | `executed` | 1 | 1 | 0 | 0 | `True` | `True` | `True` | `True` |
