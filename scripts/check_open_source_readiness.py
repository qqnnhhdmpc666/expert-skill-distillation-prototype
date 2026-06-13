from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports" / "OPEN_SOURCE_READINESS_AUDIT.md"
JSON_REPORT = ROOT / "reports" / "open_source_readiness_audit.json"


REQUIRED_DOCS = [
    "README_PROTOTYPE.md",
    "docs/QUICKSTART.md",
    "docs/CLAIM_BOUNDARY.md",
    "docs/ARTIFACT_TYPES.md",
    "docs/ADDING_A_NEW_SKILL.md",
    "docs/RUNNING_VALIDATION.md",
    "docs/TROUBLESHOOTING.md",
    "docs/RELEASE.md",
    "docs/CLEAN_CLONE_SMOKE.md",
]

REQUIRED_COMMAND_SNIPPETS = [
    "skill-deploy build-codex-skill",
    "skill-deploy install --skill outputs/deployable_codex_skill/secure_code_review --version v2",
    "skill-deploy run-skill --installed secure_code_review",
    "skill-deploy compare-variants",
    "skill-deploy defensive-security-mini-suite",
    "skill-deploy holdout-security-mini-suite",
    "skill-deploy non-oracle-validation",
    "skill-deploy activation-ablation",
    "skill-deploy advanced-evolve",
    "skill-deploy live-llm-validation",
    "skill-deploy improvement-demo",
]

FORBIDDEN_OVERCLAIMS = [
    re.compile(r"\bproduction vulnerability scanner\b", re.IGNORECASE),
    re.compile(r"\breal-world security effectiveness\b", re.IGNORECASE),
    re.compile(r"\bofficial (?:CyberSecEval|AutoPatchBench|CVE-Bench) result\b", re.IGNORECASE),
    re.compile(r"\bSWE-bench success\b", re.IGNORECASE),
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def doc_text() -> str:
    chunks = []
    for rel in REQUIRED_DOCS:
        path = ROOT / rel
        if path.exists():
            chunks.append(path.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(chunks)


def overclaim_rows() -> list[dict[str, Any]]:
    rows = []
    for rel in REQUIRED_DOCS:
        path = ROOT / rel
        text = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
        for pattern in FORBIDDEN_OVERCLAIMS:
            for match in pattern.finditer(text):
                line = text[: match.start()].count("\n") + 1
                context = text[max(0, match.start() - 240) : min(len(text), match.end() + 96)].lower()
                negated = any(
                    marker in context
                    for marker in [
                        "not ",
                        "not a ",
                        "do not claim",
                        "cannot claim",
                        "no ",
                        "what this is not",
                        "what this project is not",
                        "unsupported claims",
                        "unsafe claims",
                    ]
                )
                rows.append(
                    {
                        "doc": rel,
                        "line": line,
                        "match": match.group(0),
                        "negated_or_boundary_context": negated,
                    }
                )
    return rows


def render_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Open-Source Readiness Audit",
        "",
        f"Generated at: `{payload['generated_at']}`",
        "",
        "## Checks",
        "",
        "| Check | Status | Detail |",
        "|---|---|---|",
    ]
    for row in payload["checks"]:
        lines.append(f"| {row['check']} | `{row['status']}` | {row['detail']} |")
    lines.extend(["", "## Overclaim Scan", ""])
    if payload["overclaim_rows"]:
        lines.extend(["| Doc | Line | Match | Boundary context |", "|---|---:|---|---:|"])
        for row in payload["overclaim_rows"]:
            lines.append(f"| {row['doc']} | {row['line']} | {row['match']} | {row['negated_or_boundary_context']} |")
    else:
        lines.append("No forbidden overclaim phrase was found.")
    lines.extend(
        [
            "",
            "## Release Gap Calibration",
            "",
            f"- `open_source_prototype_readiness`: `{payload['open_source_prototype_readiness']}`",
            f"- `public_release_readiness`: `{payload['public_release_readiness']}`",
            "",
            "Missing for clean public release:",
        ]
    )
    for gap in payload["public_release_gaps"]:
        lines.append(f"- {gap}")
    lines.extend(["", "## Decision", "", f"- Overall status: `{payload['overall_status']}`"])
    return "\n".join(lines) + "\n"


def main() -> int:
    text = doc_text()
    checks: list[dict[str, Any]] = []
    for rel in REQUIRED_DOCS:
        checks.append({"check": f"doc_exists:{rel}", "status": "pass" if (ROOT / rel).exists() else "fail", "detail": rel})
    checks.append(
        {
            "check": "review_package_manifest_exists",
            "status": "pass" if (ROOT / "review_package" / "MANIFEST.json").exists() else "fail",
            "detail": "review_package/MANIFEST.json",
        }
    )
    for snippet in REQUIRED_COMMAND_SNIPPETS:
        checks.append({"check": f"command_documented:{snippet}", "status": "pass" if snippet in text else "fail", "detail": snippet})
    overclaims = overclaim_rows()
    unsafe_overclaims = [row for row in overclaims if not row["negated_or_boundary_context"]]
    checks.append({"check": "no_forbidden_overclaim_in_docs", "status": "pass" if not unsafe_overclaims else "fail", "detail": f"unsafe_hits={len(unsafe_overclaims)}"})
    prototype_status = "pass" if all(row["status"] == "pass" for row in checks) else "partial"
    public_release_gaps = [
        "clean-environment smoke has not been run from a fresh clone",
        "dependency/requirements lock has not been reviewed as a release artifact",
        "license and repository metadata are not yet release-complete",
        "one-command demo is not yet guaranteed in a clean environment",
    ]
    payload = {
        "generated_at": utc_now(),
        "checks": checks,
        "overclaim_rows": overclaims,
        "unsafe_overclaim_rows": unsafe_overclaims,
        "open_source_prototype_readiness": prototype_status,
        "public_release_readiness": "partial",
        "public_release_gaps": public_release_gaps,
        "overall_status": prototype_status,
    }
    write_json(JSON_REPORT, payload)
    write_text(REPORT, render_report(payload))
    print(json.dumps({"status": payload["overall_status"], "report": str(REPORT)}, indent=2))
    return 0 if payload["overall_status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
