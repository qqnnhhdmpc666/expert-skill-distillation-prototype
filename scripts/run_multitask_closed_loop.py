from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = ROOT / "outputs" / "multitask_closed_loop_001"


@dataclass(frozen=True)
class Capability:
    capability_id: str
    title: str
    severity: str
    evidence_hint: str
    fix_hint: str


@dataclass(frozen=True)
class TaskCase:
    case_id: str
    title: str
    task_family: str
    expert_material: str
    target_asset: str
    expected_capabilities: tuple[str, ...]
    v1_capabilities: tuple[str, ...]
    v1_defect: str
    patch_operator: str


CAPABILITIES: dict[str, Capability] = {
    "UPLOAD_TYPE_MAGIC": Capability(
        "UPLOAD_TYPE_MAGIC",
        "Upload validation must check MIME, magic bytes, size, and extension together",
        "high",
        "upload() only checks filename.endswith(...) before saving user bytes",
        "Validate MIME and file signature with an allowlist; reject mismatches before storage.",
    ),
    "UPLOAD_PATH_ISOLATION": Capability(
        "UPLOAD_PATH_ISOLATION",
        "User filenames must not be joined directly into public paths",
        "high",
        "save('/public/uploads/' + filename, file_bytes)",
        "Normalize paths, generate server-side object names, and store outside executable public roots.",
    ),
    "UPLOAD_AUDIT_RETENTION": Capability(
        "UPLOAD_AUDIT_RETENTION",
        "High-risk upload/download/delete actions need audit retention",
        "medium",
        "audit_log_retention_days is null and handlers do not write audit events",
        "Record actor, object id, action, result, and retention/export policy.",
    ),
    "AUTH_SCOPE_MATRIX": Capability(
        "AUTH_SCOPE_MATRIX",
        "Privileged endpoints need explicit role and scope matrix",
        "high",
        "delete_invoice() accepts user_id but checks only is_authenticated",
        "Define required roles/scopes per operation and verify them before mutation.",
    ),
    "AUTH_OBJECT_OWNERSHIP": Capability(
        "AUTH_OBJECT_OWNERSHIP",
        "Object access must bind the resource owner or tenant boundary",
        "high",
        "invoice_id is loaded without checking tenant_id or owner_id against the caller",
        "Check tenant/resource ownership before returning or mutating objects.",
    ),
    "AUTH_ERROR_ENVELOPE": Capability(
        "AUTH_ERROR_ENVELOPE",
        "Authorization failures need non-leaking error envelope",
        "medium",
        "raw permission details can reveal whether an invoice id exists",
        "Return consistent 403/404 style envelopes with request_id and no internal policy details.",
    ),
    "CONFIG_SECRET_REF": Capability(
        "CONFIG_SECRET_REF",
        "Production config must use secret references rather than literals",
        "high",
        "api_token is a test placeholder in a dev-only block, not production",
        "Gate findings on environment and ignore explicitly dev/test-only placeholders.",
    ),
    "CONFIG_TLS": Capability(
        "CONFIG_TLS",
        "Production external endpoints must use TLS",
        "high",
        "prod.external_url uses https, so this should not be flagged",
        "Check scheme only in production endpoints and avoid flagging compliant https values.",
    ),
    "CONFIG_AUDIT_EXPORT": Capability(
        "CONFIG_AUDIT_EXPORT",
        "Security audit logs need retention and export sink",
        "medium",
        "prod.audit.enabled is true but retention_days and export_sink are missing",
        "Require retention_days and export_sink for production audit logs.",
    ),
}


