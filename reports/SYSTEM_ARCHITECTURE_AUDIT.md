# System Architecture Audit

Date: 2026-06-08

## Verdict

Current status: **moderately mature controlled prototype**, not yet a unified reusable framework.

The repository now has a credible shared core under `src/skill_deployment/`, including a shared controlled task-case loader and shared controlled verifier. The end-to-end execution backbone still lives mostly in `scripts/` and agent-specific files. The architecture is good enough for controlled experiments, review-package export, and small multi-task evidence. It is not yet the kind of package where new tasks, new backends, and new repair operators all plug into one stable internal API.

## Lifecycle Map

The current lifecycle is implemented across these modules:

| Lifecycle stage | Main implementation | Notes |
|---|---|---|
| task definition | `data/task_cases/<case>/case.yaml`, `source_materials/`, `target_asset/`, `verifier_contract.yaml`, `src/skill_deployment/task_cases.py` | This is now the shared controlled source of truth for the suite. |
| typed artifact schemas | `src/skill_deployment/schemas.py` | Legacy `TaskCase` still exists here; controlled-suite cases now load through `task_cases.py`. |
| capability semantics | `src/skill_deployment/capability_registry.py` | Shared by the suite and the heuristic local semantic agent. |
| runner abstraction | `src/skill_deployment/runner.py` | Dispatches offline deterministic, local semantic, and local live-LLM execution. Harbor remains outside the shared runner path. |
| Harbor replay adapter | `src/skill_deployment/harbor_adapter.py` | Reads existing Harbor repair-loop artifacts into shared execution vocabulary; does not rerun Harbor. |
| repair operator registry | `src/skill_deployment/repair.py` | Best current architectural consolidation point. |
| offline suite orchestration | `scripts/run_generalization_suite.py` | Still contains execution, artifact writing, and reporting, but now delegates case selection and verifier logic to shared modules. |
| local deterministic agents | `agents/local_security_review_agent.py`, `agents/non_oracle_local_security_agent.py` | Two different local agent styles with different maturity levels. |
| live LLM backend | `agents/llm_security_agent.py`, `scripts/run_live_llm_upload.py`, `src/skill_deployment/runner.py` | Real API-backed agent path, now under the shared local runner registry, but still task-slice driven. |
| Harbor / Docker execution slices | `scripts/run_harbor_llm_repair_loop.py`, `scripts/run_harbor_llm_repair_loop_config.py` | Evidence is real, but orchestration is still per-slice. |
| external review export | `scripts/export_review_package.py`, `scripts/validate_review_package.py` | Strong artifact-packaging discipline. |

## Shared Core vs Script Gravity

### Already centralized

- `SkillPackage`, `ExecutionReport`, `VerifierReport`, `PatchPlan`, `GateDecision`, `TraceRecord` in `src/skill_deployment/schemas.py`
- typed repair registry in `src/skill_deployment/repair.py`
- shared capability catalog in `src/skill_deployment/capability_registry.py`
- lightweight CLI in `src/skill_deployment/cli.py`

### Still script-heavy

- scenario loading and case normalization in `scripts/run_generalization_suite.py`
- verifier logic in `scripts/run_generalization_suite.py`
- Harbor LLM loop logic in `scripts/run_harbor_llm_repair_loop.py` and `scripts/run_harbor_llm_repair_loop_config.py`
- live LLM local loop orchestration in `scripts/run_live_llm_upload.py`, though actual agent execution now goes through `LiveLLMSecurityRunner`
- Harbor replay access through `scripts/run_harbor_replay_summary.py`, though live Harbor execution is still script-local
- review package curation in `scripts/export_review_package.py`

This means the repo has **shared nouns** and part of a **shared verb path**, but Harbor and several legacy slices still sit outside it.

## Important Structural Findings

### 1. There are still two TaskCase worlds, but the new one is finally centralized

- `src/skill_deployment/schemas.py::TaskCase` expects `case.md` plus `expected.json`.
- `src/skill_deployment/task_cases.py` now owns the newer `data/task_cases/<case>/case.yaml` format used by the controlled suite.

This is no longer a script-only split, but it is still a split. The legacy holdout schema and the newer controlled-suite schema have not yet been merged into one canonical `TaskCase` object.

### 2. Runner abstraction now owns the stable local backends, but not Harbor

`src/skill_deployment/runner.py` now instantiates real backend runner objects for the stable local paths:

- offline deterministic execution
- local semantic execution
- local live LLM execution

What is still outside the shared path:

- Harbor paths each have their own slice runner
- the generalization suite still intentionally rejects `live_llm_text` because only the upload local slice has controlled evidence
- the new local data-quality LLM loop is real controlled evidence, but it is still not admitted into the generalization suite path

So the repo now has **partial runner ownership**, not full backend unification.

### 3. Controlled verifier is now shared, but broader verifier layering is still missing

The suite and local live-LLM upload path now share `src/skill_deployment/verifier.py` for the core controlled verifier logic. That is a real maturity gain.

What is still missing:

- negative-control verification still uses its own stricter helper
- Harbor scripts still carry some local verifier handling
- verifier results are not yet split into reusable sub-checker modules

### 4. Repair policy and repair operator registry are close, but not perfectly synchronized

`revision/repair_policy.json` maps:

- `target_context_missing -> ask_for_target_context`

but `src/skill_deployment/repair.py` currently resolves that failure via:

- `op_add_observation_step_generic`
- `repair_action = add_observation_step`

