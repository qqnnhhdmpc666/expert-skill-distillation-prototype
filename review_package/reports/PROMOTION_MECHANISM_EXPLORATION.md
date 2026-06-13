# Promotion Mechanism Exploration

This report keeps the Skill-upgrade decision mechanism open to alternatives. QGSE is treated as the current best protocol, not as an unchangeable assumption.

Best current mechanism: `qgse_protocol`

| Mechanism | Score | Recommendation | Main failure mode |
|---|---:|---|---|
| reward_delta_only | 2 | candidate_or_baseline | Cannot distinguish lucky pass, repair attribution, no-op repair, or scoped promotion evidence. |
| gate_only | 1 | candidate_or_baseline | Promotes accepted patches even when A2 behavior does not improve. |
| weighted_validity_score | 2 | candidate_or_baseline | Compresses hard blockers into a score and can hide why a revision is non-promotable. |
| pareto_conservative | 5 | candidate_or_baseline | Useful as a baseline, but does not model evidence support cards or promotion scopes as explicitly as QGSE. |
| qgse_protocol | 6 | best_current | Current best mechanism, but still needs stronger metamorphic and human-review evidence. |

## Criteria

### reward_delta_only

- matches_current_grounded_labels: `False`
- does_not_promote_support_cards: `True`
- rejects_api_noop_repair: `True`
- quarantines_config_behavior_gap: `False`
- keeps_promotion_scope_explicit: `False`
- can_explain_failure_origin: `False`

### gate_only

- matches_current_grounded_labels: `False`
- does_not_promote_support_cards: `True`
- rejects_api_noop_repair: `False`
- quarantines_config_behavior_gap: `False`
- keeps_promotion_scope_explicit: `False`
- can_explain_failure_origin: `False`

### weighted_validity_score

- matches_current_grounded_labels: `False`
- does_not_promote_support_cards: `True`
- rejects_api_noop_repair: `True`
- quarantines_config_behavior_gap: `False`
- keeps_promotion_scope_explicit: `False`
- can_explain_failure_origin: `False`

### pareto_conservative

- matches_current_grounded_labels: `True`
- does_not_promote_support_cards: `True`
- rejects_api_noop_repair: `True`
- quarantines_config_behavior_gap: `True`
- keeps_promotion_scope_explicit: `False`
- can_explain_failure_origin: `True`

### qgse_protocol

- matches_current_grounded_labels: `True`
- does_not_promote_support_cards: `True`
- rejects_api_noop_repair: `True`
- quarantines_config_behavior_gap: `True`
- keeps_promotion_scope_explicit: `True`
- can_explain_failure_origin: `True`

## Current Conclusion

The best current mechanism is QGSE because it preserves hard blockers, separates revision qualification from supporting evidence, forces claim scope, and records failure origin. It should remain replaceable: future mechanisms can win if they better predict human usefulness, held-out task transfer, and metamorphic robustness without hiding failures.
