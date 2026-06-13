# Trace Visualization Design

## Goal

The demo should not show a complex graph first. It should show a four-column evidence path:

```text
Expert Source -> Execution Finding -> Verifier Feedback -> Skill Revision
```

## Four Trace Types

### 1. source_trace

Maps expert material to capability and skill files.

Current artifact:

```text
runs/generalization/<scenario>/trace/source_trace.json
runs/generalization/<scenario>/provenance/source_to_skill_mapping.json
```

### 2. execution_trace

Records which target assets were read and which findings were produced.

Current artifact:

```text
runs/generalization/<scenario>/trace/execution_trace_A1.jsonl
runs/generalization/<scenario>/trace/execution_trace_A2.jsonl
runs/local_agent_smoke/trace.jsonl
```

### 3. feedback_trace

Records verifier failure, feedback type, missing capabilities, schema/evidence errors, and scores.

Current artifact:

```text
runs/generalization/<scenario>/trace/feedback_trace_A1.json
runs/generalization/<scenario>/verifier/A1_report.json
```

### 4. revision_trace

Records repair action, gate decision, intervention severity, and score rationale.

Current artifact:

```text
runs/generalization/<scenario>/trace/revision_trace_v1_to_v2.json
runs/generalization/<scenario>/revision/gate_decision.json
```

## Old “Editable Memory” Equivalent

In this project, editable memory should not mean chat memory. It maps to:

- capability ledger
- Skill Package files
- repair policy
- trace policy
- verifier contract

## Old “Trajectory Tracking” Equivalent

It maps to:

- source trace
- execution trace
- feedback trace
- revision trace

## Why Vulnerability Traces Are Harder

Security tasks often require cross-file evidence, business context, dynamic reachability, exploitability judgment, and false-positive control. Some vulnerabilities cannot be verified from static snippets alone.

## Automatically Recordable Now

- file reads
- target asset paths
- findings
- evidence_span
- verifier feedback
- repair action
- gate decision
- Skill diff metadata

## Not Reliably Automatic Yet

- real exploit path
- attack reachability
- business authorization semantics
- chained vulnerability proof
- production exploitability

## UI Proposal

Start with a four-column table:

| Source | Execution | Feedback | Revision |
|---|---|---|---|
| expert span / capability | finding / evidence_span | feedback type / score | repair action / gate |

Do not start with a dense graph. The graph can be generated later from the same trace schema.
