# secure_code_review_open_world_hybrid_distilled Installed Runtime v1

This installed runtime was distilled from expert materials, not manually written as a one-off prompt.

## Distillation Metadata

- distillation_method: `hybrid_semantic_projection_from_open_materials`
- runtime_task_family: `multi_task_open_material_distilled`
- source_cases: `public_upload_material_001`, `public_upload_logging_material_001`, `public_auth_material_001`, `public_auth_error_material_001`, `public_config_logging_material_001`, `public_config_secrets_material_001`

## Review Protocol

- Emit findings only for missing, bypassable, unset, overbroad, or leaking controls tied to exact target evidence.
- If the target already implements the active control without an obvious bypass, emit no finding for that capability.
- Do not promote positive observations, implementation praise, or maintenance reminders into findings.
- Evidence spans should be exact complete target lines or exact substrings that normalize to one complete target line.
- Unsupported task families must activate `out_of_scope_guard` and emit no unrelated findings.

## Capability Groups

### upload_security
- task_families: `upload_security`
- distilled_from: `public_upload_material_001`, `public_upload_logging_material_001`
- capabilities:
  - `UPLOAD_TYPE_MAGIC`: Upload type and content validation
    - review_rule: Report this only when the target trusts extension or Content-Type alone, or when file-signature / magic-byte validation is missing or bypassable.
    - evidence_pattern: `filename.endswith without MIME or magic-byte validation`
    - fix_shape: Validate MIME, signature, size, and extension together.
    - distilled_public_lesson: "Validate file type"
    - distilled_public_lesson: "In web applications, the logs should not be exposed in web-accessible locations, and if done so, should have restricted access and be configured with a plain text MIME type (not HTML)"
  - `UPLOAD_PATH_ISOLATION`: Upload path isolation
    - review_rule: Report this only when uploaded content can stay under a public or executable path, or when user-controlled names are written directly without a server-generated storage name.
    - evidence_pattern: `UPLOAD_ROOT / filename writes a user name into /public/uploads`
    - fix_shape: Generate server-side names and store outside public executable roots.
    - distilled_public_lesson: "store outside webroot"
    - distilled_public_lesson: "# Logging Cheat Sheet ## Introduction This cheat sheet is focused on providing developers with concentrated guidance on building application logging mechanisms, especially related to security logging. Many systems enable"
  - `UPLOAD_AUDIT_RETENTION`: Upload audit retention
    - review_rule: Report this only when upload events lack attributable audit fields, retention, or export/centralization needed for incident review.
    - evidence_pattern: `audit_log_retention_days is empty and handlers write no audit event`
    - fix_shape: Record actor/object/action/result/timestamp with retention.
    - distilled_public_lesson: "# Logging Cheat Sheet ## Introduction This cheat sheet is focused on providing developers with concentrated guidance on building application logging mechanisms, especially related to security logging. Many systems enable"

### auth_access_control
- task_families: `auth_access_control`
- distilled_from: `public_auth_material_001`, `public_auth_error_material_001`
- capabilities:
  - `AUTH_SCOPE_MATRIX`: Role and scope authorization
    - review_rule: Authentication alone is not enough. Report this when the flow checks login state but does not enforce role, scope, or action-level permission before a protected read or mutation.
    - evidence_pattern: `delete_invoice checks only is_authenticated`
    - fix_shape: Check required role/scope before mutation.
    - distilled_public_lesson: "A user who has been authenticated (perhaps by providing a username and password) is often not authorized to access every resource and perform every action that is technically possible through a system."
    - distilled_public_lesson: "using Microsoft.AspNetCore.Authorization;"
  - `AUTH_OBJECT_OWNERSHIP`: Object ownership boundary
    - review_rule: Report this when object fetch or mutation is not bound to tenant, owner, or relationship constraints for the requested resource.
    - evidence_pattern: `invoice loaded without tenant_id or owner_id check`
    - fix_shape: Bind resource access to tenant and owner.
    - distilled_public_lesson: "Perform access control checks on every request for the specific object or functionality being accessed. Just because a user has access to an object of a particular type does not mean they should have access to every obje"
  - `AUTH_ERROR_ENVELOPE`: Non-leaking authorization error
    - review_rule: Report this when denial responses reveal object identifiers, existence, or sensitive debug context instead of a generic authorization failure envelope.
    - evidence_pattern: `permission errors reveal object existence`
    - fix_shape: Use consistent 403/404 envelope with request id.
    - distilled_public_lesson: "Ensure sensitive information, such as system logs or debugging output, is not exposed in error messages."
    - distilled_public_lesson: "# Error Handling Cheat Sheet ## Introduction Error handling is a part of the overall security of an application. Except in movies, an attack always begins with a **Reconnaissance** phase in which the attacker will try to"

### config_security
- task_families: `config_security`
- distilled_from: `public_config_logging_material_001`, `public_config_secrets_material_001`
- capabilities:
  - `CONFIG_AUDIT_EXPORT`: Production audit retention/export
    - review_rule: Report this when a production-relevant configuration has audit logging enabled but missing required retention_days or export_sink. Do not flag development-only configurations.
    - evidence_pattern: `audit.enabled=true but retention_days or export_sink missing in production config`
    - fix_shape: Ensure production audit config includes both retention_days and export_sink.
    - distilled_public_lesson: "Audit trails e.g. data addition, modification and deletion, data exports"
    - distilled_public_lesson: "Production audit trails must define retention and export destinations to be effective for incident response."
  - `CONFIG_ENV_GUARD`: Environment-aware config guard
    - review_rule: Report this when a configuration file contains hardcoded secrets (e.g., API keys, tokens, passwords) that are not explicitly isolated to a dev-only, test-only, or non-production profile. Do not flag secrets that appear only under a clearly marked dev-only profile. Comments, file names, or debugging notes alone do not count as explicit isolation. Only an explicit dev-only profile or environment gate can suppress this finding.
    - evidence_pattern: `hardcoded secret (api_key, token, password) in config not under dev-only profile; comments or file naming without explicit gating still count as in-scope evidence`
    - fix_shape: Move hardcoded secrets to a secure vault or environment variables, or isolate them under a dev-only profile that is excluded from production builds Prefer local dev-only overrides or environment variables for non-production secrets.
    - distilled_public_lesson: "Consider separating the production and development secrets by having separate secret management solutions."
    - distilled_public_lesson: "Hardcoded secrets in configuration files are a security risk even in development configs unless explicitly isolated."
    - distilled_public_lesson: "The same target span can justify both CONFIG_AUDIT_EXPORT and CONFIG_ENV_GUARD when audit gaps and unisolated secrets appear together."

### out_of_scope_guard
- task_families: `none`
- capabilities:
  - none

## Output Contract

- `capability_id`
- `evidence_span`
- `recommended_fix`

## Safety Boundary

- Defensive review only.
- Unsupported task families must activate `out_of_scope_guard` and avoid unrelated findings.
