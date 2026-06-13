# Skill Diff: advanced_config_holdout_realization_001

## Evidence Binding

- Solves failure / limitation: `config realization must stay environment-aware on holdout cases`
- Modified capability group: `config_security`
- Changes out_of_scope_guard: `False`
- Scope expansion risk: `low`
- Held-out/negative risk case: `holdout_clean_tax_math_001`

## Why Scope Should Not Expand

Promotion is forbidden unless validation shows strict gain, no false-positive increase, no schema regression, and no scope violation.

## Diff

```diff
--- active_installed_SKILL.md
+++ advanced_config_holdout_realization_001_SKILL.md
@@ -45,3 +45,7 @@
 - `capability_id`
 - `evidence_span`
 - `recommended_fix`
+
+## Advanced Candidate Constraint: config holdout realization
+
+- Keep CONFIG_AUDIT_EXPORT and CONFIG_ENV_GUARD evidence grounded in prod/dev environment boundaries on holdout cases.
```
