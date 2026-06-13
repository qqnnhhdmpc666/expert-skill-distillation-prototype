# Academic Claim Readiness Assessment

Generated at: `2026-06-13T09:30:00+00:00`

Overall academic claim readiness: `moderate_high_with_caveat`

## Why not higher

The project now has stronger bounded evidence than a pure controlled-runtime prototype, including:

- bounded public-material open-world automatic distillation support
- bounded stable closed-loop improvement on top of that distilled Skill

But the rating remains capped because the current evidence is still bounded and local:

- no official external security benchmark result
- no official SWE-bench success
- live LLM effectiveness remains mixed outside the bounded closed-loop slice
- stable improvement is demonstrated on one bounded open-world line, not yet across broad task families

## Supported Claims

- Prototype-level Evidence-Grounded Skill Evolution Runtime.
- Controlled installed multi-capability secure_code_review validation.
- Local defensive representative mini-suite evidence with holdout and rerun checks.
- Non-oracle local semantic execution and effectiveness evidence are reported separately.
- Bounded public-material automatic distillation into an installable Skill package.
- Bounded stable closed-loop improvement on top of the open-world distilled Skill.
- QGSE-Pareto/marginal utility/task-conditioned activation/rejected-buffer mechanism as a coherent promotion-control story.

## Supported But Bounded

- `open_world_distillation`: supported only for bounded public-material validation, not arbitrary open-world materials.
- `stable_evolution_improvement`: supported only for the current bounded open-world closed-loop slice.
- `security_depth`: local bounded defensive-review evidence, not official benchmark evidence.

## Still Unsupported

- Production vulnerability scanning.
- Official CyberSecEval / AutoPatchBench / CVE-Bench claims.
- Broad real-world security validity.
- Full SPARK reproduction.
- SWE-bench software patch effectiveness while official harness remains infra-blocked.
- Universal autonomous Skill induction from arbitrary public materials.
- Broad stable autonomous evolution across arbitrary tasks.

## Highest-Value Next Evidence

- Add a second independent open-world failure family with a stable promoted candidate.
- Expand bounded open-world validation with more independent authoring while preserving leakage controls.
- Resolve official external harness infrastructure or add a separate official benchmark result.
- Strengthen clean-environment public-release reproducibility.
