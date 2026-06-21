# V1 Walking Skeleton Completion Audit

Date: 2026-06-22

| Slice | Status | Fresh executable evidence |
|---|---|---|
| WS-0/1 state and sources | pass | CAS, SQLite, source snapshots, frozen OSV provider |
| WS-2 compiler | pass_core_local | Stage 0-9, quarantine, perturbation checks, same-schema direct baseline |
| Independent Judge | blocked_by_wrong_environment_variable_with_contract_tests | `DEEPSEEK_API_KEY` absent in same process; `OPENAI_API_KEY` fallback received HTTP 401; formal pass false |
| WS-3 bundle/runtime | pass | immutable closure, exact query provenance, domain/error separation |
| WS-4 deployment | pass | accepted B, rejected unsafe C, original-digest rollback, session pin |
| AgentHost | hard_blocked_by_auth_or_network_with_contract_tests | Codex CLI 0.137.0 invoked with Bundle artifact; provider unreachable; no fake pass |
| Harbor/external backend | local_docker_smoke_pass_parity_pending | WSL2 Harbor 0.1.45 + Docker 29.1.3 ran one official local task/verifier; public adapter parity absent |
| Public OSV pilot | pass_reference_runtime | 10 frozen public records, 21 deterministic cases, 21/21 reference decisions, false-safe 0 |
| Compiler comparison | superiority_not_demonstrated | six-case dev comparison is condition-insensitive; public held-out AgentHost comparison not run |
| Evolution improvement | evaluated_partial | score 2/3→3/3 on changed source; regressions retained; scope-limited claim |

## Fresh commands

```powershell
eskill --state-dir .tmp/goal-evidence-state demo --data-dir data/v1_walking_skeleton
eskill --state-dir .tmp/goal-evidence-state evaluate-compiler --data-dir data/v1_walking_skeleton
eskill --state-dir .tmp/goal-evolution-state-20260621 evaluate-evolution
eskill --state-dir .tmp/goal-evidence-state qualify-agent-host
eskill --state-dir .tmp/goal-evidence-state qualify-harbor
eskill --state-dir .tmp/goal-evidence-state build python-advisory --require-judge --judge-base-url https://api.deepseek.com --judge-model deepseek-chat
python scripts/build_public_osv_pilot.py --output data/public_osv_pilot
python scripts/run_public_osv_pilot.py --data-dir data/public_osv_pilot --state-dir .tmp/public-osv-pilot-state
```

## Remaining external requirements

1. A rotated DeepSeek credential must be supplied as `DEEPSEEK_API_KEY` for formal Judge pass.
2. A reachable authenticated Codex/OpenHands runtime is required for AgentHost qualification.
3. A public task adapter must pass native-vs-Harbor verifier parity; local Harbor plumbing is already available.
4. A condition-sensitive mature Agent must compare direct/compiler conditions on the frozen public held-out split.
5. Repeated autonomous Skill-text improvements are required before claiming stable evolution.

## Final verification

- Full repository: `94 passed` (2026-06-22).
- V1 in newly created `.tmp/public-evidence-clean-venv`: `40 passed`.
- Clean-venv installed `eskill.exe demo`: pass with Bundle `sha256:a38606f2d57160fe556467261c790e1d2b8e4dbac19ca1001d6f7ddc55817457`.
- Ruff for `src/expert_skill_system`, V1 tests and new public/auth scripts: pass.
- Public OSV frozen-file hash verification: 11/11 pass.
- Legacy task cases: 8/8 valid.
- Review package validation: 0 errors.
