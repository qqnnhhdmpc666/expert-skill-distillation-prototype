# Skill Diff: c004_api

Targeted change: API Contract Precision.

## Evidence Binding

- Generated from failure rows, verifier feedback, evidence summaries, and normalization traces.
- Does not read verifier-only expected findings, expected evidence spans, or clean labels.
- Does not add dependency/version-risk, regex DoS, or server-side execution review to core scope.

## Candidate Patch

```diff
--- active_SKILL.md
+++ c004_api_SKILL.md
@@ -45,3 +45,12 @@
 - `capability_id`
 - `evidence_span`
 - `recommended_fix`
+
+## Iterative Contract Candidate: API Contract Precision
+
+For `api_or_code_review`, keep the two capabilities separate:
+
+- Emit `API_SCHEMA_CONTRACT` when the target says a report builder emits prose or otherwise lacks required structured fields such as `capability_id`, `evidence_span`, or `recommended_fix`.
+- Emit `API_OVERBROAD_RISK` when a risk label such as `debug_path` is asserted without a concrete target line, route, production caller, response field, or evidence span.
+
+If a note says something *might* happen in the future but no route, caller, response schema, production path, or emitted field is shown, do not emit a concrete finding. Use no findings or low-confidence notes.
```
