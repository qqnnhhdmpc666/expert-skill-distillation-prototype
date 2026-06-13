# Skill Diff: dependency_version_risk__v3_candidate_003

## Evidence Binding

- Source type: `limitation_summary`
- Source case: `mini_dependency_version_risk_001`
- Failure or limitation: `dependency/version risk is unsupported and must remain outside secure_code_review core capability`

## Scope Analysis

- Capability group changed: `dependency_version_risk`
- Scope expansion risk: `high`
- Held-out or negative risk case: `mini_dependency_version_risk_001`

## Unified Diff

```diff
--- active_installed_SKILL.md
+++ v3_dependency_scope_expansion_candidate_SKILL.md
@@ -45,3 +45,9 @@
 - `capability_id`
 - `evidence_span`
 - `recommended_fix`
+
+## Candidate Constraint: unsupported dependency expansion
+
+- Evidence-bound rationale: Dependency/version-risk mini-suite evidence is intentionally a limitation; this candidate tests whether unsupported expansion is rejected.
+- Scope note: Adding dependency audit to secure_code_review core scope is not allowed in this sprint.
+- Promotion requires strict score gain, no false-positive increase, no schema-error increase, and no scope violation.
```
