--- open_world_v2_SKILL.md
+++ open_world_v3_candidate_auth_scope.md
@@ -91,3 +91,15 @@
 
 - Defensive review only.
 - Unsupported task families must activate `out_of_scope_guard` and avoid unrelated findings.
+
+## Open-World Closed-Loop Candidate
+
+This candidate is generated from the remaining bounded open-world failure rows.
+Keep dependency/version-risk, regex DoS, and server-side execution review out of scope.
+
+### Config Security Completion
+
+- Emit `CONFIG_AUDIT_EXPORT` when a production-facing audit block is enabled but `retention_days`, `export_sink`, or equivalent review destination is empty or missing.
+- Emit `CONFIG_ENV_GUARD` when a configuration file contains hardcoded API keys, session secrets, credentials, or debug-style defaults that should not live in committed application config.
+- Hardcoded secrets remain concrete findings even if a file is named `development` when the committed config is still reachable, shared, or treated as an application default in the target task.
+- Do not suppress concrete hardcoded-secret evidence as merely contextual noise.
