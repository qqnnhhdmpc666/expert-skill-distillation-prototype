# Open-World Closed-Loop Status

Generated at: `2026-06-13T08:17:44.915678+00:00`

This run continues the bounded open-world story one step further: public-material distillation first, then a narrow auth-scope repair candidate generated from the remaining live failure pattern.

## Fresh Commands

```powershell
skill-deploy open-world-distill-validation --version v2 --backend live_llm_text --base-url https://api.deepseek.com --model deepseek-v4-flash
skill-deploy open-world-closed-loop --installed secure_code_review_open_world_distilled --repeats 3 --base-url https://api.deepseek.com --model deepseek-v4-flash
```

## Summary

- Base installed skill: `secure_code_review_open_world_distilled`
- Base version: `v2`
- Repeat count: `3`
- Promotion count: `3` / `3`
- Stable improvement: `pass`

## Repeat Decisions

| Repeat | Decision | Base score | Candidate score | Delta | FP delta | Positive regressions |
|---|---|---:|---:|---:|---:|---:|
| 1 | staged_promotion_proposal | 0.93 | 0.97 | 0.04 | 0 | 0 |
| 2 | staged_promotion_proposal | 0.93 | 0.97 | 0.04 | 0 | 0 |
| 3 | staged_promotion_proposal | 0.93 | 0.97 | 0.04 | 0 | 0 |

## Boundary

- This is bounded evidence for open-world distillation followed by one narrow evolution step.
- It is not proof of unrestricted autonomous search over arbitrary public materials.
- Unsupported dependency/version-risk remains unsupported.
