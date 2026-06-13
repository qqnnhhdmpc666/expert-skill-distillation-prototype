from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SUITES = [
    (ROOT / "data" / "external_security_mini_suite" / "cases.json", ROOT / "outputs" / "external_security_mini_suite" / "cases"),
    (ROOT / "data" / "external_security_mini_suite" / "holdout_cases.json", ROOT / "outputs" / "external_security_mini_suite" / "holdout" / "cases"),
    (ROOT / "data" / "external_security_mini_suite" / "cases_extended.json", ROOT / "outputs" / "external_security_mini_suite" / "extended" / "cases"),
]
EVOLUTION_OUTPUT = ROOT / "outputs" / "skill_evolution_lab" / "secure_code_review"
INSTALLED_ROOT = ROOT / "outputs" / "installed_skills" / "packages" / "secure_code_review" / "versions"
REPORT = ROOT / "reports" / "ORACLE_LEAKAGE_AUDIT.md"
JSON_REPORT = ROOT / "reports" / "oracle_leakage_audit.json"


FORBIDDEN_AGENT_KEYS = {
    "expected_capability_group",
    "expected_capabilities",
    "expected_security_finding",
    "expected_evidence_span",
    "clean_or_negative",
    "unsupported_limitation",
}


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


def flatten_keys(payload: Any, prefix: str = "") -> list[str]:
    keys: list[str] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            dotted = f"{prefix}.{key}" if prefix else str(key)
            keys.append(dotted)
            keys.extend(flatten_keys(value, dotted))
    elif isinstance(payload, list):
        for idx, value in enumerate(payload):
            keys.extend(flatten_keys(value, f"{prefix}[{idx}]"))
    return keys