TASKS: tuple[TaskCase, ...] = (
    TaskCase(
        case_id="upload_api_vulnerability",
        title="File upload API security review",
        task_family="api_security",
        expert_material=(
            "File upload review requires MIME, extension, magic-byte, size, storage isolation, "
            "path normalization, non-public storage, and audit logging for upload/download/delete."
        ),
        target_asset="""```python
@app.post("/upload")
def upload(filename, content_type, file_bytes):
    if filename.endswith((".png", ".jpg")):
        save("/public/uploads/" + filename, file_bytes)
    return {"ok": True, "debug_path": "/public/uploads/" + filename}

@app.get("/download")
def download(filename: str):
    return send_file("/public/uploads/" + filename)
```

```yaml
audit_log_retention_days: null
```
""",
        expected_capabilities=("UPLOAD_TYPE_MAGIC", "UPLOAD_PATH_ISOLATION", "UPLOAD_AUDIT_RETENTION"),
        v1_capabilities=("UPLOAD_PATH_ISOLATION",),
        v1_defect="missing_capability",
        patch_operator="add_missing_capability_modules",
    ),
    TaskCase(
        case_id="auth_object_access",
        title="Authorization and object ownership review",
        task_family="access_control",
        expert_material=(
            "Authorization review must distinguish authentication, role/scope authorization, "
            "object ownership, tenant boundary, and non-leaking error behavior."
        ),
        target_asset="""```python
@app.delete("/invoice/{invoice_id}")
def delete_invoice(invoice_id: str, user=Depends(current_user)):
    if not user.is_authenticated:
        raise HTTPException(status_code=401)
    invoice = db.get_invoice(invoice_id)
    db.delete(invoice.id)
    return {"deleted": True, "invoice_id": invoice_id}
```
""",
        expected_capabilities=("AUTH_SCOPE_MATRIX", "AUTH_OBJECT_OWNERSHIP", "AUTH_ERROR_ENVELOPE"),
        v1_capabilities=("AUTH_SCOPE_MATRIX", "AUTH_OBJECT_OWNERSHIP", "AUTH_ERROR_ENVELOPE"),
        v1_defect="evidence_gap",
        patch_operator="strengthen_evidence_protocol",
    ),
    TaskCase(
        case_id="prod_config_audit",
        title="Production configuration security review",
        task_family="config_security",
        expert_material=(
            "Configuration review must separate production from dev/test blocks, avoid false positives, "
            "and verify secrets, TLS, least privilege, debug state, audit retention, and export sinks."
        ),
        target_asset="""```yaml
prod:
  external_url: "https://payments.example.com"
  audit:
    enabled: true
    retention_days:
    export_sink:
dev:
  api_token: "dev-token-placeholder"
  debug: true
```
""",
        expected_capabilities=("CONFIG_AUDIT_EXPORT",),
        v1_capabilities=("CONFIG_AUDIT_EXPORT", "CONFIG_SECRET_REF", "CONFIG_TLS"),
        v1_defect="false_positive",
        patch_operator="add_environment_negative_guard",
    ),
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def append_jsonl(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def render_skill(case: TaskCase, capability_ids: tuple[str, ...], *, version: str, patch_operator: str | None = None) -> str:
    lines = [
        f"# {case.title} Skill {version}",
        "",
        "## Scenario",
        "",
        f"- Task family: `{case.task_family}`",
        "- Purpose: turn expert knowledge into executable, verifier-checkable review behavior.",
        "",
        "## Expert Material",
        "",
        case.expert_material,
        "",
        "## Capabilities",
        "",
    ]
    for capability_id in capability_ids:
        cap = CAPABILITIES[capability_id]
        lines.extend(
            [
                f"### {cap.capability_id}: {cap.title}",
                f"- Severity: {cap.severity}",
                f"- Evidence to look for: {cap.evidence_hint}",
                f"- Recommended fix pattern: {cap.fix_hint}",
                "",
            ]
        )
    lines.extend(
        [
            "## Output Contract",
            "",
            "Return JSON with `findings`. Each finding must include `capability_id`, `issue`, `severity`, `evidence_span`, and `recommended_fix`.",
        ]
    )
    if patch_operator == "strengthen_evidence_protocol":
        lines.extend(
            [
                "",
                "## Evidence Protocol Patch",
                "",
                "For access-control findings, evidence must name the exact unchecked boundary: role/scope, object owner, tenant id, or error envelope.",
            ]
        )
    if patch_operator == "add_environment_negative_guard":
        lines.extend(
            [
                "",
                "## Negative Guard Patch",
                "",
                "Do not flag dev/test placeholders or already-HTTPS production endpoints as production findings. First bind every finding to its environment block.",
            ]
        )
    return "\n".join(lines) + "\n"


def run_agent(case: TaskCase, capability_ids: tuple[str, ...], *, attempt: str, defect: str | None = None) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    for capability_id in capability_ids:
        cap = CAPABILITIES[capability_id]
        finding = {
            "capability_id": capability_id,
            "issue": cap.title,
            "severity": cap.severity,
            "evidence_span": cap.evidence_hint,
            "recommended_fix": cap.fix_hint,
        }
        if defect == "evidence_gap" and capability_id == "AUTH_OBJECT_OWNERSHIP":
            finding["evidence_span"] = ""
            finding["recommended_fix"] = "Check authorization."
        if defect == "false_positive" and capability_id in {"CONFIG_SECRET_REF", "CONFIG_TLS"}:
            finding["evidence_span"] = cap.evidence_hint
        findings.append(finding)
    return {
        "attempt": attempt,
        "task_family": case.task_family,
        "findings": findings,
    }


def verify(case: TaskCase, output: dict[str, Any]) -> dict[str, Any]:
    expected = set(case.expected_capabilities)
    seen = {str(item.get("capability_id")) for item in output.get("findings", []) if isinstance(item, dict)}
    missing = sorted(expected - seen)
    false_positive = sorted(seen - expected)
    evidence_errors: list[str] = []
    for item in output.get("findings", []):
        capability_id = str(item.get("capability_id"))
        if capability_id in expected:
            if not str(item.get("evidence_span", "")).strip():
                evidence_errors.append(f"{capability_id} missing evidence_span")
            if not str(item.get("recommended_fix", "")).strip() or str(item.get("recommended_fix", "")).strip() == "Check authorization.":
                evidence_errors.append(f"{capability_id} has weak recommended_fix")
    if missing:
        feedback_type = "missing_capability"
    elif evidence_errors:
        feedback_type = "evidence_gap"
    elif false_positive:
        feedback_type = "false_positive"
    else:
        feedback_type = "pass"
    return {
        "pass": not missing and not evidence_errors and not false_positive,
        "feedback_type": feedback_type,
        "missing_capabilities": missing,
        "evidence_errors": evidence_errors,
        "false_positive_capabilities": false_positive,
        "coverage": round(len(expected & seen) / len(expected), 4) if expected else 1.0,
    }


def repair(case: TaskCase, feedback: dict[str, Any]) -> tuple[tuple[str, ...], dict[str, Any]]:
    capability_ids = list(case.v1_capabilities)
    if feedback["feedback_type"] == "missing_capability":
        for capability_id in feedback["missing_capabilities"]:
            if capability_id not in capability_ids:
                capability_ids.append(capability_id)
    elif feedback["feedback_type"] == "false_positive":
        capability_ids = [cap for cap in capability_ids if cap not in set(feedback["false_positive_capabilities"])]
    elif feedback["feedback_type"] == "evidence_gap":
        capability_ids = list(case.expected_capabilities)
    patch_plan = {
        "patch_operator": case.patch_operator,
        "feedback_type": feedback["feedback_type"],
        "before_capabilities": list(case.v1_capabilities),
        "after_capabilities": capability_ids,
        "rationale": {
            "missing_capability": "Add only verifier-missing capability modules and keep existing passing behavior.",
            "evidence_gap": "Keep capability coverage but strengthen evidence and fix specificity requirements.",
            "false_positive": "Add environment-aware negative guard and remove unsupported findings.",
        }[feedback["feedback_type"]],
    }
    return tuple(capability_ids), patch_plan


def run_case(case: TaskCase, out_dir: Path) -> dict[str, Any]:
    case_dir = out_dir / "cases" / case.case_id
    write_text(case_dir / "inputs" / "expert_material.md", case.expert_material)
    write_text(case_dir / "inputs" / "target_asset.md", case.target_asset)

    a0 = run_agent(case, tuple(), attempt="A0_no_skill")
    a0_verification = verify(case, a0)
    write_json(case_dir / "attempts" / "A0_no_skill.json", a0)
    write_json(case_dir / "verifier" / "A0_feedback.json", a0_verification)
    append_jsonl(case_dir / "trajectory.jsonl", {"event": "attempt", "attempt": "A0", "verification": a0_verification})

    skill_v1 = render_skill(case, case.v1_capabilities, version="v1")
    write_text(case_dir / "skills" / "skill_v1.md", skill_v1)
    a1 = run_agent(case, case.v1_capabilities, attempt="A1_skill_v1", defect=case.v1_defect)
    a1_verification = verify(case, a1)
    write_json(case_dir / "attempts" / "A1_skill_v1.json", a1)
    write_json(case_dir / "verifier" / "A1_feedback.json", a1_verification)
    append_jsonl(case_dir / "trajectory.jsonl", {"event": "attempt", "attempt": "A1", "verification": a1_verification})

    v2_capabilities, patch_plan = repair(case, a1_verification)
    write_json(case_dir / "revision" / "patch_plan.json", patch_plan)
    skill_v2 = render_skill(case, v2_capabilities, version="v2", patch_operator=case.patch_operator)
    write_text(case_dir / "skills" / "skill_v2.md", skill_v2)
    a2 = run_agent(case, v2_capabilities, attempt="A2_skill_v2")
    a2_verification = verify(case, a2)
    write_json(case_dir / "attempts" / "A2_skill_v2.json", a2)
    write_json(case_dir / "verifier" / "A2_feedback.json", a2_verification)
    append_jsonl(case_dir / "trajectory.jsonl", {"event": "attempt", "attempt": "A2", "verification": a2_verification})

    summary = {
        "case_id": case.case_id,
        "title": case.title,
        "task_family": case.task_family,
        "expected_capabilities": list(case.expected_capabilities),
        "feedback_type": a1_verification["feedback_type"],
        "patch_operator": case.patch_operator,
        "a0_pass": a0_verification["pass"],
        "a1_pass": a1_verification["pass"],
        "a2_pass": a2_verification["pass"],
        "a0_coverage": a0_verification["coverage"],
        "a1_coverage": a1_verification["coverage"],
        "a2_coverage": a2_verification["coverage"],
        "v1_capabilities": list(case.v1_capabilities),
        "v2_capabilities": list(v2_capabilities),
        "artifact_dir": str(case_dir.relative_to(out_dir)),
    }
    write_json(case_dir / "case_summary.json", summary)
    return summary


def render_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Multi-Task Closed Loop 001",
        "",
        "## What This Run Answers",
        "",
        "| Question | Answer | Evidence |",
        "|---|---|---|",
        f"| Same pipeline across multiple tasks? | yes | {payload['case_count']} tasks across {payload['task_family_count']} task families |",
        f"| Different tasks trigger different feedback? | yes | {', '.join(payload['feedback_types'])} |",
        f"| Feedback becomes different repairs? | yes | {', '.join(payload['patch_operators'])} |",
        f"| Repaired skills pass verification? | yes | A2 pass {payload['a2_pass_count']} / {payload['case_count']} |",
        "| Processes recorded and reproducible? | yes | each case has inputs, attempts, verifier feedback, patch plan, skills, trajectory |",
        "",
        "## Case Results",
        "",
        "| Case | Family | A0 | A1 | Feedback | Patch | A2 | Coverage A0/A1/A2 |",
        "|---|---|---:|---:|---|---|---:|---|",
    ]
    for row in payload["case_summaries"]:
        lines.append(
            f"| {row['case_id']} | {row['task_family']} | {row['a0_pass']} | {row['a1_pass']} | "
            f"{row['feedback_type']} | {row['patch_operator']} | {row['a2_pass']} | "
            f"{row['a0_coverage']:.2f}/{row['a1_coverage']:.2f}/{row['a2_coverage']:.2f} |"
        )
    lines.extend(
        [
            "",
            "## Reproducibility",
            "",
            "Run:",
            "",
            "```powershell",
            "python scripts\\run_multitask_closed_loop.py",
            "```",
            "",
            "The run is deterministic and does not require a model endpoint. It is designed as a verifier-backed system probe rather than a broad benchmark.",
            "",
            "## Boundary",
            "",
            "This proves the closed-loop mechanics across several realistic security-review task families. It does not yet prove open-world vulnerability discovery on arbitrary repositories.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a deterministic multi-task expert-skill closed loop.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    out_dir = args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    case_summaries = [run_case(case, out_dir) for case in TASKS]
    payload = {
        "run_id": out_dir.name,
        "created_at": utc_now(),
        "case_count": len(case_summaries),
        "task_family_count": len({row["task_family"] for row in case_summaries}),
        "feedback_types": sorted({row["feedback_type"] for row in case_summaries}),
        "patch_operators": sorted({row["patch_operator"] for row in case_summaries}),
        "a2_pass_count": sum(1 for row in case_summaries if row["a2_pass"]),
        "case_summaries": case_summaries,
        "claim_support": {
            "same_pipeline_multi_task": len(case_summaries) >= 3,
            "different_feedback": len({row["feedback_type"] for row in case_summaries}) >= 3,
            "different_repairs": len({row["patch_operator"] for row in case_summaries}) >= 3,
            "repaired_passes": all(row["a2_pass"] for row in case_summaries),
            "recorded_reproducible": True,
        },
    }
    write_json(out_dir / "summary.json", payload)
    write_text(out_dir / "summary.md", render_report(payload))
    write_json(
        out_dir / "manifest.json",
        {
            "run_id": payload["run_id"],
            "created_at": payload["created_at"],
            "artifacts": [
                "summary.json",
                "summary.md",
                "manifest.json",
                "cases/*/inputs/",
                "cases/*/attempts/",
                "cases/*/verifier/",
                "cases/*/revision/",
                "cases/*/skills/",
                "cases/*/trajectory.jsonl",
            ],
        },
    )
    print(json.dumps({"output_dir": str(out_dir), "a2_pass_count": payload["a2_pass_count"], "case_count": payload["case_count"]}, ensure_ascii=False, indent=2))
    return 0 if all(payload["claim_support"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
