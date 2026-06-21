# AgentHost Qualification

Date: 2026-06-21

```text
agent_host_qualification = hard_blocked_by_auth_or_network_with_contract_tests
```

## Fresh attempts

```powershell
eskill --state-dir .tmp/goal-evidence-state qualify-agent-host `
  --executable "$env:APPDATA\npm\codex.cmd" `
  --task-id codex-agent-host-qualification-2 --timeout 45
```

Codex CLI `0.137.0` was found and invoked unattended. The adapter materialized the immutable Bundle's Agent-compatible artifact, a bounded task file, and a strict output schema. The corrected invocation reached the provider path, retried WebSocket and HTTPS, then failed because `api.openai.com` was unreachable in the execution environment. Artifact:

```text
sha256:989f5794585df306bd1d3d0f284c0bd8aabb642492a10307a15547e0cdd4ade2
```

No `ExecutionTrace` with a completed Agent result was produced, so this is not `partial` qualification. OpenHands was not present on PATH. A local echo host was deliberately not counted.

## Contract coverage

- Bundle Agent artifact is the input, not an inline replacement Skill.
- Task evidence is frozen in `task.json`; the prompt forbids live retrieval.
- timeout and invalid output are separate host failures, never domain `unresolved`.
- command shape, Bundle digest, Agent artifact digest, elapsed time and stderr are recorded.
- focused contract tests cover missing binary and timeout.

## Remaining requirement

Provide an authenticated, reachable Codex or OpenHands runtime and rerun the command. Agent effectiveness remains unclaimed.
