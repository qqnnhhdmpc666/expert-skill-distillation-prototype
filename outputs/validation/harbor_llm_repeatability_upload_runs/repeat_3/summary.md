# Harbor LLM Upload Repair Loop

| Attempt | Pass | Reward | Coverage | Missing | Skill capabilities |
|---|---:|---:|---:|---|---|
| A1 | False | 0.0 | 0.3333 | UPLOAD_AUDIT_RETENTION, UPLOAD_TYPE_MAGIC | UPLOAD_PATH_ISOLATION |
| A2 | True | 1.0 | 1.0 | none | UPLOAD_PATH_ISOLATION, UPLOAD_AUDIT_RETENTION, UPLOAD_TYPE_MAGIC |

A1 and A2 use two generated Harbor task copies so the container reads different `/app/skill` snapshots.

Boundary: this is a controlled Harbor LLM repair loop for one upload-security task. It does not prove Harbor LLM multi-task generalization.
