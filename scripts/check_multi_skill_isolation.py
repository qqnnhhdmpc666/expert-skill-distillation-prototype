from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RUN_ROOT = ROOT / "outputs" / "runtime_runs" / "installed_skills"
POINTER_ROOT = ROOT / "outputs" / "installed_skills" / "active_skill_pointers"
REPORT = ROOT / "reports" / "MULTI_SKILL_ISOLATION_STATUS.md"
JSON_REPORT = ROOT / "reports" / "multi_skill_isolation_status.json"


CHECKS = [
    {
        "command": "skill-deploy run-skill --installed secure_code_review --case upload_security_001 --backend offline_deterministic",
        "skill_id": "secure_code_review",
        "case_id": "upload_security_001",
        "forbidden_skill_id": "software_patch_review",
    },
    {
        "command": "skill-deploy run-skill --installed software_patch_review --case software_patch_review_001 --backend offline_deterministic",
        "skill_id": "software_patch_review",
        "case_id": "software_patch_review_001",
        "forbidden_skill_id": "secure_code_review",
    },
    {
        "command": "skill-deploy run-skill --installed secure_code_review --case config_security_001 --backend offline_deterministic",
        "skill_id": "secure_code_review",
        "case_id": "config_security_001",
        "forbidden_skill_id": "software_patch_review",
    },
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def latest_run_dir(skill_id: str, case_id: str) -> Path | None:
    case_root = RUN_ROOT / skill_id / case_id
    if not case_root.exists():
        return None
    dirs = [item for item in case_root.iterdir() if item.is_dir()]
    if not dirs:
        return None
    return max(dirs, key=lambda item: item.stat().st_mtime)


def check_row(spec: dict[str, str]) -> dict[str, Any]:
    pointer = read_json(POINTER_ROOT / f"{spec['skill_id']}.json", {})
    run_dir = latest_run_dir(spec["skill_id"], spec["case_id"])
    summary = read_json(run_dir / "run_summary.json", {}) if run_dir else {}
    bundle_summary = read_json(run_dir / "evidence_bundle" / "summary.json", {}) if run_dir else {}
    provenance = bundle_summary.get("provenance", {})
    skill_package_path = str(summary.get("skill_package_path") or provenance.get("skill_package_path") or "")
    skill_id_ok = summary.get("skill_id") == spec["skill_id"]
    pointer_ok = str(pointer.get("skill_dir") or "") == skill_package_path
    forbidden_not_read = spec["forbidden_skill_id"] not in skill_package_path
    hash_ok = bool(summary.get("skill_hash")) and summary.get("skill_hash") == provenance.get("skill_hash")
    manifest_ok = bool(summary.get("manifest_hash")) and summary.get("manifest_hash") == provenance.get("manifest_hash")
    return {
        "command": spec["command"],
        "skill_id": spec["skill_id"],
        "case_id": spec["case_id"],
        "run_dir": str(run_dir) if run_dir else "missing",
        "per_skill_pointer": str(POINTER_ROOT / f"{spec['skill_id']}.json"),
        "pointer_skill_dir": pointer.get("skill_dir"),
        "skill_package_path": skill_package_path,
        "skill_hash": summary.get("skill_hash"),
        "manifest_hash": summary.get("manifest_hash"),
        "skill_id_ok": skill_id_ok,
        "pointer_ok": pointer_ok,
        "forbidden_package_not_read": forbidden_not_read,
        "hash_ok": hash_ok,
        "manifest_hash_ok": manifest_ok,
        "verifier_pass": summary.get("pass"),
        "decision": "pass" if all([skill_id_ok, pointer_ok, forbidden_not_read, hash_ok, manifest_ok]) else "fail",
    }


def render_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Multi-Skill Isolation Status",
        "",
        f"Generated at: `{payload['generated_at']}`",
        "",
        "## Fresh Commands",
        "",
        "```powershell",
        *[row["command"] for row in CHECKS],
        "```",
        "",
        "## Isolation Checks",
        "",
        "| Skill | Case | Decision | Pointer ok | Forbidden package not read | Hash ok | Manifest ok | Evidence |",
        "|---|---|---|---:|---:|---:|---:|---|",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| {row['skill_id']} | {row['case_id']} | {row['decision']} | {row['pointer_ok']} | "
            f"{row['forbidden_package_not_read']} | {row['hash_ok']} | {row['manifest_hash_ok']} | {row['run_dir']} |"
        )
    lines.extend(["", "## Decision", "", f"- Overall status: `{payload['overall_status']}`"])
    return "\n".join(lines) + "\n"


def main() -> int:
    rows = [check_row(spec) for spec in CHECKS]
    payload = {
        "generated_at": utc_now(),
        "rows": rows,
        "overall_status": "pass" if all(row["decision"] == "pass" for row in rows) else "fail",
        "boundary": "Checks per-skill active pointer isolation only; this is not a production package manager concurrency test.",
    }
    write_json(JSON_REPORT, payload)
    write_text(REPORT, render_report(payload))
    print(json.dumps({"status": payload["overall_status"], "report": str(REPORT)}, indent=2))
    return 0 if payload["overall_status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
