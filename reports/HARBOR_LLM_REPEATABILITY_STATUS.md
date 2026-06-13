# Harbor LLM Repeatability Status

- Runs observed: `3`
- A1 all fail: `True`
- A2 all pass: `True`
- Reward stable: `True`
- Failure reason stable: `True`

| Run | Origin | A1 | A2 | Reward Delta | A1 Feedback | A1 Missing | Tokens A1/A2 | Latency ms A1/A2 |
|---|---|---:|---:|---:|---|---|---|---|
| repeat_1 | existing_baseline | False | True | 1.0 | missing_capability | UPLOAD_AUDIT_RETENTION, UPLOAD_TYPE_MAGIC | 962/1277 | 10903/15372 |
| repeat_2 | fresh_rerun | False | True | 1.0 | missing_capability | UPLOAD_AUDIT_RETENTION, UPLOAD_TYPE_MAGIC | 1006/1309 | 6640/15132 |
| repeat_3 | fresh_rerun | False | True | 1.0 | missing_capability | UPLOAD_AUDIT_RETENTION, UPLOAD_TYPE_MAGIC | 677/1343 | 13779/12281 |

## Interpretation

- Failure mode consistency: `feedback_types=['missing_capability'], missing_sets=[('UPLOAD_AUDIT_RETENTION', 'UPLOAD_TYPE_MAGIC')]`
- Prompt sensitivity risk: `low_in_this_slice`
- Token / latency assessment: `average total tokens per loop=2191.33, average combined latency ms per loop=24702.33`

## Boundary

This is repeatability evidence for one controlled Harbor LLM upload repair loop. It is not multi-task Harbor LLM stability evidence.
