# AgentHost Qualification

Date: 2026-06-23

```text
agent_host_binary = pass
bounded_bundle_materialization = pass
agent_host_execution = fail_timeout
agent_host_qualification = hard_blocked_provider_protocol
agent_host_effectiveness = not_evaluated
```

Codex CLI `0.137.0` is installed. On this PowerShell host, invoking `codex` resolves first
to an execution-policy-blocked npm `codex.ps1`; the explicit executable
`%APPDATA%\npm\codex.cmd` works and is the qualified path. This shell detail is not the
remaining research blocker.

The bounded adapter materialized `SKILL.md`, `task.json`, and a strict JSON output schema
from Judge-passed Bundle
`sha256:d2efd9f98fef4773a3e86ec3cef50aefe7ff67057f0cb8f7218f76eea836ae4e`.

Fresh bounded command:

```powershell
eskill --state-dir .tmp/judge-pass-state qualify-agent-host `
  --executable "$env:APPDATA\npm\codex.cmd" `
  --task-id codex-agent-host-qualification-classified --timeout 20
```

Recorded runtime envelope:

```text
status = timeout
qualification_status = fail
reason_codes = HOST_TIMEOUT
artifact = sha256:79c2b1e05affa86d127aa27c41363d51bde51803c4bb5428a9fcd8b06d66c913
```

## Exact provider blocker

The available project credential is for DeepSeek's OpenAI-compatible Chat Completions
interface. A fresh Codex provider probe using `wire_api="chat"` fails before task execution:

```text
Error: `wire_api = "chat"` is no longer supported.
How to fix: set `wire_api = "responses"` in your provider config.
```

Codex 0.137 therefore cannot be pointed directly at this Chat Completions endpoint through
its supported provider protocol. Earlier default-provider runs also showed failed OpenAI
WebSocket/HTTPS access and then timed out. The project does not insert an unverified local
Responses proxy merely to manufacture a pass.

No ReferenceDecisionBackend result is counted as AgentHost evidence. Hidden gold was not
materialized into the bounded task package. Agent effectiveness and condition-sensitive
downstream comparison remain unclaimed until a reachable Responses-compatible provider or
another qualified mature AgentHost is available.
