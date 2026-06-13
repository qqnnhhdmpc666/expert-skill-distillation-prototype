from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CapabilitySpec:
    capability_id: str
    title: str
    evidence_hint: str
    fix_hint: str
    detector_needles: tuple[str, ...]


CAPABILITY_SPECS: dict[str, CapabilitySpec] = {
    "UPLOAD_TYPE_MAGIC": CapabilitySpec(
        capability_id="UPLOAD_TYPE_MAGIC",
        title="Upload type and content validation",
        evidence_hint="filename.endswith without MIME or magic-byte validation",
        fix_hint="Validate MIME, signature, size, and extension together.",
        detector_needles=("filename.endswith",),
    ),
    "UPLOAD_PATH_ISOLATION": CapabilitySpec(
        capability_id="UPLOAD_PATH_ISOLATION",
        title="Upload path isolation",
        evidence_hint="UPLOAD_ROOT / filename writes a user name into /public/uploads",
        fix_hint="Generate server-side names and store outside public executable roots.",
        detector_needles=("UPLOAD_ROOT / filename", "/public/uploads", "writes"),
    ),
    "UPLOAD_AUDIT_RETENTION": CapabilitySpec(
        capability_id="UPLOAD_AUDIT_RETENTION",
        title="Upload audit retention",
        evidence_hint="audit_log_retention_days is empty and handlers write no audit event",
        fix_hint="Record actor/object/action/result/timestamp with retention.",
        detector_needles=("audit_log_retention_days is empty", "audit_log_retention_days"),
    ),
    "AUTH_SCOPE_MATRIX": CapabilitySpec(
        capability_id="AUTH_SCOPE_MATRIX",
        title="Role and scope authorization",
        evidence_hint="delete_invoice checks only is_authenticated",
        fix_hint="Check required role/scope before mutation.",
        detector_needles=("checks is_authenticated", "is_authenticated"),
    ),
    "AUTH_OBJECT_OWNERSHIP": CapabilitySpec(
        capability_id="AUTH_OBJECT_OWNERSHIP",
        title="Object ownership boundary",
        evidence_hint="invoice loaded without tenant_id or owner_id check",
        fix_hint="Bind resource access to tenant and owner.",
        detector_needles=("loads invoice by id", "invoice by id"),
    ),
    "AUTH_ERROR_ENVELOPE": CapabilitySpec(
        capability_id="AUTH_ERROR_ENVELOPE",
        title="Non-leaking authorization error",
        evidence_hint="permission errors reveal object existence",
        fix_hint="Use consistent 403/404 envelope with request id.",
        detector_needles=("returns invoice_id", "invoice_id"),
    ),
    "CONFIG_AUDIT_EXPORT": CapabilitySpec(
        capability_id="CONFIG_AUDIT_EXPORT",
        title="Production audit retention/export",
        evidence_hint="prod.audit enabled but retention_days/export_sink missing",
        fix_hint="Require retention and export sink for production audit logs.",
        detector_needles=("retention_days/export_sink empty", "retention_days", "export_sink"),
    ),
    "CONFIG_ENV_GUARD": CapabilitySpec(
        capability_id="CONFIG_ENV_GUARD",
        title="Environment-aware config guard",
        evidence_hint="dev api_token/debug should not be production findings",
        fix_hint="Bind findings to prod/dev/test path before flagging.",
        detector_needles=("dev.api_token", "dev.debug", "dev-only"),
    ),
    "API_SCHEMA_CONTRACT": CapabilitySpec(
        capability_id="API_SCHEMA_CONTRACT",
        title="Strict report schema",
        evidence_hint="agent output omits evidence_span or uses free-form prose",
        fix_hint="Emit JSON findings with required evidence and fix fields.",
        detector_needles=("prior report used prose without evidence_span", "evidence_span"),
    ),
    "API_OVERBROAD_RISK": CapabilitySpec(
        capability_id="API_OVERBROAD_RISK",
        title="Overbroad finding control",
        evidence_hint="generic security risk without code/config evidence",
        fix_hint="Reject findings not grounded in target spans.",
        detector_needles=("returns debug_path", "debug_path"),
    ),
    "DATA_REQUIRED_FIELD_COVERAGE": CapabilitySpec(
        capability_id="DATA_REQUIRED_FIELD_COVERAGE",
        title="Required field coverage",
        evidence_hint="row 1042 has blank country_code in a required column",
        fix_hint="Enforce non-null checks and reject rows missing required fields.",
        detector_needles=("country_code=", "row 1042"),
    ),
    "DATA_TEMPORAL_SPLIT_GUARD": CapabilitySpec(
        capability_id="DATA_TEMPORAL_SPLIT_GUARD",
        title="Temporal split guard",
        evidence_hint="train.csv includes row 9811 dated after the validation cutoff",
        fix_hint="Bind split assignment to cutoff rules and quote offending row ids.",
        detector_needles=("row 9811", "event_date=2025-05-04", "validation_cutoff=2025-04-30"),
    ),
    "DATA_LABEL_ENUM_ALIGNMENT": CapabilitySpec(
        capability_id="DATA_LABEL_ENUM_ALIGNMENT",
        title="Label enum alignment",
        evidence_hint="row 9811 uses label gold_plus outside the allowed enum",
        fix_hint="Validate labels against the contract before training or export.",
        detector_needles=("gold_plus", "allowed_labels"),
    ),
    "PATCH_TEST_FAILURE_REPRO": CapabilitySpec(
        capability_id="PATCH_TEST_FAILURE_REPRO",
        title="Patch target failure reproduction",
        evidence_hint="test_discount_rounding fails because round_discount uses int(amount * rate)",
        fix_hint="Preserve a failing test or regression assertion that captures the issue.",
        detector_needles=("test_discount_rounding fails", "round_discount uses int(amount * rate)", "int(amount * rate)"),
    ),
    "PATCH_MINIMAL_CODE_CHANGE": CapabilitySpec(
        capability_id="PATCH_MINIMAL_CODE_CHANGE",
        title="Minimal behavior-preserving patch",
        evidence_hint="replace int(amount * rate) with round(amount * rate, 2)",
        fix_hint="Apply the smallest source change that fixes the failing behavior without broad rewrites.",
        detector_needles=("replace int(amount * rate)", "round(amount * rate, 2)"),
    ),
    "PATCH_REGRESSION_VALIDATION": CapabilitySpec(
        capability_id="PATCH_REGRESSION_VALIDATION",
        title="Regression validation command",
        evidence_hint="pytest tests/test_pricing.py::test_discount_rounding",
        fix_hint="Run the targeted test and record pass/fail evidence for the patch.",
        detector_needles=("pytest tests/test_pricing.py::test_discount_rounding", "test_discount_rounding"),
    ),
}
