# secure_code_review_open_world_distilled Installed Runtime v2

This installed runtime was distilled from expert materials, not manually written as a one-off prompt.

## Distillation Metadata

- distillation_method: `keyword_projection_from_open_materials`
- runtime_task_family: `multi_task_open_material_distilled`
- source_cases: `public_upload_material_001`, `public_upload_logging_material_001`, `public_auth_material_001`, `public_config_material_001`

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
    - distilled_public_lesson: "# File Upload Cheat Sheet ## Introduction File upload is becoming a more and more essential part of any application, where the user is able to upload their photo, their CV, or a video showcasing a project they are workin"
    - distilled_public_lesson: "In web applications, the logs should not be exposed in web-accessible locations, and if done so, should have restricted access and be configured with a plain text MIME type (not HTML)"
  - `UPLOAD_PATH_ISOLATION`: Upload path isolation
    - review_rule: Report this only when uploaded content can stay under a public or executable path, or when user-controlled names are written directly without a server-generated storage name.
    - evidence_pattern: `UPLOAD_ROOT / filename writes a user name into /public/uploads`
    - fix_shape: Generate server-side names and store outside public executable roots.
    - distilled_public_lesson: "# File Upload Cheat Sheet ## Introduction File upload is becoming a more and more essential part of any application, where the user is able to upload their photo, their CV, or a video showcasing a project they are workin"
    - distilled_public_lesson: "# Logging Cheat Sheet ## Introduction This cheat sheet is focused on providing developers with concentrated guidance on building application logging mechanisms, especially related to security logging. Many systems enable"
  - `UPLOAD_AUDIT_RETENTION`: Upload audit retention
    - review_rule: Report this only when upload events lack attributable audit fields, retention, or export/centralization needed for incident review.
    - evidence_pattern: `audit_log_retention_days is empty and handlers write no audit event`
    - fix_shape: Record actor/object/action/result/timestamp with retention.
    - distilled_public_lesson: "1. Store the files on a **different host**, which allows for complete segregation of duties between the application serving the user, and the host handling file uploads and their storage."
    - distilled_public_lesson: "# Logging Cheat Sheet ## Introduction This cheat sheet is focused on providing developers with concentrated guidance on building application logging mechanisms, especially related to security logging. Many systems enable"

### auth_access_control
- task_families: `auth_access_control`
- distilled_from: `public_auth_material_001`
- capabilities:
  - `AUTH_SCOPE_MATRIX`: Role and scope authorization
    - review_rule: Authentication alone is not enough. Report this when the flow checks login state but does not enforce role, scope, or action-level permission before a protected read or mutation.
    - evidence_pattern: `delete_invoice checks only is_authenticated`
    - fix_shape: Check required role/scope before mutation.
    - distilled_public_lesson: "# Authorization Cheat Sheet ## Introduction Authorization may be defined as "the process of verifying that a requested action or service is approved for a specific entity" ([NIST](https://csrc.nist.gov/glossary/term/auth"
  - `AUTH_OBJECT_OWNERSHIP`: Object ownership boundary
    - review_rule: Report this when object fetch or mutation is not bound to tenant, owner, or relationship constraints for the requested resource.
    - evidence_pattern: `invoice loaded without tenant_id or owner_id check`
    - fix_shape: Bind resource access to tenant and owner.
    - distilled_public_lesson: "# Authorization Cheat Sheet ## Introduction Authorization may be defined as "the process of verifying that a requested action or service is approved for a specific entity" ([NIST](https://csrc.nist.gov/glossary/term/auth"
  - `AUTH_ERROR_ENVELOPE`: Non-leaking authorization error
    - review_rule: Report this when denial responses reveal object identifiers, existence, or sensitive debug context instead of a generic authorization failure envelope.
    - evidence_pattern: `permission errors reveal object existence`
    - fix_shape: Use consistent 403/404 envelope with request id.
    - distilled_public_lesson: "# Authorization Cheat Sheet ## Introduction Authorization may be defined as "the process of verifying that a requested action or service is approved for a specific entity" ([NIST](https://csrc.nist.gov/glossary/term/auth"

### config_security
- task_families: `config_security`
- distilled_from: `public_config_material_001`
- capabilities:
  - `CONFIG_AUDIT_EXPORT`: Production audit retention/export
    - review_rule: Report this when production-facing audit configuration lacks retention, export sink, or sufficient event detail for review and incident response.
    - evidence_pattern: `prod.audit enabled but retention_days/export_sink missing`
    - fix_shape: Require retention and export sink for production audit logs.
    - distilled_public_lesson: "# Logging Cheat Sheet # Logging Cheat Sheet ## Introduction This cheat sheet is focused on providing developers with concentrated guidance on building application logging mechanisms, especially related to security loggin"
  - `CONFIG_ENV_GUARD`: Environment-aware config guard
    - review_rule: Report this when production-relevant config contains hardcoded secrets, debug-style defaults, or dev/test assumptions that should be isolated from production paths.
    - evidence_pattern: `dev api_token/debug should not be production findings`
    - fix_shape: Bind findings to prod/dev/test path before flagging.
    - distilled_public_lesson: "# Logging Cheat Sheet # Logging Cheat Sheet ## Introduction This cheat sheet is focused on providing developers with concentrated guidance on building application logging mechanisms, especially related to security loggin"

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

## Open-World Closed-Loop Candidate

This candidate is generated from the remaining bounded open-world failure rows.
Keep dependency/version-risk, regex DoS, and server-side execution review out of scope.

### Config Security Completion

- Emit `CONFIG_AUDIT_EXPORT` when a production-facing audit block is enabled but `retention_days`, `export_sink`, or equivalent review destination is empty or missing.
- Emit `CONFIG_ENV_GUARD` when a configuration file contains hardcoded API keys, session secrets, credentials, or debug-style defaults that should not live in committed application config.
- Hardcoded secrets remain concrete findings even if a file is named `development` when the committed config is still reachable, shared, or treated as an application default in the target task.
- Do not suppress concrete hardcoded-secret evidence as merely contextual noise.
