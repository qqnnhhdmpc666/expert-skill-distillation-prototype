# Harbor Non-Oracle CLI Upload Attempt

## Result

- Backend: `WSL2 Ubuntu-24.04-Codex + Docker + Harbor`
- Task: `real-upload-security-review`
- Agent: `upload-security-heuristic-agent`
- Oracle: `false`
- LLM: `false`
- Entered Harbor/Docker task: `true`
- Read target files: `true`
- Generated `/app/security_report.json`: `true`
- Verifier ran: `true`
- Reward: `1.0`
- Passed: `true`

## What Improved Over `nop`

The previous `nop` non-oracle baseline entered Harbor but produced no report and received reward `0.0`.

This custom non-oracle heuristic agent reads:

- `/app/target/app.py`
- `/app/target/config.yaml`

It writes `security_report.json`, which the verifier reads and scores.

## Evidence

- `security_report.json`
- `target_reads.json`
- `verifier_report.json`
- `jobs/harbor_non_oracle_cli_upload_001/result.json`
- `jobs/harbor_non_oracle_cli_upload_001/real-upload-security-review__v67vodq/agent/UPLOAD_SECURITY_HEURISTIC_AGENT_RAN.txt`

## Boundary

This is a deterministic heuristic CLI-style Harbor custom agent. It is non-oracle and target-reading, but it is not an LLM agent and not proof of broad vulnerability discovery.
