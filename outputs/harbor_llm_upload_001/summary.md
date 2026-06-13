# Harbor LLM Upload Run

## Result

A real OpenAI-compatible LLM-backed non-oracle agent ran inside the Harbor/Docker upload-security task.

| Item | Value |
|---|---|
| Agent | `upload-security-llm-agent` |
| Model | `gpt-5.5` |
| Oracle | `false` |
| Reads target | `true` |
| Reads `/app/skill` | `true` |
| Writes `/app/security_report.json` | `true` |
| Verifier reward | `1.0` |
| Passed | `true` |

## Evidence

- `target_reads.json` shows reads from `/app/target/app.py`, `/app/target/config.yaml`, `/app/skill/SKILL.md`, and `/app/skill/manifest.json`.
- `security_report.json` contains three target-grounded findings.
- `verifier_report.json` has `missing: []` and no schema errors.
- `backend_metadata.json` records model usage without storing the API key.

## Boundary

This is one controlled Harbor LLM non-oracle upload-security run. It does not prove multi-task Harbor LLM generalization, broad vulnerability scanning, or full SPARK-PDI reproduction.