def as_search_text(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def text_or_empty(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def exact_oracle_values(verifier_only: dict[str, Any]) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for key in ("expected_security_finding",):
        value = str(verifier_only.get(key) or "").strip()
        if value:
            rows.append((key, value))
    return rows


def scan_text_for_values(text: str, values: list[tuple[str, str]]) -> list[str]:
    hits = []
    for key, value in values:
        if value and value in text:
            hits.append(key)
    return hits


def case_row(case: dict[str, Any], suite_path: Path, output_cases_root: Path) -> dict[str, Any]:
    case_id = str(case["case_id"])
    agent_visible = case.get("agent_visible", {})
    verifier_only = case.get("verifier_only", {})
    agent_keys = set(flatten_keys(agent_visible))
    verifier_keys = set(flatten_keys(verifier_only))
    direct_key_leaks = sorted(key for key in FORBIDDEN_AGENT_KEYS if key in agent_keys)
    oracle_values = exact_oracle_values(verifier_only)
    value_leaks = scan_text_for_values(as_search_text(agent_visible), oracle_values)

    affected: list[str] = []
    if direct_key_leaks or value_leaks:
        affected.append(str(suite_path))

    agent_case = output_cases_root / case_id / "agent_visible_case.json"
    if scan_text_for_values(text_or_empty(agent_case), oracle_values):
        affected.append(str(agent_case))

    for version in ("v1", "v2"):
        skill_path = INSTALLED_ROOT / version / "SKILL.md"
        manifest_path = INSTALLED_ROOT / version / "manifest.json"
        skill_hits = scan_text_for_values(text_or_empty(skill_path), oracle_values)
        manifest_hits = scan_text_for_values(text_or_empty(manifest_path), oracle_values)
        if skill_hits:
            affected.append(str(skill_path))
        if manifest_hits:
            affected.append(str(manifest_path))

    leakage_found = bool(direct_key_leaks or value_leaks or affected)
    return {
        "case_id": case_id,
        "suite": str(suite_path),
        "agent_visible_fields": sorted(agent_keys),
        "verifier_only_fields": sorted(verifier_keys),
        "leakage_found": leakage_found,
        "direct_key_leaks": direct_key_leaks,
        "oracle_value_leaks": value_leaks,
        "affected_artifact": sorted(set(affected)) if affected else [],
        "decision": "needs_fix" if leakage_found else "valid",
        "note": "task_family may equal the expected capability group; this is task conditioning, not verifier-only field leakage.",
    }


def candidate_generation_rows(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    oracle_by_case = {str(case["case_id"]): exact_oracle_values(case.get("verifier_only", {})) for case in cases}
    for path in sorted((EVOLUTION_OUTPUT / "candidates").glob("*/candidate_generation_inputs.json")):
        payload = read_json(path, {})
        text = as_search_text(payload)
        forbidden_keys = sorted(key for key in FORBIDDEN_AGENT_KEYS if key in text)
        value_hits = []
        for case_id, values in oracle_by_case.items():
            for hit in scan_text_for_values(text, values):
                value_hits.append(f"{case_id}:{hit}")
        rows.append(
            {
                "artifact": str(path),
                "forbidden_key_mentions": forbidden_keys,
                "oracle_value_hits": value_hits,
                "leakage_found": bool(forbidden_keys or value_hits or payload.get("verifier_only_oracle_fields_read")),
            }
        )
    return rows


def evidence_bundle_rows(cases: list[dict[str, Any]], suite_outputs: list[tuple[Path, Path]]) -> list[dict[str, Any]]:
    rows = []
    known = {str(case["case_id"]) for case in cases}
    for _suite_path, output_root in suite_outputs:
        if not output_root.exists():
            continue
        for case_dir in sorted(item for item in output_root.iterdir() if item.is_dir() and item.name in known):
            for bundle in sorted(case_dir.glob("*/evidence_bundle/summary.json")):
                payload = read_json(bundle, {})
                provenance = payload.get("provenance", {})
                rows.append(
                    {
                        "case_id": case_dir.name,
                        "artifact": str(bundle),
                        "oracle_fields_visible_to_runner": provenance.get("oracle_fields_visible_to_runner", False),
                        "runtime_source": provenance.get("runtime_source"),
                        "decision": "valid" if provenance.get("oracle_fields_visible_to_runner", False) is False else "needs_fix",
                    }
                )
    return rows


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Oracle Leakage Audit",
        "",
        f"Generated at: `{payload['generated_at']}`",
        "",
        "Scope: local defensive security mini-suite, mini-suite runner artifacts, installed Skill packages, evidence bundles, and candidate-generation inputs.",
        "",
        "## Case-Level Result",
        "",
            "| suite | case_id | agent_visible_fields | verifier_only_fields | leakage_found | affected_artifact | decision |",
            "|---|---|---|---|---|---|---|",
    ]
    for row in payload["case_rows"]:
        lines.append(
            "| {suite} | {case_id} | {agent_visible_fields} | {verifier_only_fields} | {leakage_found} | {affected_artifact} | {decision} |".format(
                suite=Path(row["suite"]).name,
                case_id=row["case_id"],
                agent_visible_fields="<br>".join(row["agent_visible_fields"]),
                verifier_only_fields="<br>".join(row["verifier_only_fields"]),
                leakage_found=row["leakage_found"],
                affected_artifact="<br>".join(row["affected_artifact"]) if row["affected_artifact"] else "none",
                decision=row["decision"],
            )
        )
    lines.extend(
        [
            "",
            "## Candidate Generation Inputs",
            "",
            "| artifact | leakage_found | forbidden_key_mentions | oracle_value_hits |",
            "|---|---:|---|---|",
        ]
    )
    for row in payload["candidate_generation_rows"]:
        lines.append(
            f"| {row['artifact']} | {row['leakage_found']} | {', '.join(row['forbidden_key_mentions']) or 'none'} | {', '.join(row['oracle_value_hits']) or 'none'} |"
        )
    lines.extend(
        [
            "",
            "## Evidence Bundle Runtime Flag",
            "",
            f"- Evidence bundle rows checked: `{len(payload['evidence_bundle_rows'])}`",
            f"- Any runtime oracle visibility issue: `{payload['any_evidence_runtime_leakage']}`",
            "",
            "## Decision",
            "",
            f"- Overall status: `{payload['overall_status']}`",
            "- No case is excluded from security_depth if overall status is `pass`.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    cases: list[dict[str, Any]] = []
    case_rows: list[dict[str, Any]] = []
    suite_outputs: list[tuple[Path, Path]] = []
    for suite_path, output_root in SUITES:
        if not suite_path.exists():
            continue
        suite = read_json(suite_path, {})
        suite_outputs.append((suite_path, output_root))
        for case in suite.get("cases", []):
            cases.append(case)
            case_rows.append(case_row(case, suite_path, output_root))
    candidate_rows = candidate_generation_rows(cases)
    bundle_rows = evidence_bundle_rows(cases, suite_outputs)
    any_leakage = any(row["leakage_found"] for row in case_rows)
    any_candidate_leakage = any(row["leakage_found"] for row in candidate_rows)
    any_bundle_leakage = any(row["decision"] != "valid" for row in bundle_rows)
    payload = {
        "generated_at": utc_now(),
        "overall_status": "fail" if (any_leakage or any_candidate_leakage or any_bundle_leakage) else "pass",
        "case_rows": case_rows,
        "candidate_generation_rows": candidate_rows,
        "evidence_bundle_rows": bundle_rows,
        "any_case_leakage": any_leakage,
        "any_candidate_generation_leakage": any_candidate_leakage,
        "any_evidence_runtime_leakage": any_bundle_leakage,
        "claim_boundary": "The audit checks oracle-field leakage into runner-visible artifacts; verifier reports may contain post-run verifier feedback.",
    }
    write_json(JSON_REPORT, payload)
    write_text(REPORT, render_markdown(payload))
    print(json.dumps({"status": payload["overall_status"], "report": str(REPORT)}, indent=2))
    return 0 if payload["overall_status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
