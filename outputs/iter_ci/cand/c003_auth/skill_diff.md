# Skill Diff: c003_auth

Targeted change: Auth Scope Matrix Precision.

## Evidence Binding

- Generated from failure rows, verifier feedback, evidence summaries, and normalization traces.
- Does not read verifier-only expected findings, expected evidence spans, or clean labels.
- Does not add dependency/version-risk, regex DoS, or server-side execution review to core scope.

## Candidate Patch

```diff
--- active_SKILL.md
+++ c003_auth_SKILL.md
@@ -45,3 +45,13 @@
 - `capability_id`
 - `evidence_span`
 - `recommended_fix`
+
+## Iterative Contract Candidate: Auth Scope Matrix Precision
+
+For `auth_access_control`, evaluate the three auth capabilities separately:
+
+- Emit `AUTH_SCOPE_MATRIX` when the target only checks authentication, but does not bind the operation to a role, scope, tenant, or permission matrix.
+- Emit `AUTH_OBJECT_OWNERSHIP` when an object is loaded by id without tenant_id, owner_id, account_id, or equivalent ownership filtering.
+- Emit `AUTH_ERROR_ENVELOPE` when denial or error output includes stable object identifiers or business ids instead of a neutral request id.
+
+Do not apply this rule to clean targets that already include required role scope, tenant/owner filtering, and request-id-only denial output. Do not expand into dependency, regex, or server-side execution review.
```
