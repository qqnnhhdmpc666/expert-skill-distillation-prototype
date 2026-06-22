# AgentHost Qualification

Date: 2026-06-23

```text
agent_host_binary = pass
bounded_bundle_materialization = pass
agent_host_execution = timeout
agent_host_qualification = hard_blocked
agent_host_effectiveness = not_evaluated
```

Codex CLI `0.137.0` is installed and exposes the required `exec`, read-only sandbox,
output-schema, and ephemeral-session controls. The qualified input was the immutable
Judge-passed Bundle `sha256:d2efd9f98fef4773a3e86ec3cef50aefe7ff67057f0cb8f7218f76eea836ae4e`.

Fresh bounded command:

```powershell
eskill --state-dir .tmp/judge-pass-state qualify-agent-host `
  --executable "$env:APPDATA\npm\codex.cmd" `
  --task-id codex-agent-host-qualification-classified --timeout 20
```

The adapter materialized `SKILL.md`, `task.json`, and a strict JSON output schema, then
terminated without a schema-valid Agent result. Recorded result:

```text
status = timeout
qualification_status = fail
reason_codes = HOST_TIMEOUT
artifact = sha256:79c2b1e05affa86d127aa27c41363d51bde51803c4bb5428a9fcd8b06d66c913
```

Earlier restricted-network output explicitly showed failed WebSocket/HTTPS connections.
An approved host-context retry did not create a result artifact within its bound and was
terminated. Neither attempt is counted as partial qualification. Agent effectiveness and
condition-sensitive comparison remain unclaimed.
