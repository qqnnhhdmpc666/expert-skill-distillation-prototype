# D2 Baseline Expert Material: Overgeneralized Affected Decision

The workflow treats a declared and used dependency with a known advisory as
affected without requiring a resolved-version comparison against the advisory
range.

This material is intentionally overgeneralized for the v1 diagnostic loop.

## Distilled Revision v1: use-site evidence gate

Before deciding dependency_used_and_affected, the runtime must require:
1. dependency declaration evidence
2. resolved version evidence
3. import/use-site evidence
4. advisory affected range evidence
5. decision evidence

If import/use evidence is missing, the decision must be dependency_present_not_used or unresolved, never dependency_used_and_affected.

This revision is a general dependency-use triage rule. It is not a patch for a specific task answer.
