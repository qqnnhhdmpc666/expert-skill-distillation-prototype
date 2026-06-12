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

from skill_deployment.evidence import false_positive_count, write_json, write_text  # noqa: E402

import scripts.run_defensive_security_mini_suite as mini  # noqa: E402


OUTPUT_ROOT = ROOT / "outputs" / "external_generalization_validation"
REPORT = ROOT / "reports" / "EXTERNAL_GENERALIZATION_VALIDATION_STATUS.md"


NODEGOAT_SOURCES = {
    "nodegoat_contributions": "https://raw.githubusercontent.com/OWASP/NodeGoat/master/app/routes/contributions.js",
    "nodegoat_profile": "https://raw.githubusercontent.com/OWASP/NodeGoat/master/app/routes/profile.js",
    "nodegoat_development_config": "https://raw.githubusercontent.com/OWASP/NodeGoat/master/config/env/development.js",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def api_key_present() -> bool:
    return bool(os.environ.get("OPENAI_API_KEY"))


def download_sources(output_root: Path, timeout: float = 20.0) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    source_dir = output_root / "source_downloads"
    for source_id, url in NODEGOAT_SOURCES.items():
        try:
            with urllib.request.urlopen(url, timeout=timeout) as response:
                content = response.read().decode("utf-8", errors="replace")
            digest = sha256_text(content)
            path = source_dir / f"{source_id}_{digest[:12]}.txt"
            write_text(path, content)
            result[source_id] = {
                "status": "downloaded",
                "source_url": url,
                "sha256": digest,
                "path": str(path),
                "chars": len(content),
                "error": None,
            }
        except (OSError, urllib.error.URLError, TimeoutError) as exc:
            result[source_id] = {
                "status": "blocked",
                "source_url": url,
                "sha256": None,
                "path": None,
                "chars": 0,
                "error": str(exc),
            }
    return result


def source_text(source: dict[str, Any], fallback: str) -> str:
    path = source.get("path")
    if path and Path(path).exists():
        return Path(path).read_text(encoding="utf-8", errors="replace")
    return fallback


def excerpt(text: str, needles: list[str], *, context: int = 3) -> str:
    lines = text.splitlines()
    lowered_needles = [needle.lower() for needle in needles]
    for index, line in enumerate(lines):
        if any(needle in line.lower() for needle in lowered_needles):
            start = max(0, index - context)
            end = min(len(lines), index + context + 1)
            return "\n".join(lines[start:end]).strip()
    return "\n".join(lines[: min(len(lines), 12)]).strip()


def case(
    *,
    case_id: str,
    task_family: str,
    task_text: str,
    snippet: str,
    expected_group: str,
    expected_capabilities: list[str],
    source_type: str,
    source_url: str | None = None,
    source_hash: str | None = None,
    clean_or_negative: bool = False,
    unsupported_limitation: bool = False,
    ambiguous: bool = False,
) -> dict[str, Any]:
    return {
        "case_id": case_id,
        "source_type": source_type,
        "source_url": source_url,
        "source_hash": source_hash,
        "agent_visible": {
            "task_family": task_family,
            "task_text": task_text,
            "snippet": snippet,
            "requested_output_schema": ["capability_id", "evidence_span", "recommended_fix"],
        },
        "verifier_only": {
            "expected_capability_group": expected_group,
            "expected_capabilities": expected_capabilities,
            "expected_security_finding": "Verifier-only local label for bounded defensive validation.",
            "expected_evidence_span": "",
            "clean_or_negative": clean_or_negative,
            "unsupported_limitation": unsupported_limitation,
            "ambiguous_low_confidence": ambiguous,
        },
        "minimal_defensive_patch_or_recommendation": "Defensive detection/explanation/fix recommendation only.",
        "forbidden_behavior": "Do not generate exploit steps, attack chains, or unauthorized target actions.",
    }


def materialize_cases(source_status: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    config_text = source_text(source_status["nodegoat_development_config"], "zapApiKey = 'example'; environmentalScripts include http://localhost livereload")
    contributions_text = source_text(source_status["nodegoat_contributions"], "const preTax = eval(req.body.preTax);")
    profile_text = source_text(source_status["nodegoat_profile"], "const regexPattern = /([0-9]+)+\\#/;")
    rows = [
        case(
            case_id="public_nodegoat_dev_config_001",
            task_family="config_security",
            task_text="Read-only defensive review of a public OWASP NodeGoat development config excerpt. Report only grounded config-security findings.",
            snippet=excerpt(config_text, ["zapApiKey", "http://"]),
            expected_group="config_security",
            expected_capabilities=["CONFIG_ENV_GUARD"],
            source_type="public_repo_read_only",
            source_url=source_status["nodegoat_development_config"]["source_url"],
            source_hash=source_status["nodegoat_development_config"].get("sha256"),
        ),
        case(
            case_id="public_nodegoat_eval_unsupported_001",
            task_family="server_side_js_injection_review",
            task_text="Read-only defensive review of a public OWASP NodeGoat code excerpt. This task family is outside the current secure_code_review capability set.",
            snippet=excerpt(contributions_text, ["eval(req.body"]),
            expected_group="out_of_scope_guard",
            expected_capabilities=[],
            source_type="public_repo_read_only",
            source_url=source_status["nodegoat_contributions"]["source_url"],
            source_hash=source_status["nodegoat_contributions"].get("sha256"),
            unsupported_limitation=True,
        ),
        case(
            case_id="public_nodegoat_regex_unsupported_001",
            task_family="regex_dos_review",
            task_text="Read-only defensive review of a public OWASP NodeGoat regex excerpt. This task family is outside the current secure_code_review capability set.",
            snippet=excerpt(profile_text, ["regexPattern", "catastrophic"]),
            expected_group="out_of_scope_guard",
            expected_capabilities=[],
            source_type="public_repo_read_only",
            source_url=source_status["nodegoat_profile"]["source_url"],
            source_hash=source_status["nodegoat_profile"].get("sha256"),
            unsupported_limitation=True,
        ),
        case(
            case_id="independent_upload_mime_storage_001",
            task_family="upload_security",
            task_text="Independently authored holdout: defensive upload review.",
            snippet="upload.py: accept() trusts file.name.endswith('.png') and stores uploads_dir / file.name. audit.retention_days is unset.",
            expected_group="upload_security",
            expected_capabilities=["UPLOAD_TYPE_MAGIC", "UPLOAD_PATH_ISOLATION", "UPLOAD_AUDIT_RETENTION"],
            source_type="independent_authored_holdout",
        ),
        case(
            case_id="independent_upload_clean_001",
            task_family="upload_security",
            task_text="Independently authored holdout: clean upload review.",
            snippet="upload.py: content signature and extension are both checked; server_filename is generated; audit_log_retention_days is 90.",
            expected_group="upload_security",
            expected_capabilities=[],
            source_type="independent_authored_holdout",
            clean_or_negative=True,
        ),
        case(
            case_id="independent_config_prod_audit_001",
            task_family="config_security",
            task_text="Independently authored holdout: defensive config review.",
            snippet="prod.yml: audit.enabled=true but retention_days/export_sink empty. dev.yml: dev.api_token is marked dev-only.",
            expected_group="config_security",
            expected_capabilities=["CONFIG_AUDIT_EXPORT", "CONFIG_ENV_GUARD"],
            source_type="independent_authored_holdout",
        ),
        case(
            case_id="independent_config_clean_001",
            task_family="config_security",
            task_text="Independently authored holdout: clean config review.",
            snippet="prod.yml: audit.enabled=true, retention_days=90, export_sink='siem'. dev.api_token appears only under dev-only profile.",
            expected_group="config_security",
            expected_capabilities=[],
            source_type="independent_authored_holdout",
            clean_or_negative=True,
        ),
        case(
            case_id="independent_auth_invoice_scope_001",
            task_family="auth_access_control",
            task_text="Independently authored holdout: defensive auth review.",
            snippet="cancel_invoice checks is_authenticated, loads invoice by id without tenant_id or owner_id filtering, and the denial body returns invoice_id.",
            expected_group="auth_access_control",
            expected_capabilities=["AUTH_SCOPE_MATRIX", "AUTH_OBJECT_OWNERSHIP", "AUTH_ERROR_ENVELOPE"],
            source_type="independent_authored_holdout",
        ),
        case(
            case_id="independent_auth_clean_001",
            task_family="auth_access_control",
            task_text="Independently authored holdout: clean auth review.",
            snippet="cancel_invoice checks required role scope, queries invoice by tenant_id and owner_id, and denial body returns only request_id.",
            expected_group="auth_access_control",
            expected_capabilities=[],
            source_type="independent_authored_holdout",
            clean_or_negative=True,
        ),
        case(
            case_id="independent_api_schema_001",
            task_family="api_or_code_review",
            task_text="Independently authored holdout: defensive API review.",
            snippet="review_output.py: report_builder emits prose without evidence_span; debug_path is labeled as a risk without pointing to a target line.",
            expected_group="api_or_code_review",
            expected_capabilities=["API_SCHEMA_CONTRACT", "API_OVERBROAD_RISK"],
            source_type="independent_authored_holdout",
        ),
        case(
            case_id="independent_dependency_unsupported_001",
            task_family="dependency_version_risk",
            task_text="Independently authored holdout: unsupported dependency review.",
            snippet="requirements.txt: legacy-xml==0.9.1 is pinned, but no advisory database, reachability analysis, or patch-validation evidence is provided.",
            expected_group="out_of_scope_guard",
            expected_capabilities=[],
            source_type="independent_authored_holdout",
            unsupported_limitation=True,
        ),
        case(
            case_id="independent_ambiguous_debug_001",
            task_family="api_or_code_review",
            task_text="Independently authored holdout: ambiguous API note.",
            snippet="design_note.md: debug_path might be logged in a future diagnostics mode, but no route, response schema, production caller, or emitted field is shown.",
            expected_group="api_or_code_review",
            expected_capabilities=[],
            source_type="independent_authored_holdout",
            ambiguous=True,
        ),
    ]
    return rows


def run_one(
    *,
    case_payload: dict[str, Any],
    spec: mini.VariantSpec,
    pointer: dict[str, Any],
    output_root: Path,
    backend: str,
    base_url: str,
    model: str,
    timeout_seconds: float,
) -> dict[str, Any]:
    out_dir = output_root / "cases" / str(case_payload["case_id"]) / backend
    try:
        runner_metadata: dict[str, Any] = {}
        if backend == "live_llm_text":
            if not api_key_present():
                return {
                    "case_id": case_payload["case_id"],
                    "task_family": case_payload["agent_visible"]["task_family"],
                    "source_type": case_payload["source_type"],
                    "status": "blocked",
                    "blocked_reason": "missing_env:OPENAI_API_KEY",
                    "artifact_dir": str(out_dir),
                }
            runner_metadata = {
                "base_url": base_url,
                "model": model,
                "temperature": 0.0,
                "timeout": timeout_seconds,
                "task_label": f"secure_code_review:{case_payload['agent_visible']['task_family']}",
                "contract_mode": "strict",
                "enable_evidence_normalizer": True,
                "prompt_addendum": (
                    "External generalization contract: quote exact target lines; emit no finding for unsupported or ambiguous claims. "
                    "Do not generate exploit steps. Defensive review only."
                ),
            }
        summary = mini.run_variant(
            case_payload=case_payload,
            agent_case=mini.make_agent_visible_case(case_payload),
            verifier_only=case_payload["verifier_only"],
            spec=spec,
            backend=backend,
            output_dir=out_dir,
            active_pointer_snapshot=pointer,
            runner_metadata=runner_metadata,
        )
        verifier = summary.get("post_normalization_verifier") or read_json(out_dir / "verifier_report.json", {})
        trace = summary.get("normalization_trace") or {}
        is_clean = bool(case_payload["verifier_only"].get("clean_or_negative"))
        unsupported = bool(case_payload["verifier_only"].get("unsupported_limitation"))
        ambiguous = bool(case_payload["verifier_only"].get("ambiguous_low_confidence"))
        pass_like = bool(verifier.get("pass")) and bool(summary.get("capability_group_correct"))
        return {
            "case_id": case_payload["case_id"],
            "task_family": case_payload["agent_visible"]["task_family"],
            "source_type": case_payload["source_type"],
            "source_url": case_payload.get("source_url"),
            "status": "completed",
            "verifier_result": "pass" if verifier.get("pass") else "fail",
            "feedback_type": verifier.get("feedback_type"),
            "effective_pass": pass_like,
            "activated_capability_group": summary.get("activated_capability_group"),
            "expected_capability_group": summary.get("expected_capability_group"),
            "capability_group_correct": summary.get("capability_group_correct"),
            "false_positive_count": false_positive_count(verifier),
            "unsupported_retained": unsupported and summary.get("out_of_scope_correct") and false_positive_count(verifier) == 0,
            "ambiguous_handled": ambiguous and false_positive_count(verifier) == 0,
            "clean_negative_pass": is_clean and false_positive_count(verifier) == 0,
            "evidence_exact_match_rate": trace.get("evidence_exact_match_rate"),
            "unsupported_evidence_count": len(verifier.get("unsupported_evidence_capabilities", [])),
            "artifact_dir": str(out_dir),
        }
    except Exception as exc:  # noqa: BLE001
        write_text(out_dir / "blocked_or_failed_trace.txt", traceback.format_exc())
        return {
            "case_id": case_payload["case_id"],
            "task_family": case_payload["agent_visible"]["task_family"],
            "source_type": case_payload["source_type"],
            "status": "failed",
            "failure_reason": str(exc),
            "artifact_dir": str(out_dir),
        }


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def summarize(rows: list[dict[str, Any]], source_status: dict[str, dict[str, Any]], backend: str) -> dict[str, Any]:
    completed = [row for row in rows if row.get("status") == "completed"]
    pass_count = sum(1 for row in completed if row.get("effective_pass"))
    fp_count = sum(int(row.get("false_positive_count") or 0) for row in completed)
    unsupported_retained = sum(1 for row in completed if row.get("unsupported_retained"))
    ambiguous_handled = sum(1 for row in completed if row.get("ambiguous_handled"))
    discrepancies = sum(1 for row in completed if not row.get("effective_pass"))
    rates = [float(row["evidence_exact_match_rate"]) for row in completed if row.get("evidence_exact_match_rate") is not None]
    downloaded = sum(1 for item in source_status.values() if item.get("status") == "downloaded")
    return {
        "case_count": len(rows),
        "completed_count": len(completed),
        "pass_count": pass_count,
        "false_positive_count": fp_count,
        "unsupported_retained_count": unsupported_retained,
        "ambiguous_handled_count": ambiguous_handled,
        "discrepancy_count": discrepancies,
        "evidence_exact_match_rate": round(sum(rates) / len(rates), 4) if rates else None,
        "live_llm_pass_rate": round(pass_count / len(completed), 4) if backend == "live_llm_text" and completed else None,
        "public_source_downloaded_count": downloaded,
        "public_source_blocked_count": len(source_status) - downloaded,
        "external_generalization": "pass" if completed and pass_count == len(completed) else ("partial" if completed else "blocked"),
    }


def render_report(payload: dict[str, Any]) -> str:
    lines = [
        "# External Generalization Validation Status",
        "",
        f"Generated at: `{payload['generated_at']}`",
        "",
        "This is a bounded external/semiexternal validation lane. It combines public read-only source excerpts and independently authored holdout cases. It is not an official CyberSecEval, AutoPatchBench, CVE-Bench, or SWE-bench result.",
        "",
        "## Source Acquisition",
        "",
        "| Source | Status | URL | Hash | Artifact |",
        "|---|---|---|---|---|",
    ]
    for source_id, item in payload["source_status"].items():
        lines.append(f"| {source_id} | {item.get('status')} | {item.get('source_url')} | {item.get('sha256')} | `{item.get('path')}` |")
    lines.extend(
        [
            "",
            "## Summary",
            "",
            f"- Backend: `{payload['backend']}`",
            f"- Cases: `{payload['case_count']}`",
            f"- Completed: `{payload['completed_count']}`",
            f"- Effective pass count: `{payload['pass_count']}`",
            f"- False positives: `{payload['false_positive_count']}`",
            f"- Evidence exact match rate: `{payload['evidence_exact_match_rate']}`",
            f"- Unsupported retained count: `{payload['unsupported_retained_count']}`",
            f"- Ambiguous handled count: `{payload['ambiguous_handled_count']}`",
            f"- Discrepancy count: `{payload['discrepancy_count']}`",
            f"- Live LLM pass rate: `{payload['live_llm_pass_rate']}`",
            f"- `external_generalization`: `{payload['external_generalization']}`",
            "",
            "## Rows",
            "",
            "| Case | Source | Family | Status | Group | Verifier | FP | Unsupported retained | Ambiguous handled | Artifacts |",
            "|---|---|---|---|---|---|---:|---:|---:|---|",
        ]
    )
    for row in payload["rows"]:
        lines.append(
            f"| {row['case_id']} | {row.get('source_type')} | {row['task_family']} | {row.get('status')} | "
            f"{row.get('activated_capability_group')} | {row.get('verifier_result')}:{row.get('feedback_type')} | "
            f"{row.get('false_positive_count')} | {row.get('unsupported_retained')} | {row.get('ambiguous_handled')} | `{row.get('artifact_dir')}` |"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- Public repo cases are read-only defensive review demos over source excerpts.",
            "- Labels are local verifier labels; this is not a third-party benchmark score.",
            "- Unsupported dependency, regex DoS, and code-execution review families remain limitations for `secure_code_review`.",
            "- No exploit generation or attack-chain execution was performed.",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run bounded external/semiexternal generalization validation.")
    parser.add_argument("--installed", default="secure_code_review")
    parser.add_argument("--backend", default="live_llm_text", choices=["live_llm_text", "non_oracle_local_semantic", "offline_deterministic"])
    parser.add_argument("--base-url", default=os.environ.get("OPENAI_BASE_URL") or "https://api.deepseek.com")
    parser.add_argument("--model", default=os.environ.get("MODEL") or os.environ.get("OPENAI_MODEL") or "deepseek-v4-flash")
    parser.add_argument("--timeout-seconds", type=float, default=60.0)
    parser.add_argument("--output-dir", default=str(OUTPUT_ROOT))
    args = parser.parse_args(argv)

    output_root = Path(args.output_dir)
    source_status = download_sources(output_root)
    cases = materialize_cases(source_status)
    write_json(output_root / "cases_materialized.json", {"cases": cases})
    specs, pointer, unavailable = mini.build_variant_specs(args.installed)
    active_spec = next(spec for spec in specs if spec.name == "active_installed")
    rows = [
        run_one(
            case_payload=case_payload,
            spec=active_spec,
            pointer=pointer,
            output_root=output_root,
            backend=args.backend,
            base_url=args.base_url,
            model=args.model,
            timeout_seconds=args.timeout_seconds,
        )
        for case_payload in cases
    ]
    summary = summarize(rows, source_status, args.backend)
    payload = {
        "run_id": "external_generalization_validation",
        "generated_at": utc_now(),
        "installed_skill": args.installed,
        "backend": args.backend,
        "model": args.model if args.backend == "live_llm_text" else args.backend,
        "api_key_present": api_key_present() if args.backend == "live_llm_text" else None,
        "source_status": source_status,
        "unavailable_variants": unavailable,
        "rows": rows,
        "claim_boundary": "bounded external/semiexternal validation; not official benchmark",
        **summary,
    }
    write_json(output_root / "external_generalization_summary.json", payload)
    write_text(REPORT, render_report(payload))
    print(json.dumps({"summary": str(output_root / "external_generalization_summary.json"), "report": str(REPORT), "external_generalization": payload["external_generalization"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
