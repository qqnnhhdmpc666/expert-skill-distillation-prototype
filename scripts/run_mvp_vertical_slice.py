from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class Evidence:
    source_id: str
    location: str
    quote: str


@dataclass(frozen=True)
class Rule:
    rule_id: str
    category: str
    priority: str
    rule_text: str
    rationale: str
    compact_check: str
    evidence_terms: tuple[str, ...]


RULES: tuple[Rule, ...] = (
    Rule(
        "R001",
        "auth",
        "high",
        "Every API endpoint must document authentication method and authorization boundary.",
        "Authentication alone is not enough; reviewers need roles, scopes, and failure behavior.",
        "Check whether authentication method, roles/scopes, and auth failure behavior are explicit.",
        ("authentication", "authorization", "roles", "scopes", "login required"),
    ),
    Rule(
        "R002",
        "input_validation",
        "high",
        "Each request field must define required/optional status, type, range, length, and enum constraints.",
        "Missing validation boundaries make client behavior and server-side protection ambiguous.",
        "Check required fields, optional defaults, type, range, length, and enum constraints.",
        ("required", "optional", "type", "range", "length", "enum", "validation"),
    ),
    Rule(
        "R003",
        "error_codes",
        "high",
        "APIs should provide stable error codes for success, invalid input, unauthorized, forbidden, not found, duplicate request, and server failure.",
        "Overly vague error codes make client handling, monitoring, and repair unstable.",
        "Check error codes for validation, auth, permission, not found, duplicate, and server errors.",
        ("error code", "invalid input", "unauthorized", "forbidden", "not found", "duplicate", "server error"),
    ),
    Rule(
        "R004",
        "sensitive_data",
        "high",
        "API responses must not expose tokens, raw secrets, internal stack traces, full identity numbers, or unnecessary personal data.",
        "Sensitive fields should be masked, omitted, or protected by separate authorization.",
        "Check for token, secret, stack trace, full phone or identity exposure in responses.",
        ("sensitive", "access_token", "secrets", "stack traces", "phone number", "personal data"),
    ),
    Rule(
        "R005",
        "response_format",
        "medium",
        "Responses should use a consistent envelope with code, message, request_id, and data.",
        "A stable response envelope makes downstream parsing and troubleshooting predictable.",
        "Check consistent envelope fields: code, message, request_id, and data.",
        ("response envelope", "code", "message", "request_id", "data"),
    ),
    Rule(
        "R006",
        "idempotency",
        "medium",
        "POST, PUT, and PATCH endpoints should explain idempotency or duplicate submission behavior.",
        "Mutation endpoints often fail in retry paths unless duplicate handling is explicit.",
        "Check whether mutation endpoints document idempotency or duplicate submission handling.",
        ("idempotency", "duplicate submission", "POST", "PUT", "PATCH"),
    ),
    Rule(
        "R007",
        "observability",
        "medium",
        "APIs should expose request_id or equivalent trace metadata and document key audit logging requirements.",
        "Troubleshooting and audit review need stable trace identifiers.",
        "Check request_id, trace metadata, and audit logging expectations.",
        ("request identifier", "request_id", "logs", "audit", "troubleshooting"),
    ),
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def load_materials(materials_dir: Path) -> dict[str, str]:
    return {path.name: read_text(path) for path in sorted(materials_dir.glob("*.md"))}


def find_evidence(rule: Rule, materials: dict[str, str]) -> list[Evidence]:
    hits: list[Evidence] = []
    lowered_terms = tuple(term.lower() for term in rule.evidence_terms)
    for source_id, text in materials.items():
        lines = text.splitlines()
        current_heading = "document"
        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith("#"):
                current_heading = stripped.lstrip("#").strip() or current_heading
            searchable = stripped.lower()
            if any(term in searchable for term in lowered_terms):
                quote = stripped
                if quote:
                    hits.append(Evidence(source_id, f"{current_heading}, line {idx}", quote))
                    break
    return hits


def evidence_status(rule: Rule, evidence: list[Evidence]) -> str:
    if not evidence:
        return "unsupported"
    if rule.priority == "high" and len(evidence) >= 2:
        return "supported"
    if any(ev.source_id == "api_design_guidelines.md" for ev in evidence):
        return "supported"
    return "weak"


def build_evidence_map(materials: dict[str, str]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for rule in RULES:
        evidence = find_evidence(rule, materials)
        status = evidence_status(rule, evidence)
        suggestion = ""
        risk = "low"
        if status == "weak":
            risk = "medium"
            suggestion = "Keep in full skill, but treat as advisory until execution evidence confirms impact."
        elif status == "unsupported":
            risk = "high"
            suggestion = "Do not include in compact skill until material or execution evidence is added."
        rows.append(
            {
                "rule_id": rule.rule_id,
                "rule_text": rule.rule_text,
                "category": rule.category,
                "priority": rule.priority,
                "status": status,
                "risk": risk,
                "suggestion": suggestion,
                "evidence": [asdict(ev) for ev in evidence],
            }
        )
    return rows


def render_full_skill(evidence_map: list[dict[str, object]]) -> str:
    lines = [
        "# API Review Full Skill Package",
        "",
        "## Purpose",
        "",
        "Distill API/code review expert knowledge into auditable rules with material evidence, examples, and behavior boundaries.",
        "",
        "## Rules",
        "",
    ]
    by_id = {rule.rule_id: rule for rule in RULES}
    for row in evidence_map:
        rule = by_id[str(row["rule_id"])]
        lines.extend(
            [
                f"### {rule.rule_id}: {rule.category}",
                "",
                f"- Priority: {rule.priority}",
                f"- Status: {row['status']}",
                f"- Rule: {rule.rule_text}",
                f"- Rationale: {rule.rationale}",
                "- Evidence:",
            ]
        )
        evidence = row["evidence"]
        if evidence:
            for ev in evidence:  # type: ignore[assignment]
                lines.append(f"  - {ev['source_id']} ({ev['location']}): {ev['quote']}")
        else:
            lines.append("  - No direct material evidence found.")
        lines.append("")
    lines.extend(
        [
            "## Required Review Output",
            "",
            "Return JSON with `passed`, `failed_rules`, `findings`, and `suggested_patch`.",
            "",
        ]
    )
    return "\n".join(lines)


def render_evidence_report(evidence_map: list[dict[str, object]]) -> str:
    lines = [
        "# Evidence Coverage Report",
        "",
        "| Rule | Priority | Status | Risk | Evidence Count | Suggestion |",
        "|---|---|---|---|---:|---|",
    ]
    for row in evidence_map:
        suggestion = str(row["suggestion"]).replace("|", "\\|")
        lines.append(
            f"| {row['rule_id']} | {row['priority']} | {row['status']} | {row['risk']} | {len(row['evidence'])} | {suggestion} |"
        )
    lines.append("")
    return "\n".join(lines)


def compact_rows(evidence_map: list[dict[str, object]], include_execution_critical: Iterable[str] = ()) -> list[dict[str, object]]:
    critical = set(include_execution_critical)
    return [
        row
        for row in evidence_map
        if (row["status"] == "supported" and row["priority"] == "high") or row["rule_id"] in critical
    ]


def render_compact_skill(evidence_map: list[dict[str, object]], version: str, execution_critical: Iterable[str] = ()) -> str:
    by_id = {rule.rule_id: rule for rule in RULES}
    rows = compact_rows(evidence_map, execution_critical)
    lines = [
        f"# API Review Compact Skill {version}",
        "",
        "Use this skill to review an API specification. Focus on actionable findings, not long explanations.",
        "",
        "## Checklist",
        "",
    ]
    for row in rows:
        rule = by_id[str(row["rule_id"])]
        marker = " execution-critical" if row["rule_id"] in set(execution_critical) else ""
        lines.append(f"- [{rule.rule_id}] {rule.compact_check} Status: {row['status']}.{marker}")
    lines.extend(
        [
            "",
            "## Output Format",
            "",
            "Return JSON only:",
            "",
            "```json",
            "{",
            '  "passed": false,',
            '  "failed_rules": ["R001"],',
            '  "findings": [',
            '    {"rule_id": "R001", "severity": "high", "message": "Finding text", "evidence": "Spec excerpt"}',
            "  ],",
            '  "suggested_patch": ["Concrete API spec improvement"]',
            "}",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def has_any(text: str, terms: Iterable[str]) -> bool:
    lowered = text.lower()
    return any(term.lower() in lowered for term in terms)


def simulate_execution(case_text: str, compact_skill: str, version: str) -> dict[str, object]:
    expected_findings: dict[str, dict[str, str]] = {}
    if "requires login" in case_text.lower() and not has_any(case_text, ("role", "scope", "authorization")):
        expected_findings["R001"] = (
            {
                "rule_id": "R001",
                "severity": "high",
                "message": "The spec only says login is required and does not document roles, scopes, or authorization failure behavior.",
                "evidence": "Notes: The endpoint requires login.",
            }
        )
    if not has_any(case_text, ("required", "optional", "length", "enum", "range")):
        expected_findings["R002"] = (
            {
                "rule_id": "R002",
                "severity": "high",
                "message": "Request fields lack required/optional markers and validation constraints.",
                "evidence": "Request body lists display_name, phone, and avatar_url without constraints.",
            }
        )
    if "500 | server error" in case_text.lower() and not has_any(case_text, ("400", "401", "403", "404", "409")):
        expected_findings["R003"] = (
            {
                "rule_id": "R003",
                "severity": "high",
                "message": "Error code coverage only includes success and server error.",
                "evidence": "Error Codes table lists 0 and 500 only.",
            }
        )
    if has_any(case_text, ("access_token", "13800138000")):
        expected_findings["R004"] = (
            {
                "rule_id": "R004",
                "severity": "high",
                "message": "Response exposes access_token and full phone number.",
                "evidence": "Response data includes access_token and phone.",
            }
        )
    if "request_id" not in case_text.lower():
        expected_findings["R005"] = (
            {
                "rule_id": "R005",
                "severity": "medium",
                "message": "Response envelope lacks request_id.",
                "evidence": "Response includes code, message, and data but no request_id.",
            }
        )
    if "POST " in case_text and not has_any(case_text, ("idempotency", "duplicate")):
        expected_findings["R006"] = (
            {
                "rule_id": "R006",
                "severity": "medium",
                "message": "Mutation endpoint does not explain idempotency or duplicate submission behavior.",
                "evidence": "Endpoint is POST /api/v1/users/{user_id}/profile.",
            }
        )

    active_rules = {rule.rule_id for rule in RULES if has_any(compact_skill, (rule.rule_id,))}
    findings = [finding for rule_id, finding in expected_findings.items() if rule_id in active_rules]
    detected_rules = sorted({finding["rule_id"] for finding in findings})
    expected_rules = sorted(expected_findings)
    missed_rules = sorted(set(expected_rules) - set(detected_rules))
    return {
        "version": version,
        "passed": not missed_rules,
        "expected_rules": expected_rules,
        "detected_rules": detected_rules,
        "missed_rules": missed_rules,
        "findings": findings,
        "checklist_pass": len(detected_rules),
        "checklist_total": len(expected_rules),
        "retry_count": 0,
        "verifier_calls": 1,
        "latency_ms": 0,
    }


def estimate_tokens(text: str) -> int:
    # Fermi estimate for quick cost comparison without external tokenizer dependency.
    return max(1, round(len(text) / 4))


def render_repair_log(execution_report: dict[str, object]) -> tuple[str, set[str]]:
    missed = set(execution_report["missed_rules"])  # type: ignore[arg-type]
    lines = [
        "# Repair Log",
        "",
        "## Execution Feedback",
        "",
        f"- Passed: {execution_report['passed']}",
        f"- Expected rules: {', '.join(execution_report['expected_rules'])}",  # type: ignore[arg-type]
        f"- Detected rules: {', '.join(execution_report['detected_rules'])}",  # type: ignore[arg-type]
        f"- Missed rules: {', '.join(sorted(missed)) if missed else 'none'}",
        "",
        "## Skill Patch",
        "",
    ]
    if "R006" in missed:
        lines.append("- Mark R006 as execution-critical because the demo mutation endpoint failed idempotency review.")
    if "R005" in missed:
        lines.append("- Keep R005 in compact skill because missing request_id was observed during execution.")
    if not missed:
        lines.append("- No patch required.")
    lines.append("")
    critical = {rule_id for rule_id in missed if rule_id in {"R005", "R006", "R007"}}
    return "\n".join(lines), critical


def build_manifest(run_id: str, args: argparse.Namespace, artifact_names: list[str]) -> dict[str, object]:
    return {
        "run_id": run_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "materials_dir": str(args.materials_dir),
        "case_path": str(args.case_path),
        "artifacts": artifact_names,
        "note": "Deterministic MVP runner for artifact-flow validation; replace distiller/judge with LLM or Harbor later.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run deterministic MVP vertical slice artifact flow.")
    parser.add_argument("--materials-dir", type=Path, default=Path("data/api_review_expert_materials"))
    parser.add_argument("--case-path", type=Path, default=Path("data/api_review_cases/case_001_openapi.md"))
    parser.add_argument("--output-root", type=Path, default=Path("outputs/mvp_vertical_slice"))
    parser.add_argument("--run-id", default=datetime.now().strftime("%Y%m%d_%H%M%S"))
    args = parser.parse_args()

    materials = load_materials(args.materials_dir)
    case_text = read_text(args.case_path)
    out_dir = args.output_root / args.run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    evidence_map = build_evidence_map(materials)
    full_skill = render_full_skill(evidence_map)
    compact_v1 = render_compact_skill(evidence_map, "v1")
    execution_v1 = simulate_execution(case_text, compact_v1, "v1")
    repair_log, execution_critical = render_repair_log(execution_v1)
    compact_v2 = render_compact_skill(evidence_map, "v2", execution_critical)
    execution_v2 = simulate_execution(case_text, compact_v2, "v2")

    artifacts = {
        "full_skill.md": full_skill,
        "evidence_report.md": render_evidence_report(evidence_map),
        "compact_skill_v1.md": compact_v1,
        "repair_log.md": repair_log,
        "compact_skill_v2.md": compact_v2,
    }
    for name, content in artifacts.items():
        write_text(out_dir / name, content)

    write_json(out_dir / "evidence_map.json", evidence_map)
    write_json(out_dir / "execution_report_v1.json", execution_v1)
    write_json(out_dir / "execution_report_v2.json", execution_v2)

    cost_summary = {
        "token_estimator": "round(characters / 4)",
        "full_skill_tokens": estimate_tokens(full_skill),
        "compact_skill_v1_tokens": estimate_tokens(compact_v1),
        "compact_skill_v2_tokens": estimate_tokens(compact_v2),
        "compression_ratio_v1": round(estimate_tokens(compact_v1) / estimate_tokens(full_skill), 3),
        "compression_ratio_v2": round(estimate_tokens(compact_v2) / estimate_tokens(full_skill), 3),
        "execution_v1": {
            "retry_count": execution_v1["retry_count"],
            "verifier_calls": execution_v1["verifier_calls"],
            "checklist_pass": execution_v1["checklist_pass"],
            "checklist_total": execution_v1["checklist_total"],
        },
        "execution_v2": {
            "retry_count": execution_v2["retry_count"],
            "verifier_calls": execution_v2["verifier_calls"],
            "checklist_pass": execution_v2["checklist_pass"],
            "checklist_total": execution_v2["checklist_total"],
        },
    }
    write_json(out_dir / "cost_summary.json", cost_summary)

    artifact_names = sorted([*artifacts.keys(), "evidence_map.json", "execution_report_v1.json", "execution_report_v2.json", "cost_summary.json"])
    write_json(out_dir / "manifest.json", build_manifest(args.run_id, args, artifact_names))

    print(json.dumps({"run_id": args.run_id, "output_dir": str(out_dir), "artifacts": artifact_names}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
