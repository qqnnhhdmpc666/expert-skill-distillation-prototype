# Harbor Non-Oracle Skill Diff

A1 capability config:

```text
UPLOAD_PATH_ISOLATION
```

A1 verifier feedback:

```text
missing: UPLOAD_AUDIT_RETENTION, UPLOAD_TYPE_MAGIC
```

A2 capability config:

```diff
 UPLOAD_PATH_ISOLATION
+UPLOAD_TYPE_MAGIC
+UPLOAD_AUDIT_RETENTION
```

Boundary: this is a deterministic heuristic Harbor repair loop, not an LLM-autonomous vulnerability discovery loop.
