# WSL / Harbor Status

Updated: 2026-06-08 final audit.

## Summary

The WSL2 / Docker / Harbor substrate is available. The recorded Harbor upload-security task now includes four evidence layers: oracle pass, non-oracle `nop` fail, non-oracle deterministic heuristic pass, and a non-oracle deterministic heuristic A1/A2 repair loop.

Evidence file:

- `outputs/wsl_harbor_real_upload_001/summary.md`
- `outputs/wsl_harbor_real_upload_001/summary.json`
- `outputs/harbor_non_oracle_upload_001/summary.md`
- `outputs/harbor_non_oracle_cli_upload_001/summary.md`
- `outputs/harbor_non_oracle_repair_loop_upload_001/summary.md`

## What This Proves

The current Harbor result supports these claims:

- WSL2 and Docker can host a Harbor-style task execution substrate.
- The upload-security task can run in a sandbox-like environment.
- Target files, agent execution logs, artifacts, downloaded results, and verifier reward can be recorded.
- The oracle path can produce all expected upload-security capabilities and receive reward 1.0.
- A non-oracle `nop` baseline can enter Harbor/Docker execution and receive verifier feedback with reward 0.0.
- A non-oracle deterministic heuristic agent can read target files, write `/app/security_report.json`, and receive reward 1.0 on the controlled upload task.
- A restricted non-oracle deterministic heuristic A1 can fail with reward 0.0, produce missing-capability feedback, consume a repair plan, rerun as A2, and receive reward 1.0.

## What This Does Not Prove

This does not prove:

- a non-oracle LLM/security agent can solve the task
- a live non-oracle LLM/CLI agent can solve the task
- a CLI agent can autonomously inspect target files and write the correct report
- the project has reproduced full SPARK-PDI trajectory distillation
- the system is a general vulnerability scanner
- sandbox execution has been integrated into the Streamlit demo as the default path

## Current Boundary

Safe wording:

> WSL2/Docker/Harbor substrate is available and an oracle security task passed. This proves task execution and verifier plumbing, not non-oracle agent autonomy.

Updated safe wording:

> A non-oracle `nop` baseline also ran in Harbor and failed with reward 0.0, proving non-oracle execution and failure feedback plumbing, not solving ability.

Additional safe wording:

> A custom non-oracle heuristic Harbor agent solved the controlled upload task by reading target files and writing `security_report.json`. This is a deterministic heuristic attempt, not LLM autonomy or broad vulnerability discovery.

Repair-loop safe wording:

> A controlled Harbor A1/A2 loop was run with the deterministic heuristic agent: A1 used a restricted capability config and failed with missing-capability feedback; the repair plan patched the capability config; A2 reran in Harbor and passed. This proves controlled feedback/repair plumbing in Harbor, not autonomous LLM vulnerability discovery.

Unsafe wording:

> A real sandbox agent already solves vulnerability tasks end to end.

## Next Required Step

Run one live non-oracle CLI or LLM-backed agent in Harbor on one security task, record:

- command trace
- stdout/stderr
- target file reads
- produced security report
- verifier output
- reward
- failure feedback
- repair attempt if it fails

Only after that should the project claim a live sandbox LLM/CLI agent closed loop. The current Harbor closed loop is deterministic heuristic code.
