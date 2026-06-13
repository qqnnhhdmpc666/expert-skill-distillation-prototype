# Open-World Closed-Loop Status

Generated at: `2026-06-13T16:08:42.389947+00:00`

This run continues the bounded open-world story one step further: public-material distillation first, then a narrow structured repair candidate generated from the remaining live failure pattern.

## Fresh Commands

```powershell
skill-deploy open-world-distill-validation --skill-id secure_code_review_open_world_hybrid_distilled --version v1 --backend live_llm_text --base-url https://api.deepseek.com --model deepseek-v4-flash --projection-mode hybrid_semantic
skill-deploy open-world-closed-loop --installed secure_code_review_open_world_hybrid_distilled --repeats 5 --base-url https://api.deepseek.com --model deepseek-v4-flash --candidate-mode reused_candidate --reuse-candidate-dir C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\open_world_closed_loop\frozen_candidate_config_guard_v1
```

## Summary

- Base installed skill: `secure_code_review_open_world_hybrid_distilled`
- Base version: `v1`
- Repeat count: `5`
- Candidate mode: `reused_candidate`
- Candidate dir: `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\open_world_closed_loop\frozen_candidate_config_guard_v1`
- Promotion count: `4` / `5`
- Stable improvement: `partial`
- Base mean score: `0.9167`
- Candidate mean score: `0.95`
- Mean score delta: `0.0333`
- Strict positive repeats: `4` / `5`

## Repeat Decisions

| Repeat | Decision | Base score | Candidate score | Delta | FP delta | Positive regressions |
|---|---|---:|---:|---:|---:|---:|
| 1 | staged_promotion_proposal | 0.93 | 0.97 | 0.04 | 0 | 0 |
| 2 | not_promoted | 0.89 | 0.87 | -0.02 | 0 | 1 |
| 3 | staged_promotion_proposal | 0.93 | 0.97 | 0.04 | 0 | 0 |
| 4 | staged_promotion_proposal | 0.93 | 0.97 | 0.04 | 0 | 0 |
| 5 | staged_promotion_proposal | 0.9033 | 0.97 | 0.0667 | 0 | 0 |

## Interpretation

- `staged_promotion_proposal` means the candidate beat the active installed skill on that repeat under the strict gate.
- `reused_candidate` means the validation froze one previously generated candidate and reran it, instead of regenerating a new candidate each time.
- Positive mean delta is supportive bounded evidence even when one repeat remains tied or negative; it is not the same as universal strict stability.

## Boundary

- This is bounded evidence for open-world distillation followed by one narrow evolution step.
- It is not proof of unrestricted autonomous search over arbitrary public materials.
- Unsupported dependency/version-risk remains unsupported.
