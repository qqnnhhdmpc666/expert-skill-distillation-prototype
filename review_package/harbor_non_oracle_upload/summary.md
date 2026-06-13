# Harbor Non-Oracle Upload Smoke

## Result

- Backend: `WSL2 Ubuntu-24.04-Codex + Docker + Harbor`
- Task: `real-upload-security-review`
- Agent: `nop`
- Oracle: `false`
- Entered Harbor/Docker task: `true`
- Agent read target files: `false`
- Agent generated report: `false`
- Verifier ran: `true`
- Reward: `0.0`
- Passed: `false`

## Failure Feedback

The verifier failed because `/app/security_report.json` was not created.

Missing expected capabilities:

- `UPLOAD_AUDIT_RETENTION`
- `UPLOAD_PATH_ISOLATION`
- `UPLOAD_TYPE_MAGIC`

## Evidence

- `jobs/harbor_non_oracle_upload_001/result.json`
- `jobs/harbor_non_oracle_upload_001/real-upload-security-review__YfzBaaN/result.json`
- `jobs/harbor_non_oracle_upload_001/real-upload-security-review__YfzBaaN/verifier/result.json`
- `jobs/harbor_non_oracle_upload_001/real-upload-security-review__YfzBaaN/verifier/test-stdout.txt`

## Boundary

This is a real Harbor/Docker non-oracle baseline using the `nop` agent. It proves non-oracle Harbor execution and verifier feedback plumbing, but it intentionally does not solve the task.
