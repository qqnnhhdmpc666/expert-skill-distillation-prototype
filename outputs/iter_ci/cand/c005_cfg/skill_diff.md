# Skill Diff: c005_cfg

Targeted change: Config Audit Precision.

## Evidence Binding

- Generated from failure rows, verifier feedback, evidence summaries, and normalization traces.
- Does not read verifier-only expected findings, expected evidence spans, or clean labels.
- Does not add dependency/version-risk, regex DoS, or server-side execution review to core scope.

## Candidate Patch

```diff
--- active_SKILL.md
+++ c005_cfg_SKILL.md
@@ -45,3 +45,12 @@
 - `capability_id`
 - `evidence_span`
 - `recommended_fix`
+
+## Iterative Contract Candidate: Config Audit Precision
+
+For `config_security`, keep audit export and environment guard distinct:
+
+- Emit `CONFIG_AUDIT_EXPORT` when audit is enabled but retention duration, export sink, or reviewable audit destination is empty or missing.
+- Emit `CONFIG_ENV_GUARD` only when a prod/release profile exposes secrets or a dev-only token is not clearly fenced to a development profile.
+
+A dev-only token that is explicitly marked dev-only is not itself a production config finding. Do not add dependency/version-risk review to this skill.
```
