# V1 Walking Skeleton Completion Audit

Date: 2026-06-21

| Slice | Status | Fresh executable evidence |
|---|---|---|
| WS-0/1 state and sources | pass | CAS, SQLite, source snapshots, frozen OSV provider |
| WS-2 compiler | pass_core_local | Stage 0-9, quarantine, perturbation checks, same-schema direct baseline |
| Independent Judge | hard_blocked_by_auth_with_contract_tests | DeepSeek official endpoint returned HTTP 401; malformed/auth/critical tests pass |
| WS-3 bundle/runtime | pass | immutable closure, exact query provenance, domain/error separation |
| WS-4 deployment | pass | accepted B, rejected unsafe C, original-digest rollback, session pin |
| AgentHost | hard_blocked_by_auth_or_network_with_contract_tests | Codex CLI 0.137.0 invoked with Bundle artifact; provider unreachable; no fake pass |
| Harbor/external backend | contract_ready_but_harbor_missing | Harbor, Docker and WSL distribution absent; non-replay contract tested |
| Compiler comparison | evaluated_on_dev_only_inconclusive | four conditions × six dev cases; reference backend is condition-insensitive |
| Evolution improvement | evaluated_partial | score 2/3→3/3 on changed source; regressions retained; scope-limited claim |

## Fresh commands

```powershell
eskill --state-dir .tmp/goal-evidence-state demo --data-dir data/v1_walking_skeleton
eskill --state-dir .tmp/goal-evidence-state evaluate-compiler --data-dir data/v1_walking_skeleton
eskill --state-dir .tmp/goal-evolution-state-20260621 evaluate-evolution
eskill --state-dir .tmp/goal-evidence-state qualify-agent-host
eskill --state-dir .tmp/goal-evidence-state qualify-harbor
eskill --state-dir .tmp/goal-evidence-state build python-advisory --require-judge --judge-base-url https://api.deepseek.com --judge-model deepseek-chat
```

## Remaining external requirements

1. A valid DeepSeek credential is required for formal Judge pass.
2. A reachable authenticated Codex/OpenHands runtime is required for AgentHost qualification.
3. Harbor plus Docker/WSL is required for external backend execution.
4. A condition-sensitive mature Agent and held-out/public tasks are required to test compiler superiority.
5. Repeated autonomous Skill-text improvements are required before claiming stable evolution.

## Final verification

- Full repository: `88 passed`.
- V1 in a newly created external clean venv: `34 passed`.
- Ruff: pass.
- Legacy task cases: 8/8 valid.
- Review package validation: 0 errors.
- Installed clean-venv `eskill.exe` demo: pass with Bundle `sha256:a458b8005fd99e26820231a21c411fdcb1b9d195d571fd60dbe4e168afbb89f4`.
