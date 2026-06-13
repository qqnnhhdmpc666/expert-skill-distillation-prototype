# Skill Revision Validity Metrics

## Why one score is not enough

The current project should not compress “skill got better” into one scalar. The safer path is a multi-axis validity view.

## Proposed validity dimensions

1. `outcome_delta`
   - did A2 improve task outcome relative to A1?
2. `evidence_grounding`
   - are findings tied to real target observations rather than empty or unsupported spans?
3. `repair_attribution`
   - does A2 improve in the dimension that A1 feedback actually pointed to?
4. `regression_safety`
   - did the repair avoid introducing new false positives or contract breakage?
5. `transferability`
   - does the same repair-and-gate skeleton span multiple task families?
6. `repeatability`
   - does the result hold across reruns, especially on live LLM / Harbor paths?
7. `cost_budget`
   - is the improvement affordable in runtime, token, or trace budget terms?
8. `verifier_robustness`
   - can the verifier reject unsupported evidence and obvious shortcuts?
9. `human_plausibility`
   - would a human judge A2 as meaningfully better and more actionable?

## Status vocabulary

- `supported`
- `partially_supported`
- `not_measured`
- `manual_review_pending`

## Current implementation

The first minimal implementation now exists at:

- `outputs/validation/skill_revision_validity_cards.json`
- `reports/SKILL_REVISION_VALIDITY_CARD_STATUS.md`

## How this differs from related-work-style single diagnostics

This project should avoid pretending it already has a SPARK-scale posterior metric like PDI/PDR. The more honest move is:

> treat revision validity as a card with multiple evidence axes, some strong, some partial, and some still missing.

That framing matches the actual maturity of the system much better.

## Current strongest axes

1. controlled `outcome_delta`
2. typed `repair_attribution`
3. narrow `regression_safety`
4. narrow `verifier_robustness`
5. upload-loop `repeatability`

## Current weakest axes

1. `human_plausibility`
2. broader `transferability` on Harbor/live LLM
3. broad semantic `evidence_grounding`
4. calibrated `cost_budget`

## Recommendation

Keep using the validity-card format for every future major result rather than adding another single “overall score” that would overclaim certainty.
