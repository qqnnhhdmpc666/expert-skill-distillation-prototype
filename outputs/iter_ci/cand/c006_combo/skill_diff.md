# Skill Diff: c006_combo

Targeted change: Composed Low-Scope Contract Patch.

## Evidence Binding

- Generated from failure rows, verifier feedback, evidence summaries, and normalization traces.
- Does not read verifier-only expected findings, expected evidence spans, or clean labels.
- Does not add dependency/version-risk, regex DoS, or server-side execution review to core scope.

## Candidate Patch

```diff
--- active_SKILL.md
+++ c006_combo_SKILL.md
@@ -45,3 +45,13 @@
 - `capability_id`
 - `evidence_span`
 - `recommended_fix`
+
+## Iterative Contract Candidate: Composed Low-Scope Contract Patch
+
+Apply the following narrow live-output discipline:
+
+1. Positive observations are notes, not findings. Existing checks, generated filenames, configured retention, tenant/owner filters, role scopes, and request-id denial envelopes should not be reported as problems.
+2. Auth findings must be separated into `AUTH_SCOPE_MATRIX`, `AUTH_OBJECT_OWNERSHIP`, and `AUTH_ERROR_ENVELOPE` only when exact target lines support each one.
+3. API findings must distinguish missing structured output fields from overbroad risk labels. Future or hypothetical debug notes without route/schema/caller evidence should produce no concrete finding.
+4. Config findings must distinguish missing audit export/retention from environment profile guard issues. Dev-only tokens are not production findings when they are explicitly fenced.
+5. Unsupported dependency/version, regex DoS, and server-side execution review remain out of scope for `secure_code_review`.
```
