# AgentHost Route Decision

Date: 2026-06-23

```text
agent_host_route_decision = no_compatible_mature_host_available
agent_host_qualification = hard_blocked_no_compatible_mature_host
heldout_compiler_vs_direct = not_run_agenthost_unavailable
```

## Route comparison

| Route | Requirements | Observed status | Risk | Implementation effort | Qualifies as mature AgentHost evidence? | Next command |
|---|---|---|---|---|---|---|
| Codex + current DeepSeek Chat Completions | Codex provider accepting `wire_api="chat"` | Codex 0.137 rejects `wire_api="chat"` before task execution | Unsupported protocol; cannot execute | Low to probe, not viable | No | None until provider or Codex protocol changes |
| Codex + Responses-compatible provider | Valid OpenAI/Responses-compatible credential and reachable endpoint | Bounded smoke consumed Bundle artifact but failed: websocket 403, HTTP fallback invalid-key 401 | Real host path exists, but current endpoint/credential not usable | Low after valid credential | Yes, if it returns schema-valid output | `eskill --state-dir .tmp\judge-pass-state qualify-agent-host --executable "$env:APPDATA\npm\codex.cmd" --task-id codex-agent-host-qualification --timeout 90` |
| OpenHands + current provider | Installed OpenHands CLI/runtime and Chat Completions provider support | `openhands` command not installed locally | New host installation and contract adapter required | Medium | Potentially, only after bounded adapter and hidden-gold checks | Install/qualify OpenHands, then implement adapter |
| Local Responses proxy | Verified proxy translating Responses protocol to DeepSeek Chat Completions without semantic loss | Not implemented and deliberately not used | High risk of manufacturing evidence; protocol semantics may drift | Medium to high | No, unless independently specified and qualified as host infrastructure | Deferred |

## Fresh evidence

Codex binary:

```text
codex-cli 0.137.0
```

DeepSeek Chat probe:

```text
Error: `wire_api = "chat"` is no longer supported.
How to fix: set `wire_api = "responses"` in your provider config.
```

Default Responses smoke:

```text
artifact = sha256:6e8483d5a2d2572b385800e3bf153d77f0f34f6c8c5809e8383b40f2bc539f5a
bundle_digest = sha256:d2efd9f98fef4773a3e86ec3cef50aefe7ff67057f0cb8f7218f76eea836ae4e
agent_artifact_digest = sha256:b1e0d32349fe46049d4655d89c87e425d593bdf4a54bf4aee5efea83853cbbdb
exit_code = 1
reason_codes = CODEX_AUTH_OR_NETWORK_BLOCKED
```

The bounded task package did not contain hidden gold. No ReferenceDecisionBackend output is counted as AgentHost evidence.

## Decision

Do not continue trying DeepSeek Chat Completions directly with Codex 0.137. The next viable path is either:

1. provide a valid Responses-compatible provider credential for Codex; or
2. install and qualify a mature host that natively supports the current Chat Completions provider.

Until then:

```text
compiler_superiority = prepared_condition_sensitive_eval_no_agenthost
agent_effectiveness = not_evaluated
```
