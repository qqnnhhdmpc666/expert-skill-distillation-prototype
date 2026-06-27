# D1 Baseline Expert Material: Missing Use-Site Gate

The workflow checks dependency declaration, resolved version, and advisory
affected range before deciding dependency-use triage.

This material is intentionally incomplete: it does not state that an actual
repository import/use-site is required before deciding
`dependency_used_and_affected`.

## Distilled Revision v1: use-site evidence gate

Before deciding dependency_used_and_affected, the runtime must require:
1. dependency declaration evidence
2. resolved version evidence
3. import/use-site evidence
4. advisory affected range evidence
5. decision evidence

If import/use evidence is missing, the decision must be dependency_present_not_used or unresolved, never dependency_used_and_affected.

This revision is a general dependency-use triage rule. It is not a patch for a specific task answer.
