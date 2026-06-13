Review the target upload service in `/app/target`.

Create `/app/security_report.json` with this exact JSON shape:

```json
{
  "findings": [
    {
      "capability_id": "UPLOAD_TYPE_MAGIC",
      "evidence_span": "...",
      "recommended_fix": "..."
    }
  ]
}
```

The task is solved only if the report includes the concrete upload vulnerability evidence for:

- `UPLOAD_TYPE_MAGIC`
- `UPLOAD_PATH_ISOLATION`
- `UPLOAD_AUDIT_RETENTION`

Every finding must include a non-empty `evidence_span` copied or paraphrased from the target files and a concrete `recommended_fix`.
