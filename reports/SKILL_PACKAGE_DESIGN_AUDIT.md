# Skill Package Design Audit

## Verdict

The current Skill Package design is **good enough for controlled deployment experiments** and already better than a single prompt string, but it is still a **thin package contract**, not yet a mature installable skill system.

## What the current package gets right

1. It separates reusable skill state from per-run artifacts.
2. It carries a task family, capability set, output contract, and trace contract.
3. It is serializable as a manifest plus `SKILL.md`.
4. It supports revision from `v1` to `v2` with artifact-backed diffing and gate decisions.
5. It is already shared across offline, local heuristic, live LLM, and Harbor slices.

## Current concrete representations

In code:

- `src/skill_deployment/schemas.py::SkillPackage`

In artifacts:

- `manifest.json`
- `SKILL.md`
- Harbor slices sometimes emit `skill_manifest.json`

This is already enough to support:

- A1/A2 capability deltas
- prompt construction for agents
- verifier-aligned output fields
- review-package inspection

## Current weaknesses

### 1. Package surface is still capability-centric

The package mostly says:

- which capabilities exist
- which output fields are required
- which trace fields matter

It does **not yet cleanly encode**:

- richer observation procedures
- failure-specific evidence policies
- multi-file target traversal plans
- backend-specific execution affordances
- tool requirements

### 2. Contract naming is not perfectly uniform

Some paths use:

- `manifest.json`

others use:

- `skill_manifest.json`

This is survivable, but it creates avoidable friction for a supposed package abstraction.

### 3. Output contract is embedded but not fully first-class

The package stores `output_contract`, but most real enforcement still lives in verifier code and slice-specific logic. That means the package describes the contract, but does not yet own it.

### 4. Cross-domain support is promising but still shallow

The package format now spans:

- upload security
- auth access control
- config security
- API/code review
- data quality review

That is a good sign. But the actual package semantics are still narrow enough that a harder non-security domain would probably require more explicit procedure fields.

## Comparison to “single prompt” baselines

This package is meaningfully better than a single prompt because it supports:

- versioning
- inspectability
- revision attribution
- structured verifier interfaces
- backend portability

But it is still much lighter than a product-grade skill system like:

- installable multi-file skill packages
- executable tool manifests
- environment dependency declarations
- compatibility and migration rules

## Safe claim

Safe:

> The project has a deployable, inspectable Skill Package abstraction that is strong enough for controlled posterior revision experiments.

Unsafe:

> The Skill Package implementation is already a mature general-purpose skill operating system.

## Strongest supporting artifacts

- `runs/generalization/*/skills/skill_v1/manifest.json`
- `runs/generalization/*/skills/skill_v2/manifest.json`
- `outputs/harbor_llm_repair_loop_upload_001/A1/skill_manifest.json`
- `outputs/harbor_llm_repair_loop_upload_001/A2/skill_manifest.json`
- `outputs/harbor_llm_repair_loop_config_001/A1/skill_manifest.json`
- `outputs/harbor_llm_repair_loop_config_001/A2/skill_manifest.json`

## Design gaps to close

1. unify manifest naming across all backends
2. move output contract and trace contract validation into shared modules
3. optionally add explicit `observation_steps`, `evidence_policy`, and `backend_hints`
4. document one canonical Skill Package schema in code and docs together
5. add schema tests against current artifact directories

## Bottom line

The Skill Package is **not copied boilerplate** and **not just a prompt wrapper**. It is a real internal abstraction. The main issue is not originality; it is that the abstraction still needs one more round of schema hardening before it can be called mature.
