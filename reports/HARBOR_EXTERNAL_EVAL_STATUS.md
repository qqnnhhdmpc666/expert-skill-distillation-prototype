# Harbor External Evaluation Status

Date: 2026-06-22

```text
external_evaluation_backend = runtime_and_local_docker_smoke_available_parity_pending
external_evaluation_pass = false
```

Fresh command:

```powershell
eskill --state-dir .tmp/goal-evidence-state qualify-harbor
```

Corrected observed environment:

- Windows Harbor/Docker commands: missing.
- WSL distribution: `Ubuntu-24.04-Codex` (WSL2).
- Harbor: `/opt/spark/harbor-src-locked/.venv/bin/harbor` (`0.1.45`).
- Docker: `/usr/bin/docker` (client/server `29.1.3`).
- adapter contract test: pass.
- replay used: false.

The command wrote a minimal non-replay task contract and qualification artifact:

```text
sha256:ca683a0c908d48a1f9eeba5c3dffdc6133c48a5b4bd95e9c50323b4c33c36c06
```

A fresh local Harbor Docker smoke completed 1/1 trials with no errors and verifier reward `1.0`. Its official result is `/opt/spark/harbor-local-smoke-20260622/eskill-harbor-smoke-20260622/result.json` inside WSL. This proves plumbing only. No public benchmark parity or non-oracle Agent/Skill effectiveness result exists, so `external_evaluation_pass` remains false.

Full commands and evidence are recorded in `reports/LOCAL_ENV_DISCOVERY.md`.
