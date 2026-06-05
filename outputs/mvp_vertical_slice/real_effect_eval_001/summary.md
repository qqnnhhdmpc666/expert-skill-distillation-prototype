# Real Effect Evaluation 001

## Positioning

Small controlled holdout set for checking whether skill-conditioned deployment improves API-review behavior.

| Variant | Avg Coverage | Pass@1 | Critical Misses | False Positives | Avg Total Tokens |
|---|---:|---:|---:|---:|---:|
| no_skill | 0.25 | 1 / 4 | 5 | 0 | 4.0 |
| full_skill | 1.00 | 4 / 4 | 0 | 0 | 1429.8 |
| compact_v1 | 0.58 | 1 / 4 | 1 | 0 | 323.5 |
| patched_compact | 1.00 | 4 / 4 | 0 | 0 | 438.8 |
| patched_compact_selective_trace | 1.00 | 4 / 4 | 0 | 0 | 335.0 |

## Conservative Conclusion

- Status: partially_supported
- Finding: Small holdout evidence suggests patched compact skill improves controlled API-review behavior over compact_v1.
- Boundary: Controlled 4-case holdout only. This is not a benchmark and does not prove general real-world correctness.
