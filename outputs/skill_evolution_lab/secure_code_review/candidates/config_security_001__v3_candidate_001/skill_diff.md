# Skill Diff: config_security_001__v3_candidate_001

## Evidence Binding

- Source type: `verifier_feedback_and_evidence_summary`
- Source case: `config_security_001`
- Failure or limitation: `configuration realization can regress to capability presence without explicit evidence realization`

## Scope Analysis

- Capability group changed: `config_security`
- Scope expansion risk: `low`
- Held-out or negative risk case: `mini_clean_out_of_scope_001`

## Unified Diff

```diff
--- active_installed_SKILL.md
+++ v3_config_realization_candidate_SKILL.md
@@ -45,3 +45,9 @@
 - `capability_id`
 - `evidence_span`
 - `recommended_fix`
+
+## Candidate Constraint: config realization constraint
+
+- Evidence-bound rationale: Mini-suite and internal evidence require config findings to express environment-aware audit/export reasoning without broadening scope.
+- Scope note: No new task family is added; only config_security wording is constrained.
+- Promotion requires strict score gain, no false-positive increase, no schema-error increase, and no scope violation.
```
