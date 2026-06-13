# Harbor Non-Oracle Repair Loop: Upload Security

## Result

A deterministic non-oracle Harbor agent was run twice on the same controlled `real-upload-security-review` task.

| Attempt | Capability config | Reward | Verifier result |
|---|---|---:|---|
| A1 | `UPLOAD_PATH_ISOLATION` | 0.0 | FAIL: missing `UPLOAD_AUDIT_RETENTION`, `UPLOAD_TYPE_MAGIC` |
| A2 | `UPLOAD_PATH_ISOLATION`, `UPLOAD_TYPE_MAGIC`, `UPLOAD_AUDIT_RETENTION` | 1.0 | PASS |

## Closed Loop

1. A1 entered Harbor/Docker, read `/app/target/app.py` and `/app/target/config.yaml`, and wrote `/app/security_report.json`.
2. The Harbor verifier rejected A1 because the report only covered path isolation.
3. `A1/failure_feedback.json` was converted into `revision/patch_plan.json` via `revision/repair_policy.json` with repair action `patch_capability`.
4. A2 reran in Harbor with the patched capability config and passed with reward `1.0`.

## Artifacts

- `A1/security_report.json`
- `A1/target_reads.json`
- `A1/verifier_report.json`
- `A1/failure_feedback.json`
- `revision/patch_plan.json`
- `revision/gate_decision.json`
- `revision/skill_diff.md`
- `A2/security_report.json`
- `A2/target_reads.json`
- `A2/verifier_report.json`
- `summary.json`

## Boundary

This is a Harbor-in-the-loop deterministic heuristic repair loop. It proves that the non-oracle execution path can produce verifier feedback and a repaired rerun inside Harbor. It does not prove LLM-autonomous vulnerability discovery, broad security scanning, or full SPARK-PDI reproduction.
