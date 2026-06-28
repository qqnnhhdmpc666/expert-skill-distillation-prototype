# Public Held-Out Evaluation v0 Effect Interpretation

- effect_observed: `not_evaluable_due_to_partial_lane`
- distillation_loop_v1_bundle_improves_pass_rate: `False`
- pass_rate_delta_count: `0`
- distillation_loop_v1_bundle_improves_evidence_completeness: `False`
- evidence_completeness_delta: `0.0`
- distillation_loop_v1_bundle_improves_abstention_correctness: `False`
- abstention_correctness_delta: `0.0`
- unsupported_affected_decision_delta: `0`
- mini_swe_agent_produced_schema_valid_verifier_artifacts: `False`
- any_condition_adds_overhead_without_benefit: `False`
- runtime_seconds_delta_bundle_minus_no_skill: `-0.053`

## Null or Negative Results

- mini_swe_agent rows are framework execution evidence only in v0; they do not produce schema-valid dependency-use predictions.
- SWE-bench rows are bounded smoke / contract evidence only; official harness performance is not claimed.
- repo lane remains `partial` because fewer than 3 A-tier distinct public repos are frozen.

## Next-Step Bridge

- Suitable for real LLM Agent evaluation: A-tier repo excerpts, starting with `dependency_use_triage_the_gan_zoo_public`.
- Suitable for dev/debug use: B/C/rejected candidates from the candidate search log after manual curation.
- Should remain frozen held-out: accepted A-tier excerpts in `public_heldout_v0/registry.json`.
- Closed-loop revision candidates: unsupported affected decisions, evidence completeness regressions, and abstention failures observed in future multi-excerpt runs.
- Additional public repos needed next: at least two more distinct A-tier Python repositories with pinned dependency, use-site or absent-use evidence, advisory binding, and clear license.
- SWE-bench next step: move from bounded smoke to `harness_executed` only after existing Docker/conda/harness environment is stable.
