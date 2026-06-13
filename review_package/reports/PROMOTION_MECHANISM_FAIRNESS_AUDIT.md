# Promotion Mechanism Fairness Audit

Question: Is the mechanism comparison fair, or did it use weak baselines?

- Same evidence bundle: `partially`
- Main risk: QGSE and QGSE-Pareto may appear stronger because the challenge fields were designed around failure-origin and scope discipline.
- Mitigation: Keep Pareto conservative and future vetoed-weighted-score as stronger baselines; expand to artifact-backed and human-labeled challenges.

| Mechanism | Role | Strawman risk | Verdict |
|---|---|---|---|
| reward_delta_only | intentionally weak baseline | medium | Keep only as a lower-bound baseline. |
| gate_only | ablation baseline for trusting the repair gate alone | medium | Keep only as a gate-ablation baseline. |
| weighted_validity_score | reasonable score-based baseline | low-medium | Add a future vetoed-weighted variant for a stronger baseline. |
| pareto_conservative | strong conservative baseline | low | Treat as the strongest current baseline, not a weak strawman. |
| qgse_protocol | current grounded-label best | n/a | Use as current default, with boundary. |
| qgse_pareto_protocol | next candidate mechanism | n/a | Advance as candidate, not final mechanism. |

## Next Actions

- Add vetoed_weighted_score baseline.
- Evaluate on artifact-backed challenge set.
- Add hidden/human usefulness labels before final mechanism claims.
