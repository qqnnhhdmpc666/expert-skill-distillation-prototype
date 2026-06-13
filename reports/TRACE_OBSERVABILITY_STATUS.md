# Trace Observability Status

更新时间：2026-06-08 04:16 CST

## Current Status

The generalization suite now writes all four required trace families:

```text
runs/generalization/<scenario>/trace/source_trace.json
runs/generalization/<scenario>/trace/execution_trace_A1.jsonl
runs/generalization/<scenario>/trace/feedback_trace_A1.json
runs/generalization/<scenario>/trace/revision_trace_v1_to_v2.json
runs/generalization/<scenario>/trace/execution_trace_A2.jsonl
```

The local real agent also writes:

```text
runs/local_agent_smoke/trace.jsonl
runs/local_agent_smoke/stdout.log
runs/local_agent_smoke/backend_metadata.json
```

## What Is Observable

- Expert source to capability mapping.
- Which target files were read.
- Which findings were emitted.
- Which evidence spans were bound.
- Which verifier feedback type fired.
- Which repair action was chosen.
- Which gate decision accepted or rejected the repair.

## Remaining Gaps

- No full UI visualization yet.
- No real non-oracle sandbox-agent stdout/command trajectory yet.
- No dynamic exploitability or reachability trace.
- No cross-file semantic evidence graph.

## Design Decision

The next UI should read trace artifacts, not recompute them in Streamlit. First visualization should be a four-column table: source, execution, feedback, revision.
