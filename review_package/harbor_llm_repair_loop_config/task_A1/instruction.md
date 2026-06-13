Review the target configuration in `/app/target`.

Create `/app/security_report.json` with the outer shape:

```json
{"findings": [{"capability_id": "CONFIG_HARDCODED_SECRET", "evidence_span": "...", "recommended_fix": "..."}]}
```

For this exploratory v1 run, the report may omit `recommended_fix` if evidence is already specific.

The task focuses on hardcoded secret, insecure production HTTP endpoint, and production debug mode.