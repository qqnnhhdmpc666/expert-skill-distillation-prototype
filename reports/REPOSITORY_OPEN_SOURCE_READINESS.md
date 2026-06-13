# Repository Open-Source Readiness

## Verdict

Current readiness: **not yet ready for clean public release**, but close enough that one focused hygiene pass could get it there.

## What is already in place

- `pyproject.toml`
- importable `src/skill_deployment/`
- eight pytest files under `tests/`
- review-package export and validation
- substantial documentation and claim-boundary notes
- artifact-backed outputs that support auditability

## What is still missing

### Blocking

1. no `LICENSE`
2. no `CONTRIBUTING.md`
3. no CI workflow under `.github/workflows/`
4. no dependency lockfile

### High-friction

1. two competing task-case formats
2. no single architecture README for contributors
3. many `scripts/run_*.py` entrypoints without one obvious canonical pathway
4. generated outputs and experiment slices may overwhelm new users

## Security / release hygiene

Good:

- `scripts/validate_review_package.py` includes secret scanning
- export validation checks links and missing references
- review package avoids blindly shipping every output

Still needed:

- a repo-level secret-scan policy
- `.env.example` / configuration guidance
- pre-release checklist for what must never be committed

## Contributor experience

Current experience:

- strong for an internal collaborator who already knows the story
- weak for an external contributor landing cold

Needed for public release:

1. `README.md` with quickstart and architecture map
2. `LICENSE`
3. `CONTRIBUTING.md`
4. minimal CI smoke:
   - `pytest`
   - `validate_task_cases.py`
   - `export_review_package.py`
   - `validate_review_package.py`
5. clear statement of supported Python version and optional Harbor/LLM prerequisites

## Safe public positioning

Safe:

> artifact-rich controlled prototype for posterior skill revision experiments

Unsafe:

> mature open-source framework for general autonomous vulnerability discovery

## Release recommendation

Short answer: **do not open-source exactly as-is**.

Do this first:

1. add `LICENSE`
2. add CI smoke workflow
3. unify task-case schema
4. add one contributor-facing architecture doc
5. prune or clearly label legacy experiment slices

Once those are done, the repo becomes a credible public research prototype rather than an internal overnight lab notebook with strong artifacts.
