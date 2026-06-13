# demo_material_skill Installed Runtime v1

This installed runtime was distilled from expert materials, not manually written as a one-off prompt.

## Distillation Metadata

- distillation_method: `keyword_projection_from_user_or_public_materials`
- runtime_task_family: `multi_task_open_material_distilled`
- source_cases: `upload_guidance_demo`, `auth_guidance_demo`, `config_guidance_demo`

## Review Protocol

- Emit findings only for missing, bypassable, unset, overbroad, or leaking controls tied to exact target evidence.
- If the target already implements the active control without an obvious bypass, emit no finding for that capability.
- Do not promote positive observations, implementation praise, or maintenance reminders into findings.
- Evidence spans should be exact complete target lines or exact substrings that normalize to one complete target line.
- Unsupported task families must activate `out_of_scope_guard` and emit no unrelated findings.

## Capability Groups

### upload_security
- task_families: `upload_security`
- distilled_from: `upload_guidance_demo`
- capabilities:
  - `UPLOAD_TYPE_MAGIC`: Upload type and content validation
    - review_rule: Report this only when the target trusts extension or Content-Type alone, or when file-signature / magic-byte validation is missing or bypassable.
    - evidence_pattern: `filename.endswith without MIME or magic-byte validation`
    - fix_shape: Validate MIME, signature, size, and extension together.
    - distilled_public_lesson: "Validate file type with signature or magic-byte checks, do not trust extension alone, store uploads outside the web root, and keep attributable audit logs for upload actions."
  - `UPLOAD_PATH_ISOLATION`: Upload path isolation
    - review_rule: Report this only when uploaded content can stay under a public or executable path, or when user-controlled names are written directly without a server-generated storage name.
    - evidence_pattern: `UPLOAD_ROOT / filename writes a user name into /public/uploads`
    - fix_shape: Generate server-side names and store outside public executable roots.
    - distilled_public_lesson: "Validate file type with signature or magic-byte checks, do not trust extension alone, store uploads outside the web root, and keep attributable audit logs for upload actions."
  - `UPLOAD_AUDIT_RETENTION`: Upload audit retention
    - review_rule: Report this only when upload events lack attributable audit fields, retention, or export/centralization needed for incident review.
    - evidence_pattern: `audit_log_retention_days is empty and handlers write no audit event`
    - fix_shape: Record actor/object/action/result/timestamp with retention.
    - distilled_public_lesson: "Validate file type with signature or magic-byte checks, do not trust extension alone, store uploads outside the web root, and keep attributable audit logs for upload actions."

### auth_access_control
- task_families: `auth_access_control`
- distilled_from: `auth_guidance_demo`
- capabilities:
  - `AUTH_SCOPE_MATRIX`: Role and scope authorization
    - review_rule: Authentication alone is not enough. Report this when the flow checks login state but does not enforce role, scope, or action-level permission before a protected read or mutation.
    - evidence_pattern: `delete_invoice checks only is_authenticated`
    - fix_shape: Check required role/scope before mutation.
    - distilled_public_lesson: "Enforce authorization on every protected request, bind objects to owner or tenant scope, and avoid denial responses that leak object identifiers or sensitive debug detail."
  - `AUTH_OBJECT_OWNERSHIP`: Object ownership boundary
    - review_rule: Report this when object fetch or mutation is not bound to tenant, owner, or relationship constraints for the requested resource.
    - evidence_pattern: `invoice loaded without tenant_id or owner_id check`
    - fix_shape: Bind resource access to tenant and owner.
    - distilled_public_lesson: "Enforce authorization on every protected request, bind objects to owner or tenant scope, and avoid denial responses that leak object identifiers or sensitive debug detail."

### config_security
- task_families: `config_security`
- distilled_from: `config_guidance_demo`
- capabilities:
  - `CONFIG_AUDIT_EXPORT`: Production audit retention/export
    - review_rule: Report this when production-facing audit configuration lacks retention, export sink, or sufficient event detail for review and incident response.
    - evidence_pattern: `prod.audit enabled but retention_days/export_sink missing`
    - fix_shape: Require retention and export sink for production audit logs.
    - distilled_public_lesson: "Production-facing configuration should not include hardcoded secrets or dev/test assumptions, and audit exports should preserve enough detail for incident review."
  - `CONFIG_ENV_GUARD`: Environment-aware config guard
    - review_rule: Report this when production-relevant config contains hardcoded secrets, debug-style defaults, or dev/test assumptions that should be isolated from production paths.
    - evidence_pattern: `dev api_token/debug should not be production findings`
    - fix_shape: Bind findings to prod/dev/test path before flagging.
    - distilled_public_lesson: "Production-facing configuration should not include hardcoded secrets or dev/test assumptions, and audit exports should preserve enough detail for incident review."

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
