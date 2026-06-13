# Skill Diff: advanced_dependency_scope_expansion_004

## Evidence Binding

- Solves failure / limitation: `unsupported limitation retained=retained; dependency audit remains out of core scope`
- Modified capability group: `dependency_version_risk`
- Changes out_of_scope_guard: `False`
- Scope expansion risk: `high`
- Held-out/negative risk case: `holdout_dependency_no_advisory_001`

## Why Scope Should Not Expand

Promotion is forbidden unless validation shows strict gain, no false-positive increase, no schema regression, and no scope violation.

## Diff

```diff
--- active_installed_SKILL.md
+++ advanced_dependency_scope_expansion_004_SKILL.md
@@ -45,3 +45,7 @@
 - `capability_id`
 - `evidence_span`
 - `recommended_fix`
+
+## Advanced Candidate Constraint: unsupported dependency expansion
+
+- This candidate intentionally tests adding dependency audit and should be rejected if it expands secure_code_review scope.
```
