# Harbor External Evaluation Status

Date: 2026-06-23

```text
harbor_binary = pass (0.1.45)
docker_binary = pass (29.1.3)
public_task_adapter = prepared
native_public_pair = pass
native_vs_harbor_parity = inconclusive
external_evaluation_pass = false
```

Two Harbor-native tasks were added for frozen public OSV record `PYSEC-2018-28`:

- `requests==2.19.1` -> `advisory_applicable / VERSION_IN_RANGE`
- `requests==2.20.0` -> `advisory_not_applicable / VERSION_OUT_OF_RANGE`

The task verifier requires the same verdict/reason contract as the native evaluator and
writes Harbor reward plus verifier result artifacts. The fresh native public pilot passed
21/21 before the v2 expansion.

Harbor execution did not complete. WSL initially exposed Harbor and Docker, then subsequent
calls reported the distribution unavailable; a host-context status probe also failed to
complete within its bound. No Harbor reward or verifier artifact exists, so parity remains
`inconclusive`, not pass. The prepared tasks are plumbing artifacts only.
