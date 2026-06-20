# V1 Walking Skeleton Completion Audit

Date: 2026-06-21

## Requirement ledger

| Slice | Status | Fresh executable evidence |
|---|---|---|
| WS-0 schema/state | pass | CAS artifact store, SQLite WAL metadata, CAS ActiveBinding, strict runtime envelope tests |
| WS-1 sources/providers | pass | Markdown line/byte locators, pinned requirements diagnostics, frozen OSV SQLite provider, held-out exclusion |
| WS-2 compiler | pass_core_local | Stage 0–9 artifacts, exact binding, conflict preservation, quarantine, independent Skill/Knowledge digests, 8 perturbation checks |
| Independent Judge | configured_but_auth_blocked | Formal gate and blind API client implemented; fresh DeepSeek official endpoint attempt returned HTTP 401 |
| WS-3 bundle/runtime | pass | immutable Bundle closure, snapshot A/B identity separation, exact query provenance, decision/error matrix |
| WS-4 deployment | pass | promote A, promote B, reject unsafe C, explicit rollback B→original A digest, session pin retained |
| Unified CLI | pass | installed `eskill.exe`; init/source/build/validate/promote/run/inspect/history/rollback/baselines/demo |
| Clean install | pass | isolated venv `pip install -e .[dev]`, installed demo and V1 tests passed |
| AgentHost qualification | blocked_not_run | ReferenceDecisionBackend is intentionally not counted as Agent effectiveness |
| External/Harbor qualification | blocked_not_run | deferred until Core Walking Skeleton; no parity or benchmark claim |

## Fresh commands

```powershell
python -m pytest -q
python -m ruff check src/expert_skill_system tests/v1
python scripts\validate_task_cases.py
python -m skill_deployment.cli validate-review-package

python -m venv .tmp\clean-core-venv
.\.tmp\clean-core-venv\Scripts\python.exe -m pip install -e .[dev]
.\.tmp\clean-core-venv\Scripts\eskill.exe --state-dir .tmp\clean-core-demo-state demo --data-dir data\v1_walking_skeleton
```

## Invariants exercised

- Runtime state is under `.eskill`, not legacy `outputs/`.
- Held-out digest is absent from build visibility manifests.
- Dynamic OSV advisory data is absent from Skill IR.
- Attestation subjects must match exact Bundle component digests.
- Advisory absence is unresolved, not “not applicable”.
- Missing knowledge binding blocks; corrupt closure is runtime failure.
- Rejected candidate never enters ActiveBinding.
- Rollback rebinds the original Bundle digest rather than recompiling an approximation.
- A running session remains pinned to its original Bundle after rollback.
- Repeating the same semantic build under a different build id produces the same ReleaseBundle digest.

## Remaining research gaps

1. A valid independent Judge credential/run is still required for `formal-research` attestation pass.
2. Codex/OpenHands AgentHost qualification is not run.
3. Harbor and public external task parity are not run.
4. The current deterministic V1 compiler proves the staged architecture and source constraints, not broad open-world extraction.
5. Compiler superiority and stable evolution improvement remain not demonstrated.
