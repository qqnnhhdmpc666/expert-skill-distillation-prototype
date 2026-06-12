# Live Mechanism Ablation Status

Generated at: `2026-06-12T18:19:12.016139+00:00`

This ablation compares the active contract-grounded runtime against bounded live variants. It is local live evidence, not an official benchmark. The full local report includes per-case rows under `outputs/mechanism_ablation/live_contract/`.

## Summary

- Cases: `7`
- Variants: `active_contract_system, no_evidence_normalizer, no_out_of_scope_guard, all_capabilities_always_on, no_task_router, simple_prompt_baseline`
- `mechanism_ablation`: `supports_mechanism`

## Variant Metrics

| Variant | Completed | Pass | FP | Scope violations | Unsupported evidence | Schema errors | Avg score |
|---|---:|---:|---:|---:|---:|---:|---:|
| active_contract_system | 7 | 3 | 0 | 0 | 0 | 0 | 0.8381 |
| no_evidence_normalizer | 7 | 3 | 0 | 0 | 0 | 0 | 0.8238 |
| no_out_of_scope_guard | 7 | 6 | 0 | 2 | 0 | 0 | 0.9571 |
| all_capabilities_always_on | 7 | 3 | 0 | 7 | 0 | 0 | 0.8238 |
| no_task_router | 7 | 3 | 0 | 5 | 0 | 0 | 0.7714 |
| simple_prompt_baseline | 7 | 4 | 0 | 7 | 0 | 0 | 0.8619 |

## Interpretation

The active contract system is not claimed to maximize raw pass count. The support comes from scope discipline: the active system has zero false positives, zero unsupported evidence, zero schema errors, and zero scope violations, while several ablated variants improve raw pass count only by violating task scope or disabling the guardrail boundary.

## Boundary

- Verifier logic was not relaxed.
- This is bounded local live evidence, not an official benchmark.
- The correct claim is `supports_mechanism`, not universal dominance over every metric.
