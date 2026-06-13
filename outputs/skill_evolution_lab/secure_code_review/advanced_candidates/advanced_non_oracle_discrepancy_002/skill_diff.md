# Skill Diff: advanced_non_oracle_discrepancy_002

## Evidence Binding

- Solves failure / limitation: `non_oracle_completed_rows=6; preserve schema grounding under non-oracle backend`
- Modified capability group: `api_or_code_review`
- Changes out_of_scope_guard: `False`
- Scope expansion risk: `low`
- Held-out/negative risk case: `holdout_clean_tax_math_001`

## Why Scope Should Not Expand

Promotion is forbidden unless validation shows strict gain, no false-positive increase, no schema regression, and no scope violation.

## Diff

```diff
--- active_installed_SKILL.md
+++ advanced_non_oracle_discrepancy_002_SKILL.md
@@ -45,3 +45,7 @@
 - `capability_id`
 - `evidence_span`
 - `recommended_fix`
+
+## Advanced Candidate Constraint: non-oracle schema grounding
+
+- Require API findings to keep structured evidence spans under non-oracle local semantic execution.
```
