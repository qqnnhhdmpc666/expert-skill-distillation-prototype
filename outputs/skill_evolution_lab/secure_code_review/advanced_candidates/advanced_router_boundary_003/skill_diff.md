# Skill Diff: advanced_router_boundary_003

## Evidence Binding

- Solves failure / limitation: `ablation mechanism_status=supports_mechanism; guard out-of-scope routing against always-on capability variants`
- Modified capability group: `out_of_scope_guard`
- Changes out_of_scope_guard: `True`
- Scope expansion risk: `medium`
- Held-out/negative risk case: `holdout_clean_tax_math_001`

## Why Scope Should Not Expand

Promotion is forbidden unless validation shows strict gain, no false-positive increase, no schema regression, and no scope violation.

## Diff

```diff
--- active_installed_SKILL.md
+++ advanced_router_boundary_003_SKILL.md
@@ -45,3 +45,7 @@
 - `capability_id`
 - `evidence_span`
 - `recommended_fix`
+
+## Advanced Candidate Constraint: task router boundary
+
+- Preserve out_of_scope_guard for clean business-logic tasks and avoid always-on security findings.
```
