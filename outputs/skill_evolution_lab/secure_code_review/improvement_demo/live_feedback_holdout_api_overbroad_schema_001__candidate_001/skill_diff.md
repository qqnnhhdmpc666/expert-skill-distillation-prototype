# Skill Diff: live_feedback_holdout_api_overbroad_schema_001__candidate_001

## Evidence Binding

- Solves live failure / discrepancy from: `holdout_api_overbroad_schema_001`
- Live feedback: `unsupported_evidence`
- Scope expansion: `forbidden`
- Risk controls: clean negative and unsupported limitation must not regress.

```diff
--- active_installed_SKILL.md
+++ live_feedback_holdout_api_overbroad_schema_001__candidate_001_SKILL.md
@@ -45,3 +45,10 @@
 - `capability_id`
 - `evidence_span`
 - `recommended_fix`
+
+## Improvement Demo Candidate: live-feedback repair
+
+- Source case: `holdout_api_overbroad_schema_001`.
+- Live feedback type: `unsupported_evidence`.
+- Repair lesson: Quote or tightly paraphrase exact target lines in evidence_span; do not cite generic risk labels.
+- Do not expand secure_code_review scope; dependency/version-risk remains out of scope.
```