The system behaves reasonably, but the policy surface and typed operator surface are not in one canonical place yet.

### 5. Old experiment slices still coexist with the new architecture

`scripts/run_multitask_closed_loop.py` still defines its own `TaskCase` dataclass and internal repair logic. That file is now useful as historical evidence, but it is no longer the cleanest architectural center.

## What changes when we add something new?

### Add a new task family

Today this usually means touching:

1. `data/task_cases/<new_case>/case.yaml`
2. `source_materials/`, `target_asset/`, `verifier_contract.yaml`
3. `src/skill_deployment/capability_registry.py`
4. sometimes verifier logic inside `scripts/run_generalization_suite.py`
5. sometimes backend-specific scripts if Harbor/LLM variants are needed

This is better than before, but still not “drop-in task plugin” maturity.

### Add a new backend

Today this means:

1. creating a new agent or runner script under `agents/` or `scripts/`
2. wiring a new branch into orchestration scripts
3. deciding how outputs map back into verifier expectations

The missing piece is a concrete `BackendRunner` registry that all backends must implement.

### Add a new repair operator

This is the cleanest extension path currently:

1. add a typed operator in `src/skill_deployment/repair.py`
2. align `revision/repair_policy.json`
3. add tests
4. ensure at least one scenario can trigger it

This part already looks like a real systems research substrate.

## Open-Source Readiness Snapshot

Good:

- `pyproject.toml` exists
- `src/` package exists
- `tests/` exists
- artifact export/validation exists
- review-package discipline is strong

Missing:

- no `LICENSE`
- no `CONTRIBUTING.md`
- no CI workflow
- no lockfile
- no clear backend plugin interface
- no single canonical task-case schema

## Strongest Current Evidence

1. `outputs/validation/generalization_suite.json`: five controlled task families through one suite
2. `outputs/validation/negative_controls.json`: explicit unsupported-evidence and false-positive refusal
3. `outputs/validation/ablation_summary.json`: typed repair plus gate pressure test
4. `outputs/harbor_llm_repair_loop_upload_001/summary.json`
5. `outputs/harbor_llm_repair_loop_config_001/summary.json`
6. `review_package.zip` plus `scripts/validate_review_package.py`

## Weakest Current Assumptions

1. the shared `TaskCase` schema is not actually the same object used by the current suite
2. Harbor and several slice scripts still keep backend logic outside the shared runner
3. local agents remain deterministic and capability-driven
4. the verifier is still implemented as slice logic rather than a standalone reusable package
5. Harbor LLM evidence is real but narrow

## Top 10 Risks

1. schema drift between `src/skill_deployment/schemas.py` and `data/task_cases/`
2. backend logic divergence across `scripts/`
3. verifier duplication and silent behavior skew
4. repair policy/operator mismatch
5. review package export list drifting away from actual evidence surface
6. old script slices confusing contributors about which path is canonical
7. local deterministic agents being overinterpreted as semantic agents
8. lack of CI allowing regressions in reports/export/validation
9. no license, which blocks safe open-source release
10. mixed maturity levels presented side by side without one architecture README

## Next 5 Highest-Value Fixes

1. merge legacy `TaskCase` and controlled `ControlledTaskCase` into one canonical schema surface
2. extend `BackendRunner` from the current local trio to Harbor wrappers
3. extend the shared verifier so Harbor and negative-control paths stop carrying local verifier variants
4. align `revision/repair_policy.json` and typed operators into one canonical registry contract
5. add `LICENSE`, CI smoke checks, and a small architecture README pointing to the canonical path

## Bottom Line

The repository is no longer a pile of demo scripts. It has real shared architecture now. But the architecture is still **half-centralized**: strong enough to support controlled research claims, not yet strong enough to claim mature framework status.

## Addendum: Local Live LLM Runner Closure

One more architecture closure has landed beyond the earlier runner audit:

1. local live LLM execution now routes through `src/skill_deployment/runner.py::LiveLLMSecurityRunner`
2. `scripts/run_live_llm_upload.py` no longer shells directly into `agents/llm_security_agent.py`
3. the local upload A1/A2 loop now emits a per-loop validity card artifact alongside summary, verifier, and patch artifacts

This improves internal honesty: local live LLM execution is still upload-only controlled evidence, but it now uses the same shared execution spine as the other stable local backends.

## Addendum: Harbor Replay Adapter Closure

Another controlled-system closure has now landed:

1. `src/skill_deployment/harbor_adapter.py` reads existing Harbor upload/config repair loops
2. `get_backend_runner(...)` now exposes replay backends for those two Harbor evidence slices
3. the shared system can summarize Harbor A1/A2 outputs without re-running Docker/WSL

This is still not full Harbor backend unification. It is a minimal replay/read-existing bridge from standalone Harbor evidence into the shared system skeleton.

## Addendum: Core Skeleton Closure

Since the first audit draft, two concrete architecture closures landed:

1. `TaskCase` now has one canonical forward path in `src/skill_deployment/task_cases.py`, while the older holdout format is preserved only through `LegacyHoldoutTaskCase`.
2. `src/skill_deployment/runner.py` now has real `OfflineDeterministicRunner` and `NonOracleLocalSemanticRunner` implementations, and `run_generalization_suite.py` uses the runner registry for those two backends.

This does not make the architecture fully mature, but it moves the repo from “shared nouns only” toward “shared nouns plus partial shared execution ownership.”
