from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "review_package"
MANIFEST = PACKAGE / "MANIFEST.json"
REPORT = ROOT / "reports" / "REVIEW_PACKAGE_INTEGRITY_STATUS.md"
JSON_REPORT = ROOT / "reports" / "review_package_integrity_status.json"


KEY_ARTIFACTS = [
    ("reports/RAPID_ADVANCEMENT_SPRINT_STATUS.md", "derived_summary", "skill-deploy representative-matrix + P0-J hardening update"),
    ("reports/REPRESENTATIVE_VALIDATION_MATRIX.md", "derived_summary", "skill-deploy representative-matrix"),
    ("reports/FRAMEWORK_MATURITY_EVIDENCE_LEDGER.md", "derived_summary", "skill-deploy representative-matrix"),
    ("reports/DEFENSIVE_SECURITY_MINI_SUITE_STATUS.md", "fresh_run", "skill-deploy defensive-security-mini-suite"),
    ("outputs/external_security_mini_suite/mini_suite_summary.json", "fresh_run", "skill-deploy defensive-security-mini-suite"),
    ("reports/SWEBENCH_OFFICIAL_HARNESS_INFRA_UNBLOCK_STATUS.md", "infra_blocked", "skill-deploy swebench-infra-unblock"),
    ("reports/NON_ORACLE_VALIDATION_STATUS.md", "fresh_run", "skill-deploy non-oracle-validation"),
    ("outputs/non_oracle_validation/non_oracle_validation_summary.json", "fresh_run", "skill-deploy non-oracle-validation"),
    ("reports/LIVE_LLM_VALIDATION_STATUS.md", "fresh_run", "skill-deploy live-llm-validation"),
    ("outputs/live_llm_validation/live_llm_validation_summary.json", "fresh_run", "skill-deploy live-llm-validation"),
    ("reports/LIVE_CONTRACT_VALIDATION_STATUS.md", "fresh_run", "skill-deploy live-contract-validation"),
    ("outputs/live_contract_validation/live_contract_validation_summary.json", "fresh_run", "skill-deploy live-contract-validation"),
    ("reports/EXTERNAL_GENERALIZATION_VALIDATION_STATUS.md", "fresh_run", "skill-deploy external-generalization"),
    ("outputs/external_generalization_validation/external_generalization_summary.json", "fresh_run", "skill-deploy external-generalization"),
    ("reports/LIVE_MECHANISM_ABLATION_STATUS.md", "fresh_run", "skill-deploy live-mechanism-ablation"),
    ("outputs/mechanism_ablation/live_contract/live_mechanism_ablation_summary.json", "fresh_run", "skill-deploy live-mechanism-ablation"),
    ("reports/CONTRACT_IMPROVEMENT_DEMO_STATUS.md", "fresh_run", "skill-deploy contract-improvement-demo"),
    ("outputs/contract_improvement_demo/contract_improvement_demo_summary.json", "fresh_run", "skill-deploy contract-improvement-demo"),
    ("reports/ITERATIVE_CONTRACT_IMPROVEMENT_STATUS.md", "fresh_run", "skill-deploy iterative-contract-improvement"),
    ("outputs/iterative_contract_improvement/iterative_contract_improvement_summary.json", "fresh_run", "skill-deploy iterative-contract-improvement"),
    ("reports/DEFENSIVE_SECURITY_MINI_SUITE_EXTENDED_STATUS.md", "fresh_run", "skill-deploy defensive-security-mini-suite-extended"),
    ("outputs/external_security_mini_suite/extended/extended_summary.json", "fresh_run", "skill-deploy defensive-security-mini-suite-extended"),
    ("reports/SWEBENCH_INFRA_FINAL_STATUS.md", "infra_blocked", "skill-deploy swebench-infra-final"),
    ("reports/GRAND_AUTONOMOUS_SPRINT_STATUS.md", "derived_summary", "skill-deploy grand-maturity-report"),
    ("reports/ACADEMIC_CLAIM_READINESS_ASSESSMENT.md", "derived_summary", "skill-deploy grand-maturity-report"),
    ("reports/RELEASE_READINESS_CHECKLIST.md", "derived_summary", "skill-deploy grand-maturity-report"),
    ("reports/GITHUB_UPLOAD_STATUS_20260613.md", "derived_summary", "GitHub connector snapshot upload"),
    ("reports/PUBLIC_RELEASE_READINESS_STATUS.md", "fresh_run", "skill-deploy public-release-readiness"),
    ("reports/public_release_readiness_status.json", "fresh_run", "skill-deploy public-release-readiness"),
    ("reports/CLEAN_CLONE_SMOKE_STATUS.md", "fresh_run", "python scripts/run_clean_clone_smoke.py --source . --keep-artifacts"),
    ("outputs/release/clean_clone_smoke/summary.json", "fresh_run", "python scripts/run_clean_clone_smoke.py --source . --keep-artifacts"),
    ("LICENSE", "derived_summary", "release hardening"),
    ("requirements.txt", "derived_summary", "release hardening"),
    ("docs/CLAIM_BOUNDARY.md", "derived_summary", "python scripts/run_claim_boundary_redteam.py"),
    ("docs/QUICKSTART.md", "derived_summary", "manual prototype docs"),
    ("docs/ARTIFACT_TYPES.md", "derived_summary", "manual prototype docs"),
    ("docs/RELEASE.md", "derived_summary", "release hardening docs"),
    ("docs/CLEAN_CLONE_SMOKE.md", "derived_summary", "release hardening docs"),
    ("PROJECT_OVERVIEW_FOR_GITHUB.md", "derived_summary", "github-facing docs"),
    ("docs/ARCHITECTURE_AND_DESIGN.md", "derived_summary", "github-facing docs"),
    ("docs/USER_GUIDE.md", "derived_summary", "github-facing docs"),
    ("HANDOFF_FOR_NEXT_CHAT.md", "derived_summary", "handoff docs"),
    ("docs/RUN_STATE_SUMMARY.md", "derived_summary", "handoff docs"),
    ("docs/REPRODUCE_LATEST_RESULTS.md", "derived_summary", "handoff docs"),
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def infer_review_package_type(path: Path) -> str:
    rel = path.relative_to(PACKAGE).as_posix()
    if "harbor_live_skeleton" in rel or "external_security_validation" in rel:
        return "scaffold"
    if "evidence_bundle" in rel or "validation" in rel:
        return "fresh_run"
    return "derived_summary"


def build_manifest_entries() -> tuple[list[dict[str, Any]], list[str]]:
    entries: list[dict[str, Any]] = []
    issues: list[str] = []
    for path in sorted(PACKAGE.rglob("*")):
        if not path.is_file() or path == MANIFEST:
            continue
        entries.append(
            {
                "artifact_path": str(path.relative_to(ROOT)).replace("\\", "/"),
                "artifact_type": infer_review_package_type(path),
                "sha256": sha256_file(path),
                "generated_by": "existing review_package artifact",
                "evidence_type": infer_review_package_type(path),
                "exists": True,
            }
        )
    for rel, evidence_type, generated_by in KEY_ARTIFACTS:
        path = ROOT / rel
        if not path.exists():
            issues.append(f"missing key artifact: {rel}")
            entries.append(
                {
                    "artifact_path": rel,
                    "artifact_type": evidence_type,
                    "sha256": None,
                    "generated_by": generated_by,
                    "evidence_type": evidence_type,
                    "exists": False,
                }
            )
            continue
        entries.append(
            {
                "artifact_path": rel,
                "artifact_type": evidence_type,
                "sha256": sha256_file(path),
                "generated_by": generated_by,
                "evidence_type": evidence_type,
                "exists": True,
            }
        )
    return entries, issues


def verify_entries(entries: list[dict[str, Any]]) -> list[str]:
    issues = []
    for entry in entries:
        if not entry.get("exists"):
            continue
        path = ROOT / str(entry["artifact_path"])
        if not path.exists():
            issues.append(f"manifest listed missing artifact: {entry['artifact_path']}")
            continue
        current = sha256_file(path)
        if current != entry.get("sha256"):
            issues.append(f"hash mismatch: {entry['artifact_path']}")
    return issues


def render_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Review Package Integrity Status",
        "",
        f"Generated at: `{payload['generated_at']}`",
        f"Manifest: `{payload['manifest_path']}`",
        "",
        "## Summary",
        "",
        f"- Artifact entries: `{payload['artifact_count']}`",
        f"- Missing artifact issues: `{len(payload['missing_or_hash_issues'])}`",
        f"- Verification issues: `{len(payload['verification_issues'])}`",
        f"- Overall status: `{payload['overall_status']}`",
        "",
        "## Evidence Type Counts",
        "",
    ]
    for key, value in sorted(payload["evidence_type_counts"].items()):
        lines.append(f"- `{key}`: `{value}`")
    if payload["missing_or_hash_issues"] or payload["verification_issues"]:
        lines.extend(["", "## Issues", ""])
        for issue in payload["missing_or_hash_issues"] + payload["verification_issues"]:
            lines.append(f"- {issue}")
    lines.extend(
        [
            "",
            "## Note",
            "",
            "`review_package/MANIFEST.json` is not self-hashed to avoid recursive manifest drift.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    entries, missing_issues = build_manifest_entries()
    payload = {
        "generated_at": utc_now(),
        "schema_version": "review_package_manifest.v1",
        "artifact_count": len(entries),
        "artifacts": entries,
    }
    write_json(MANIFEST, payload)
    verification_issues = verify_entries(entries)
    evidence_counts: dict[str, int] = {}
    for entry in entries:
        evidence_type = str(entry.get("evidence_type") or "unknown")
        evidence_counts[evidence_type] = evidence_counts.get(evidence_type, 0) + 1
    status = {
        "generated_at": utc_now(),
        "manifest_path": str(MANIFEST),
        "artifact_count": len(entries),
        "evidence_type_counts": evidence_counts,
        "missing_or_hash_issues": missing_issues,
        "verification_issues": verification_issues,
        "overall_status": "pass" if not missing_issues and not verification_issues else "needs_fix",
    }
    write_json(JSON_REPORT, status)
    write_text(REPORT, render_report(status))
    print(json.dumps({"status": status["overall_status"], "manifest": str(MANIFEST), "report": str(REPORT)}, indent=2))
    return 0 if status["overall_status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
