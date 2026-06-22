# Public Validation and Agent Usability Status

Date: 2026-06-23

| Track | Status | Real evidence | Remaining gap |
|---|---|---|---|
| Independent DeepSeek Judge | pass | authenticated blind response; formal build attestation pass | rotate chat-exposed credential |
| Codex AgentHost | hard_blocked | real bounded invocation ended as `HOST_TIMEOUT` | reachable authenticated CLI execution |
| Harbor public OSV parity | infra_blocked | native 21/21 fresh run; two Harbor task adapters prepared | WSL distribution became unavailable before Harbor execution |
| Public OSV pilot v2 | pass_reference_runtime | 33/33, false-safe 0, frozen public records | mature non-reference Agent execution |
| Compiler vs Direct | prepared_but_blocked | seven held-out cases and all artifact digests frozen | direct/compiler artifacts are identical; AgentHost unavailable |

## Conservative conclusion

The public deterministic runtime line is substantially stronger and the Independent Judge
is now real. Agent usability and Compiler improvement are not yet demonstrated. In
particular, identical direct/compiler artifacts prohibit a version-benefit claim even before
the AgentHost blocker is removed.
