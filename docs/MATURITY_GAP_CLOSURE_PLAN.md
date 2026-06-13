# Maturity Gap Closure Plan

Updated: 2026-06-08

## Goal

Move the project from an artifact-rich controlled prototype toward a more mature research system without pretending it is already SPARK-PDI- or COLLEAGUE.SKILL-level.

Safe current positioning:

```text
typed posterior revision over deployable expert-skill packages
```

Not the current goal:

```text
add more page chrome
claim open-world vulnerability discovery
claim broad multi-domain Harbor generalization
```

## What "maturity" means here

We should treat maturity as five separate layers:

1. backend reality
2. task/evaluation breadth
3. reusable architecture
4. engineering hygiene
5. product/demo clarity

The project is already ahead on artifact discipline and controlled evidence. The biggest remaining gaps are backend breadth, reusable core abstractions, and engineering standardization.

## Priority Order

### P0: Stop demo/UI churn and harden the system core

Why:

- The repository already has enough evidence to explain the idea.
- Extra UI complexity is now lower value than backend and architecture hardening.

Required actions:

1. Keep `demo/streamlit_app.py` result-first and artifact-backed.
2. Do not add new tabs unless they expose new evidence.
3. Route every displayed claim to a real file under `runs/` or `outputs/`.
4. Keep claim-boundary language synchronized between page, docs, and reports.

Success signal:

```text
Every major UI conclusion can be traced to an artifact path.
```

### P1: Broaden real execution evidence

Why:

- We now have controlled Harbor LLM evidence on upload and config.
- The biggest credibility gap versus stronger systems is still narrow real-execution breadth.

Required actions:

1. Add one third Harbor LLM task family beyond upload/config.
2. Repeat at least a small A1/A2 repair loop on that task.
3. Record:
   - target reads
   - security report
   - verifier report
   - patch plan
   - gate decision
   - reward delta
4. Keep verifier/gate deterministic.

Success signal:

```text
Harbor LLM A1/A2 repair-loop evidence exists for 3 task families with at least 1 repeatability probe.
```

### P2: Replace script-first sprawl with shared core modules

Why:

- Many claims already rely on common patterns, but much logic still lives in long runners.
- This is the biggest gap versus more mature open-source systems.

Required actions:

1. Move reusable logic out of `scripts/` and into `src/skill_deployment/`.
2. Define typed schemas or dataclasses for:
   - `TaskCase`
   - `SkillPackage`
   - `ExecutionReport`
   - `VerifierReport`
   - `PatchPlan`
   - `GateDecision`
   - `TraceRecord`
3. Add one shared runner interface for:
   - offline deterministic
   - local non-oracle heuristic
   - local live LLM
   - Harbor LLM
4. Make repair policy selection a reusable module rather than inline script logic.

Success signal:

```text
scripts/ only do argument parsing and orchestration;
TaskCase / SkillPackage / VerifierReport / PatchPlan / GateDecision share one schema layer;
offline / local / LLM / Harbor backends fit one runner interface;
repair-policy selection lives in one reusable module;
adding a new task family does not require changing the main runner logic.
```

### P3: Add one non-security task family before over-expanding the benchmark

Why:

- The project goal is broader than a security-review-only system.
- If every new task is still security-only, the abstraction will keep looking domain-bound.

Required actions:

1. Add one non-security controlled task family in offline/local backend first.
2. Reuse the same TaskCase / SkillPackage / Verifier / Repair / Gate skeleton.
3. Prefer a task that still allows explicit evidence and repair, for example:
   - document review
   - data quality checking
   - compatibility review
   - log diagnosis
4. Record the same artifact chain as security tasks.

Success signal:

```text
At least one non-security task family runs through the same controlled lifecycle without special-casing the main runner.
```

### P4: Strengthen evaluation from controlled demo to controlled benchmark

Why:

- The current evidence is decent for a 0.1 prototype.
- It is still too small to claim system maturity.

Required actions:

1. Expand `data/task_cases/` from 4 positive + 2 negative to a more convincing suite.
2. Keep task families distinct enough to force different feedback/repair paths.
3. Add more negative controls:
   - unsupported evidence
   - false positive on clean target
   - regression after append-style repair
   - output contract degradation
4. Add aggregate summaries:
   - feedback distribution
   - repair operator distribution
   - A1 -> A2 reward delta distribution
   - pass/fail by backend

Success signal:

```text
The project can report controlled cross-task metrics, not only handpicked case summaries.
```

### P5: Upgrade engineering hygiene to "real repo" level

Why:

- This is where SPARK/COLLEAGUE still clearly look more mature.

Required actions:

1. Add CI for:
   - `py_compile`
   - `pytest`
   - task-case validation
   - review-package validation
2. Expand unit tests around:
   - schema parsing
   - verifier
   - repair policy
   - gate logic
   - trace validation
3. Add clearer package entrypoints:
   - `skill-deploy run-demo`
   - `skill-deploy run-suite`
   - `skill-deploy export-review-package`
   - `skill-deploy validate`
4. Keep dependency lock and lint config stable.

Success signal:

```text
Any contributor can clone, install, validate, and rerun the main evidence path from one documented command sequence.
```

### P6: Productize the “what does the user get” story

Why:

- The demo is now clearer, but the system still risks sounding like an internal verifier lab.

Required actions:

1. Keep the top-level presentation about user value:
   - does the report get better
   - does the failure trigger a meaningful repair
   - can the run be exported and audited
2. Keep rules/capabilities secondary to:
   - task outcome
   - evidence quality
   - repair loop
3. Keep custom-material mode honest:
   - controlled compilation entry
   - not arbitrary strict vulnerability verification

Success signal:

```text
A reviewer can explain the system in 30-60 seconds without falling back to internal jargon.
```

## Where our own innovation should concentrate

Do not anchor novelty on:

- “we also use posterior feedback”
- “we also have a skill package”

Better focus:

1. typed posterior repair operators
2. promotion gate and rollback boundary
3. risk-budgeted selective trace
4. artifact-backed repair-loop evidence
5. deployment-time revision, not just one-shot distillation

## Concrete 2-stage execution plan

### Stage A: Must-do for the next maturity pass

1. Third Harbor LLM task family
2. shared backend runner abstraction
3. typed artifact schemas
4. one non-security task family in offline/local controlled mode
5. CI smoke workflow
6. aggregated controlled metrics report

### Stage B: Strong next-step upgrades

1. larger repeatability probe
2. rollback/list/diff CLI around Skill versions
3. narrower but cleaner public API
4. packaged reproducibility guide

## Bottom Line

The current system is no longer a toy page demo. It is a controlled, multi-backend, artifact-backed prototype for deployable expert-skill revision.

The biggest maturity gaps are now:

```text
real-execution breadth
shared reusable architecture
engineering standardization
controlled evaluation scale
```

The next maturity step is not more UI, but broader real execution evidence, reusable core abstractions, controlled cross-task evaluation, and minimal repo-level standardization.
