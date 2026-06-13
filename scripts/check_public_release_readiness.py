from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports" / "PUBLIC_RELEASE_READINESS_STATUS.md"
JSON_REPORT = ROOT / "reports" / "public_release_readiness_status.json"


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


def render(payload: dict[str, Any]) -> str:
    lines = [
        "# Public Release Readiness Status",
        "",
        f"Generated at: `{payload['generated_at']}`",
        "",
        "| Check | Status | Detail |",
        "|---|---|---|",
    ]
    for row in payload["checks"]:
        lines.append(f"| {row['check']} | `{row['status']}` | {row['detail']} |")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- `open_source_prototype_readiness`: `{payload['open_source_prototype_readiness']}`",
            f"- `public_release_readiness`: `{payload['public_release_readiness']}`",
            "",
            "## Boundary",
            "",
            "Passing this checklist means the prototype has local release hygiene. It does not make the system a production security tool or an official benchmark result.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    clean = read_json(ROOT / "outputs" / "release" / "clean_clone_smoke" / "summary.json", {})
    checks = [
        {"check": "license_exists", "status": "pass" if (ROOT / "LICENSE").exists() else "partial", "detail": "LICENSE"},
        {"check": "requirements_exists", "status": "pass" if (ROOT / "requirements.txt").exists() else "partial", "detail": "requirements.txt"},
        {"check": "lock_exists", "status": "pass" if (ROOT / "uv.lock").exists() else "partial", "detail": "uv.lock"},
        {"check": "release_doc_exists", "status": "pass" if (ROOT / "docs" / "RELEASE.md").exists() else "partial", "detail": "docs/RELEASE.md"},
        {"check": "clean_smoke_doc_exists", "status": "pass" if (ROOT / "docs" / "CLEAN_CLONE_SMOKE.md").exists() else "partial", "detail": "docs/CLEAN_CLONE_SMOKE.md"},
        {"check": "clean_environment_smoke", "status": "pass" if clean.get("overall_status") == "pass" else "fail", "detail": clean.get("worktree", "missing")},
    ]
    prototype = "pass"
    public = "pass" if all(row["status"] == "pass" for row in checks) else "partial"
    payload = {
        "generated_at": utc_now(),
        "checks": checks,
        "open_source_prototype_readiness": prototype,
        "public_release_readiness": public,
        "clean_environment_smoke": "pass" if clean.get("overall_status") == "pass" else "fail",
        "requirements_lock_reviewed": "pass" if (ROOT / "requirements.txt").exists() and (ROOT / "uv.lock").exists() else "partial",
        "license_and_repo_metadata": "pass" if (ROOT / "LICENSE").exists() and (ROOT / "pyproject.toml").exists() else "partial",
        "one_command_demo": "pass" if clean.get("overall_status") == "pass" else "partial",
    }
    write_json(JSON_REPORT, payload)
    write_text(REPORT, render(payload))
    print(json.dumps({"report": str(REPORT), "public_release_readiness": public}, indent=2))
    return 0 if public == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
