# Skill Diff: clean_false_positive_guard__v3_candidate_002

## Evidence Binding

- Source type: `negative_control_evidence_summary`
- Source case: `mini_clean_out_of_scope_001`
- Failure or limitation: `false-positive control must remain zero on clean out-of-scope tasks`

## Scope Analysis

- Capability group changed: `upload_security`
- Scope expansion risk: `high`
- Held-out or negative risk case: `mini_clean_out_of_scope_001`

## Unified Diff

```diff
--- active_installed_SKILL.md
+++ v3_false_positive_stress_candidate_SKILL.md
@@ -45,3 +45,9 @@
 - `capability_id`
 - `evidence_span`
 - `recommended_fix`
+
+## Candidate Constraint: false-positive stress scope expansion
+
+- Evidence-bound rationale: Stress test candidate intentionally maps a clean out-of-scope task to upload_security to verify rejection/quarantine logic.
+- Scope note: This is expected to be rejected if it introduces false positives or scope violation.
+- Promotion requires strict score gain, no false-positive increase, no schema-error increase, and no scope violation.
```
