# Evolution Improvement Repeatability Status

Generated at: `2026-06-13T07:48:53.054713+00:00`

This run measures whether previously promoted live-feedback candidate proposals remain promotable across fresh reruns.

## Fresh Command

```powershell
skill-deploy evolution-repeatability --installed secure_code_review --repeats 3 --base-url https://api.deepseek.com --model deepseek-v4-flash
```

## Summary

- Candidate count: `2`
- Repeat count: `3`
- Stable promotion candidates: `none`
- `stable_evolution_improvement`: `partial`

## Candidate Repeatability

| Candidate | Promotions / repeats | Stable | Mean delta | Worst delta | Any FP regression | Any scope violation |
|---|---:|---:|---:|---:|---:|---:|
| c003_auth | 2/3 | False | 0.0528 | 0.0167 | False | False |
| c006_combo | 2/3 | False | 0.0236 | -0.0708 | False | False |

## Boundary

- This is repeatability of fixed candidate proposals under fresh live reruns.
- It is stronger than a single proposal artifact, but it is not proof of universal autonomous-search stability.
- No candidate was auto-installed during this run.
