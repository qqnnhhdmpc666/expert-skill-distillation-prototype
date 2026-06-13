# Algorithm Gap And Next Steps

## Current algorithmic identity

The strongest current algorithmic identity is:

> typed posterior revision over deployable Skill Packages under deterministic verifier and gate constraints.

That is already a real idea. It is narrower than SPARK-style trajectory verification and narrower than a general skill platform, but it is not just UI or glue code either.

## Main algorithmic gaps

### 1. Posterior signal is still small-taxonomy

Current feedback types are useful, but still limited. Real systems will need richer states such as:

- ambiguous requirement
- conflicting expert materials
- insufficient target context
- infeasible repair
- budget-exceeded repair
- verifier uncertainty

### 2. Repair is typed, but still mostly capability-closure oriented

The current repair operators are strongest when the missing piece is:

- add a capability
- tighten output contract
- reduce false positives
- add observation step

They are weaker when the true fix is:

- restructure the observation order
- change evidence policy
- revise tool use
- refuse execution
- ask for more context

### 3. Verifier semantics are too shallow for strong claims

The verifier currently protects against several important failure modes, but still reasons at a fairly shallow structured-output level.

### 4. Harbor/live LLM evidence is still narrow

The Harbor LLM path is the most important realism upgrade so far, but it still covers only a tiny controlled task set.

## Highest-value next algorithm moves

1. **uncertainty-aware repair and gate**
   - add `manual_review_required`, `need_more_context`, and `infeasible`
2. **observation-policy repair**
   - let repairs modify ordered observation plans, not only capability membership
3. **semantic evidence auditing**
   - add target-span verification stronger than keyword presence
4. **human-backed A1/A2 delta audit**
   - small manual ratings for usefulness and actionability
5. **second non-security live-LLM family**
   - prove the method is not trapped inside security-only task design

## What not to do next

1. do not add more UI first
2. do not add more demo tabs first
3. do not inflate task count with near-duplicates
4. do not claim open-world autonomy from current Harbor slices

## Best next scoped contribution

If the project keeps moving, the cleanest next scientific step is:

> show that typed posterior revision can choose among capability repair, output-contract repair, observation repair, rollback, and abstention under controlled evidence and cost constraints.

That would be a stronger and more original systems-method statement than just “we also have another backend.”
