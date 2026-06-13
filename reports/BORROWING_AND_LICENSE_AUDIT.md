# Borrowing And License Audit

## Executive answer

The project is **inspired by SPARK-PDI and COLLEAGUE.SKILL**, but the current implementation is not a verbatim copy of either repository's core code. The bigger risk right now is not hidden copying; it is **unclear public-release hygiene** because the repository still lacks a top-level license and a crisp boundary between “our implementation,” “historical experiment slices,” and “related-work references.”

## Current evidence reviewed

- `reports/SPARK_COLLEAGUE_BORROWING_NOTES.md`
- `docs/RELATED_WORK_DELTA_AUDIT.md`
- current code under `src/skill_deployment/`, `scripts/`, and `agents/`

## Category breakdown

### 1. SPARK-inspired ideas

Clearly inspired by SPARK-style thinking:

- posterior evidence matters more than prior plan confidence
- execution traces and verifier outputs are first-class artifacts
- repair should be triggered by observed failure, not just initial compilation

These are idea-level borrowings and should be cited as related work.

### 2. COLLEAGUE.SKILL-inspired ideas

Clearly inspired by COLLEAGUE-like packaging:

- skill as a package rather than a single prompt
- inspectable manifests and versioned directories
- lifecycle framing around skill revision rather than just one-shot prompting

These are again idea-level borrowings and should be cited.

### 3. Our own implementation surface

The concrete current implementation appears to be locally authored:

- `src/skill_deployment/schemas.py`
- `src/skill_deployment/repair.py`
- `src/skill_deployment/capability_registry.py`
- `src/skill_deployment/runner.py`
- `agents/non_oracle_local_security_agent.py`
- `agents/llm_security_agent.py`
- `scripts/run_generalization_suite.py`
- `scripts/export_review_package.py`
- `scripts/validate_review_package.py`

These files reflect the current repo's own controlled-task assumptions and naming, not a direct transplant of upstream package structures.

## What should be treated as related-work borrowing, not originality

Do not present these as fully original concepts:

- execution-grounded posterior revision as a broad idea
- skill packaging as a broad idea
- trace-aware verification as a broad idea
- rollback/gate after repair as a broad idea

The scoped contribution is in **how these ideas are combined and narrowed inside a controlled skill-revision prototype**, not in inventing every concept from zero.

## Open-source / license risks

### Current risks

1. no top-level `LICENSE`
2. no explicit third-party attribution section in the public README
3. no documented rule for what external/reference files may or may not ship in `review_package`

### What looks safe to include in `review_package`

- locally authored reports
- locally authored scripts
- generated outputs
- docs that summarize related work in our own words

### What should remain reference-only

- any future cloned external repos
- large copied code snippets from upstream projects
- redistributed assets or configs whose license status is unclear

## Claims that require citation

These should explicitly cite related work:

- posterior execution evidence as a skill-distillation signal
- inspectable skill package lifecycle
- trace/evidence-driven diagnosis framing

## Claims that can be framed as our scoped contribution

Safer local contribution claims:

1. controlled multi-task prototype for typed posterior skill revision
2. artifact-backed review/export discipline for this prototype
3. typed repair operator registry over deployable Skill Packages
4. controlled Harbor/live-LLM repair-loop evidence with explicit claim boundaries
5. first-cut Skill Revision Validity Card framing for multi-axis result auditing

## Strongest current evidence

1. local code structure does not resemble a direct mirrored upstream package
2. borrowing docs already distinguish inspiration from reproduction
3. current artifacts are tightly coupled to this repo's own controlled-task schema

## Weakest current assumptions

1. without a repo license, public release remains muddy
2. without a public attribution section, external readers may misread inspiration as novelty
3. without a release checklist, future contributors could accidentally ship external reference material

## Top 10 Risks

1. no top-level license
2. no explicit public attribution file in root docs
3. concept-level inspiration being oversold as full originality
4. future external repo clones being mixed into core source claims
5. review-package export accidentally sweeping in reference assets later
6. advisor/reviewer confusion between “inspired by” and “reproduced from”
7. narrow engineering deltas being presented as sweeping algorithmic invention
8. lack of formal provenance check for imported code
9. weak public contributor guidance on attribution norms
10. no machine-readable license inventory

## Next 5 Highest-Value Fixes

1. add a top-level `LICENSE`
2. add a short root-level attribution note pointing to `reports/SPARK_COLLEAGUE_BORROWING_NOTES.md`
3. define `external_repos/` handling rules in docs
4. add a release checklist for review-package contents
5. keep framing the contribution as scoped and controlled rather than universal

## Bottom Line

The current repo should be described as **related-work-inspired but locally implemented**. The borrowing problem is manageable. The release-hygiene problem is more urgent.
