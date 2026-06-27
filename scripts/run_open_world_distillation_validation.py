from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import traceback
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from skill_deployment import MaterialSource, distill_material_skill_bundle, install_skill_package, load_active_pointer, resolve_installed_skill  # noqa: E402
from skill_deployment.evidence import false_positive_count, write_json, write_text  # noqa: E402

import scripts.run_defensive_security_mini_suite as mini  # noqa: E402
from scripts.run_external_generalization_validation import materialize_cases as materialize_validation_cases  # noqa: E402
from scripts.run_external_generalization_validation import download_sources as download_validation_sources  # noqa: E402


OUTPUT_ROOT = ROOT / "outputs" / "open_world_distillation_validation"
REPORT = ROOT / "reports" / "OPEN_WORLD_DISTILLATION_VALIDATION_STATUS.md"

PUBLIC_MATERIAL_URLS = {
    "upload_file_upload_cheatsheet": {
        "task_family": "upload_security",
        "title": "OWASP File Upload Cheat Sheet",
        "url": "https://raw.githubusercontent.com/OWASP/CheatSheetSeries/master/cheatsheets/File_Upload_Cheat_Sheet.md",
    },
    "auth_authorization_cheatsheet": {
        "task_family": "auth_access_control",
        "title": "OWASP Authorization Cheat Sheet",
        "url": "https://raw.githubusercontent.com/OWASP/CheatSheetSeries/master/cheatsheets/Authorization_Cheat_Sheet.md",
    },
    "auth_error_handling_cheatsheet": {
        "task_family": "auth_access_control",
        "title": "OWASP Error Handling Cheat Sheet",
        "url": "https://raw.githubusercontent.com/OWASP/CheatSheetSeries/master/cheatsheets/Error_Handling_Cheat_Sheet.md",
    },
    "config_logging_cheatsheet": {
        "task_family": "config_security",
        "title": "OWASP Logging Cheat Sheet",
        "url": "https://raw.githubusercontent.com/OWASP/CheatSheetSeries/master/cheatsheets/Logging_Cheat_Sheet.md",
    },
    "config_secrets_cheatsheet": {
        "task_family": "config_security",
        "title": "OWASP Secrets Management Cheat Sheet",
        "url": "https://raw.githubusercontent.com/OWASP/CheatSheetSeries/master/cheatsheets/Secrets_Management_Cheat_Sheet.md",
    },
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def api_key_present() -> bool:
    return bool(os.environ.get("OPENAI_API_KEY"))


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def download_public_materials(output_root: Path, timeout: float = 30.0) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    source_dir = output_root / "source_material_downloads"
    for source_id, spec in PUBLIC_MATERIAL_URLS.items():
        try:
            with urllib.request.urlopen(spec["url"], timeout=timeout) as response:
                content = response.read().decode("utf-8", errors="replace")
            digest = sha256_text(content)
            path = source_dir / f"{source_id}_{digest[:12]}.md"
            write_text(path, content)
            result[source_id] = {
                "status": "downloaded",
                "task_family": spec["task_family"],
                "title": spec["title"],
                "source_url": spec["url"],
                "sha256": digest,
                "path": str(path),
                "chars": len(content),
                "error": None,
            }
        except (OSError, urllib.error.URLError, TimeoutError) as exc:
            result[source_id] = {
                "status": "blocked",
                "task_family": spec["task_family"],
                "title": spec["title"],
                "source_url": spec["url"],
                "sha256": None,
                "path": None,
                "chars": 0,
                "error": str(exc),
            }
    return result


def source_text(status: dict[str, Any], fallback: str) -> str:
    path = status.get("path")
    if path and Path(path).exists():
        return Path(path).read_text(encoding="utf-8", errors="replace")
    return fallback


def material_sources(status: dict[str, dict[str, Any]]) -> list[MaterialSource]:
    upload = status["upload_file_upload_cheatsheet"]
    auth = status["auth_authorization_cheatsheet"]
    auth_errors = status["auth_error_handling_cheatsheet"]
    logging = status["config_logging_cheatsheet"]
    secrets = status["config_secrets_cheatsheet"]
    return [
        MaterialSource(
            source_id="public_upload_material_001",
            task_family="upload_security",
            title="OWASP File Upload Cheat Sheet",
            material_text=source_text(upload, "Validate file type, rename uploads, store outside webroot, and log upload events."),
            source_url=upload.get("source_url"),
            source_path=upload.get("path"),
            metadata={"sha256": upload.get("sha256"), "material_scope": "public_cheatsheet"},
        ),
        MaterialSource(
            source_id="public_upload_logging_material_001",
            task_family="upload_security",
            title="OWASP Logging Cheat Sheet (upload audit excerpt)",
            material_text=source_text(logging, "Submission and processing of user-generated content, especially file uploads, should be logged with retention and export."),
            source_url=logging.get("source_url"),
            source_path=logging.get("path"),
            metadata={"sha256": logging.get("sha256"), "material_scope": "public_cheatsheet"},
        ),
        MaterialSource(
            source_id="public_auth_material_001",
            task_family="auth_access_control",
            title="OWASP Authorization Cheat Sheet",
            material_text=source_text(auth, "Enforce authorization on every request, least privilege, object-level access control, and avoid revealing identifiers in denial flows."),
            source_url=auth.get("source_url"),
            source_path=auth.get("path"),
            metadata={"sha256": auth.get("sha256"), "material_scope": "public_cheatsheet"},
        ),
        MaterialSource(
            source_id="public_auth_error_material_001",
            task_family="auth_access_control",
            title="OWASP Error Handling Cheat Sheet",
            material_text=source_text(auth_errors, "Error handling should fail safely and avoid leaking sensitive internal details or business identifiers."),
            source_url=auth_errors.get("source_url"),
            source_path=auth_errors.get("path"),
            metadata={"sha256": auth_errors.get("sha256"), "material_scope": "public_cheatsheet"},
        ),
        MaterialSource(
            source_id="public_config_logging_material_001",
            task_family="config_security",
            title="OWASP Logging Cheat Sheet",
            material_text=source_text(logging, "Logging should preserve sufficient detail, protect integrity, and support incident review."),
            source_url=logging.get("source_url"),
            source_path=logging.get("path"),
            metadata={"sha256": logging.get("sha256"), "material_scope": "public_cheatsheet"},
        ),
        MaterialSource(
            source_id="public_config_secrets_material_001",
            task_family="config_security",
            title="OWASP Secrets Management Cheat Sheet",
            material_text=source_text(secrets, "Secrets should not be exposed across environments and should be separated from development defaults."),
            source_url=secrets.get("source_url"),
            source_path=secrets.get("path"),
            metadata={"sha256": secrets.get("sha256"), "material_scope": "public_cheatsheet"},
        ),
    ]


def select_validation_cases(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    wanted = {
        "public_nodegoat_dev_config_001",
        "public_nodegoat_eval_unsupported_001",
        "public_nodegoat_regex_unsupported_001",
        "independent_upload_mime_storage_001",
        "independent_upload_clean_001",
        "independent_config_prod_audit_001",
        "independent_config_clean_001",
        "independent_auth_invoice_scope_001",
        "independent_auth_clean_001",
        "independent_dependency_unsupported_001",
    }
    selected = [case for case in cases if case["case_id"] in wanted]
    selected.sort(key=lambda item: str(item["case_id"]))
    return selected


def run_variant(
    *,
    case_payload: dict[str, Any],
    spec: mini.VariantSpec,
    output_dir: Path,
    active_pointer_snapshot: dict[str, Any],
    backend: str,
    base_url: str,
    model: str,
    timeout_seconds: float,
) -> dict[str, Any]:
    out_dir = output_dir / str(case_payload["case_id"]) / spec.name
    try:
        runner_metadata: dict[str, Any] = {}
        if backend == "live_llm_text":
            if not api_key_present():
                return {
                    "case_id": case_payload["case_id"],
                    "task_family": case_payload["agent_visible"]["task_family"],
                    "variant": spec.name,
                    "status": "blocked",
                    "blocked_reason": "missing_env:OPENAI_API_KEY",
                    "artifact_dir": str(out_dir),
                }
            runner_metadata = {
                "base_url": base_url,
                "model": model,
                "temperature": 0.0,
                "timeout": timeout_seconds,
                "task_label": f"{spec.name}:{case_payload['agent_visible']['task_family']}",
                "contract_mode": "strict",
                "enable_evidence_normalizer": True,
                "prompt_addendum": (
                    "Open-material validation: quote exact target lines; emit no finding for unsupported or clean cases. "
                    "Defensive review only. Do not invent capabilities beyond the installed Skill package."
                ),
            }
        summary = mini.run_variant(
            case_payload=case_payload,
            agent_case=mini.make_agent_visible_case(case_payload),
            verifier_only=case_payload["verifier_only"],
            spec=spec,
            backend=backend,
            output_dir=out_dir,
            active_pointer_snapshot=active_pointer_snapshot,
            runner_metadata=runner_metadata,
        )
        verifier = summary.get("post_normalization_verifier") or read_json(out_dir / "verifier_report.json", {})
        return {
            "case_id": case_payload["case_id"],
            "task_family": case_payload["agent_visible"]["task_family"],
            "variant": spec.name,
            "status": "completed",
            "verifier_result": "pass" if verifier.get("pass") else "fail",
            "feedback_type": verifier.get("feedback_type"),
            "effective_pass": bool(verifier.get("pass")) and bool(summary.get("capability_group_correct")),
            "activated_capability_group": summary.get("activated_capability_group"),
            "expected_capability_group": summary.get("expected_capability_group"),
            "capability_group_correct": summary.get("capability_group_correct"),
            "false_positive_count": false_positive_count(verifier),
            "out_of_scope_correct": summary.get("out_of_scope_correct"),
            "clean_or_negative": bool(case_payload["verifier_only"].get("clean_or_negative")),
            "unsupported_limitation": bool(case_payload["verifier_only"].get("unsupported_limitation")),
            "artifact_dir": str(out_dir),
        }
    except Exception as exc:  # noqa: BLE001
        write_text(out_dir / "blocked_or_failed_trace.txt", traceback.format_exc())
        return {
            "case_id": case_payload["case_id"],
            "task_family": case_payload["agent_visible"]["task_family"],
            "variant": spec.name,
            "status": "failed",
            "failure_reason": str(exc),
            "artifact_dir": str(out_dir),
        }


def summarize(distilled_rows: list[dict[str, Any]], baseline_rows: list[dict[str, Any]]) -> dict[str, Any]:
    distilled_completed = [row for row in distilled_rows if row.get("status") == "completed"]
    baseline_completed = [row for row in baseline_rows if row.get("status") == "completed"]
    return {
        "distilled_case_count": len(distilled_rows),
        "distilled_completed_count": len(distilled_completed),
        "baseline_completed_count": len(baseline_completed),
        "distilled_effective_pass_count": sum(1 for row in distilled_completed if row.get("effective_pass")),
        "baseline_effective_pass_count": sum(1 for row in baseline_completed if row.get("effective_pass")),
        "distilled_false_positive_count": sum(int(row.get("false_positive_count") or 0) for row in distilled_completed),
        "baseline_false_positive_count": sum(int(row.get("false_positive_count") or 0) for row in baseline_completed),
        "distilled_clean_negative_pass_count": sum(1 for row in distilled_completed if row.get("clean_or_negative") and int(row.get("false_positive_count") or 0) == 0),
        "distilled_unsupported_preserved_count": sum(1 for row in distilled_completed if row.get("unsupported_limitation") and row.get("out_of_scope_correct") and int(row.get("false_positive_count") or 0) == 0),
    }


def render_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Open-World Distillation Validation Status",
        "",
        f"Generated at: `{payload['generated_at']}`",
        "",
        "This run evaluates a bounded public-material automatic distillation path. It does not claim universal open-world semantic induction.",
        "",
        "## Fresh Commands",
        "",
        "```powershell",
        f"skill-deploy open-world-distill-validation --backend live_llm_text --base-url https://api.deepseek.com --model deepseek-v4-flash --projection-mode {payload['projection_mode']}",
        "```",
        "",
        "## Distillation",
        "",
        f"- Installed skill id: `{payload['distilled_skill_id']}`",
        f"- Distillation method: `{payload['distillation_method']}`",
        f"- Projection mode: `{payload['projection_mode']}`",
        f"- Supported families: `{', '.join(payload['supported_task_families'])}`",
        f"- Selected capabilities: `{', '.join(payload['selected_capabilities'])}`",
        "",
        "## Summary",
        "",
        f"- Distilled completed rows: `{payload['distilled_completed_count']}` / `{payload['distilled_case_count']}`",
        f"- Distilled effective pass count: `{payload['distilled_effective_pass_count']}`",
        f"- Baseline effective pass count: `{payload['baseline_effective_pass_count']}`",
        f"- Distilled false positives: `{payload['distilled_false_positive_count']}`",
        f"- Clean negative controls passed: `{payload['distilled_clean_negative_pass_count']}`",
        f"- Unsupported limitations preserved: `{payload['distilled_unsupported_preserved_count']}`",
        "",
        "## Case Comparison",
        "",
        "| Case | Family | Distilled | Baseline | Distilled group | Baseline group | Distilled FP | Note |",
        "|---|---|---|---|---|---|---:|---|",
    ]
    baseline_by_case = {row["case_id"]: row for row in payload["baseline_rows"]}
    for row in payload["distilled_rows"]:
        base = baseline_by_case.get(row["case_id"], {})
        note = "ok"
        if row.get("clean_or_negative") and int(row.get("false_positive_count") or 0) != 0:
            note = "clean negative failed"
        elif row.get("unsupported_limitation") and not row.get("out_of_scope_correct"):
            note = "unsupported limitation not preserved"
        elif not row.get("effective_pass"):
            note = row.get("feedback_type") or row.get("failure_reason") or row.get("blocked_reason") or "fail"
        lines.append(
            f"| {row['case_id']} | {row['task_family']} | {row.get('status')}:{row.get('verifier_result')} | "
            f"{base.get('status')}:{base.get('verifier_result')} | {row.get('activated_capability_group')} | "
            f"{base.get('activated_capability_group')} | {row.get('false_positive_count')} | {note} |"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- Distillation source is public or independent material, not the controlled `expert_material.md` files.",
            "- Validation labels are still local deterministic verifier labels, not official external benchmark labels.",
            "- This is evidence for bounded open-material automatic distillation into the current capability registry.",
            "- It is not proof of arbitrary open-world vulnerability discovery or unrestricted Skill induction.",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run bounded open-world/public-material automatic distillation and validate the resulting Skill.")
    parser.add_argument("--skill-id", default="secure_code_review_open_world_distilled")
    parser.add_argument("--version", default="v1")
    parser.add_argument("--backend", default="live_llm_text")
    parser.add_argument("--baseline-skill", default="secure_code_review")
    parser.add_argument("--output-dir", default=str(OUTPUT_ROOT))
    parser.add_argument("--base-url", default=os.environ.get("OPENAI_BASE_URL") or "https://api.deepseek.com")
    parser.add_argument("--model", default=os.environ.get("MODEL") or os.environ.get("OPENAI_MODEL") or "deepseek-v4-flash")
    parser.add_argument("--timeout-seconds", type=float, default=60.0)
    parser.add_argument("--projection-mode", choices=["keyword", "live_semantic", "hybrid_semantic"], default="keyword")
    args = parser.parse_args(argv)

    output_root = Path(args.output_dir)
    material_status = download_public_materials(output_root)
    materials = material_sources(material_status)
    distilled_output_dir = output_root / "distilled_skill" / args.skill_id
    distill_summary = distill_material_skill_bundle(
        skill_id=args.skill_id,
        version=args.version,
        materials=materials,
        output_dir=distilled_output_dir,
        title="Open-Material Distilled Secure Code Review",
        distillation_method=(
            "live_semantic_projection_from_open_materials"
            if args.projection_mode == "live_semantic"
            else "hybrid_semantic_projection_from_open_materials"
            if args.projection_mode == "hybrid_semantic"
            else "keyword_projection_from_open_materials"
        ),
        projection_mode=args.projection_mode,
        base_url=args.base_url,
        api_key=os.environ.get("OPENAI_API_KEY"),
        model=args.model,
        timeout_seconds=args.timeout_seconds,
    )
    install_summary = install_skill_package(ROOT, distilled_output_dir, requested_version=args.version)
    distilled_resolved = resolve_installed_skill(ROOT, args.skill_id)
    baseline_resolved = resolve_installed_skill(ROOT, args.baseline_skill)
    distilled_pointer = load_active_pointer(ROOT, args.skill_id)
    baseline_pointer = load_active_pointer(ROOT, args.baseline_skill)

    validation_sources = download_validation_sources(output_root / "validation_sources")
    cases = select_validation_cases(materialize_validation_cases(validation_sources))
    distilled_spec = mini.VariantSpec(
        "open_world_distilled",
        distilled_resolved["skill_package"],
        distilled_resolved["skill_text"],
        distilled_resolved["skill_dir"],
        "open_world_distilled_package",
    )
    baseline_spec = mini.VariantSpec(
        "baseline_active",
        baseline_resolved["skill_package"],
        baseline_resolved["skill_text"],
        baseline_resolved["skill_dir"],
        "baseline_active_package",
    )
    distilled_rows = [
        run_variant(
            case_payload=case_payload,
            spec=distilled_spec,
            output_dir=output_root / "cases" / "distilled",
            active_pointer_snapshot=distilled_pointer,
            backend=args.backend,
            base_url=args.base_url,
            model=args.model,
            timeout_seconds=args.timeout_seconds,
        )
        for case_payload in cases
    ]
    baseline_rows = [
        run_variant(
            case_payload=case_payload,
            spec=baseline_spec,
            output_dir=output_root / "cases" / "baseline",
            active_pointer_snapshot=baseline_pointer,
            backend=args.backend,
            base_url=args.base_url,
            model=args.model,
            timeout_seconds=args.timeout_seconds,
        )
        for case_payload in cases
    ]
    payload = {
        "run_id": "open_world_distillation_validation",
        "generated_at": utc_now(),
        "backend": args.backend,
        "model": args.model,
        "api_key_present": api_key_present(),
        "distilled_skill_id": args.skill_id,
        "baseline_skill_id": args.baseline_skill,
        "distillation_method": distill_summary["distillation_method"],
        "projection_mode": distill_summary["projection_mode"],
        "supported_task_families": distill_summary["supported_task_families"],
        "selected_capabilities": distill_summary["selected_capabilities"],
        "material_status": material_status,
        "validation_source_status": validation_sources,
        "distillation_output_dir": distill_summary["output_dir"],
        "install_summary": install_summary,
        "distilled_rows": distilled_rows,
        "baseline_rows": baseline_rows,
    }
    payload.update(summarize(distilled_rows, baseline_rows))
    write_json(output_root / "open_world_distillation_validation_summary.json", payload)
    write_text(REPORT, render_report(payload))
    print(
        json.dumps(
            {
                "status": "ok",
                "report": str(REPORT),
                "summary": str(output_root / "open_world_distillation_validation_summary.json"),
                "distilled_effective_pass_count": payload["distilled_effective_pass_count"],
                "baseline_effective_pass_count": payload["baseline_effective_pass_count"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
