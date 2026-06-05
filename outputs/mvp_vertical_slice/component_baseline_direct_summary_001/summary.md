# Component Baseline Direct Summary 001

## Purpose

Compare a plain direct-summary skill against existing structured skill variants on the controlled API-review holdout.

This is a component attribution slice, not a benchmark.

| Variant | Avg Coverage | Pass@1 | Critical Misses | False Positives | Avg Total Tokens |
|---|---:|---:|---:|---:|---:|
| direct_summary_skill | 0.92 | 3 / 4 | 0 | 0 | 263.0 |
| full_skill | 1.00 | 4 / 4 | 0 | 0 | 1429.8 |
| compact_v1 | 0.58 | 1 / 4 | 1 | 0 | 323.5 |
| patched_compact | 1.00 | 4 / 4 | 0 | 0 | 438.8 |
| patched_compact_selective_trace | 1.00 | 4 / 4 | 0 | 0 | 335.0 |

## Interpretation

- Status: partially_supported
- Finding: Structured patch loop improves over direct summarization in this controlled slice by recovering a missed long-tail/failure-critical rule.
- Boundary: Controlled 4-case attribution slice only. This is not a benchmark and does not prove broad superiority over direct summarization.
