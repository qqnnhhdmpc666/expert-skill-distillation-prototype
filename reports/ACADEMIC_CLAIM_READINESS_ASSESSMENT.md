# Academic Claim Readiness Assessment

Generated at: `2026-06-13T16:10:00+00:00`

Overall academic claim readiness: `moderate_high_with_caveat`

## Why this is stronger than before

The project is no longer just a controlled runtime prototype. It now has two bounded lines that point directly at the core thesis:

- bounded public-material automatic distillation into an installable Skill
- bounded evidence-grounded Skill evolution with live-semantic candidate generation and repeated validation

## What is now supportable

- Prototype-level Evidence-Grounded Skill Evolution Runtime.
- Installed Skill runtime with real install / execute / compare / evidence / reject / rollback paths.
- Bounded public-material automatic distillation through a hybrid-semantic path with explicit fallback provenance.
- Bounded evolution improvement on top of that distilled Skill.
- A stronger repeatability line for one frozen evolved candidate:
  - `4 / 5` strict promotion proposals
  - positive mean paired delta `+0.0333`
  - no false-positive increase across that frozen-candidate validation run
- Honest preservation of a negative teaching-utility result.

## What is supported but still bounded

### `open_world_distillation`

Supported only on the current bounded public-material slice.

Most honest reading:

- a fresh run exceeded the baseline (`8 / 10` vs `7 / 10`)
- a later fresh rerun matched the baseline (`8 / 10` vs `8 / 10`)

So the claim is:

> bounded automatic distillation from public materials is supported,
> but stable strict superiority over the installed baseline is not yet universal.

### `stable_evolution_improvement`

Supported only on the current bounded hybrid-semantic closed-loop slice.

Most honest reading:

- one fresh generated-candidate run achieved `3 / 3`
- one frozen-candidate repeatability run achieved `4 / 5`
- mean gain stayed positive
- one repeat still regressed slightly

So the claim is:

> bounded evolution improvement is demonstrated,
> and repeatability is meaningfully stronger than before,
> but universal strict repeat-by-repeat stability is not yet established.

## Why the rating is not higher

The current evidence is still bounded and local:

- no official external security benchmark result
- no official SWE-bench success
- no broad real-world security validity claim
- no broad stable candidate-improvement story across multiple independent failure families

## Highest-value next evidence

1. Add a second independent open-world failure family with a frozen candidate that also shows positive repeated gain.
2. Keep public-material distillation bounded but expand the number of independently authored materials and failure families.
3. Resolve official external harness infrastructure or add one official benchmark result.
4. Strengthen clean-clone public release reproducibility.
