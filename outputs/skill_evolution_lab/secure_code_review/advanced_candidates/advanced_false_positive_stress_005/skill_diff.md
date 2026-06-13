# Skill Diff: advanced_false_positive_stress_005

## Evidence Binding

- Solves failure / limitation: `clean negative must not be routed into upload_security`
- Modified capability group: `upload_security`
- Changes out_of_scope_guard: `False`
- Scope expansion risk: `high`
- Held-out/negative risk case: `holdout_clean_tax_math_001`

## Why Scope Should Not Expand

Promotion is forbidden unless validation shows strict gain, no false-positive increase, no schema regression, and no scope violation.

## Diff

```diff
--- active_installed_SKILL.md
+++ advanced_false_positive_stress_005_SKILL.md
@@ -45,3 +45,7 @@
 - `capability_id`
 - `evidence_span`
 - `recommended_fix`
+
+## Advanced Candidate Constraint: false-positive stress
+
+- This candidate intentionally maps clean tasks into upload scope and should be rejected by scope checks.
```
