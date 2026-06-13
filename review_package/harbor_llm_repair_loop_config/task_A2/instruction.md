Review the target configuration in `/app/target`.

Create `/app/security_report.json` with the outer shape:

```json
{"findings": [{"capability_id": "CONFIG_HARDCODED_SECRET", "evidence_span": "...", "recommended_fix": "..."}]}
```

The report must include capability_id, evidence_span, and recommended_fix for each finding.

The task focuses on hardcoded secret, insecure production HTTP endpoint, and production debug mode.