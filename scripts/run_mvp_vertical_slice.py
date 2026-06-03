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
        ("response envelope", "consistent envelope", "request_id", "paginated endpoints"),
    ),
    Rule(
        "R006",
        "idempotency",
        "medium",
        "POST, PUT, and PATCH endpoints should explain idempotency or duplicate submission behavior.",
        "Mutation endpoints often fail in retry paths unless duplicate handling is explicit.",
        "Check whether mutation endpoints document idempotency or duplicate submission handling.",
        ("idempotency", "duplicate submission", "duplicate request"),
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


def contains_term(text: str, term: str) -> bool:
    lowered = text.lower()
    needle = term.lower()
    if re.fullmatch(r"[a-z0-9_]+", needle):
        return re.search(rf"\b{re.escape(needle)}\b", lowered) is not None
    return needle in lowered


def find_evidence(rule: Rule, materials: dict[str, str]) -> list[Evidence]:
    hits: list[Evidence] = []
    for source_id, text in materials.items():
        lines = text.splitlines()
        current_heading = "document"
        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith("#"):
                current_heading = stripped.lstrip("#").strip() or current_heading
            if any(contains_term(stripped, term) for term in rule.evidence_terms):
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


def evidence_refs(row: dict[str, object]) -> list[str]:
    refs: list[str] = []
    for ev in row["evidence"]:  # type: ignore[assignment]
        refs.append(f"{ev['source_id']}:{ev['location']}")
    return refs


def build_initial_rule_ledger(evidence_map: list[dict[str, object]]) -> list[dict[str, object]]:
    ledger: list[dict[str, object]] = []
    for row in evidence_map:
        keep_v1 = row["status"] == "supported" and row["priority"] == "high"
        decision_v1 = "keep" if keep_v1 else "drop"
        cost_status = "compact_keep" if keep_v1 else "compact_drop"
        reason = (
            "High-priority supported rule retained in compact v1."
            if keep_v1
            else "Dropped from compact v1 to keep initial invocation lightweight; can be patched back by execution evidence."
        )
        ledger.append(
            {
                "rule_id": row["rule_id"],
                "rule_text": row["rule_text"],
                "category": row["category"],
                "priority": row["priority"],
                "source": "material_seed",
                "material_evidence": evidence_refs(row),
                "material_status": row["status"],
                "execution_status": "not_observed",
                "cost_status": cost_status,
                "decision_v1": decision_v1,
                "decision_v2": decision_v1,
                "decision_reason_v1": reason,
                "decision_reason_v2": "No execution feedback has been applied yet.",
                "patches": [],
            }
        )
    return ledger


def update_rule_ledger_with_execution(ledger: list[dict[str, object]], execution_report: dict[str, object]) -> list[dict[str, object]]:
    detected = set(execution_report["detected_rules"])  # type: ignore[arg-type]
    missed = set(execution_report["missed_rules"])  # type: ignore[arg-type]
    expected = set(execution_report["expected_rules"])  # type: ignore[arg-type]
    updated: list[dict[str, object]] = []
    for row in ledger:
        next_row = dict(row)
        rule_id = str(row["rule_id"])
        patches = list(row["patches"])  # type: ignore[arg-type]
        if rule_id in missed:
            next_row["execution_status"] = "failure_critical"
            next_row["cost_status"] = "compact_patch"
            next_row["decision_v2"] = "patch"
            next_row["decision_reason_v2"] = "Compact v1 missed this expected task rule; execution feedback promotes it into compact v2."
            patches.append(
                {
                    "patch_id": f"P-{rule_id}-v2",
                    "source": "execution_report_v1.json",
                    "failure_type": "missing_rule",
                    "action": "patch_into_compact_v2",
                    "reason": "The rule was needed by the task but absent from compact v1.",
                }
            )
        elif rule_id in detected:
            next_row["execution_status"] = "detected"
            next_row["decision_v2"] = "keep"
            next_row["decision_reason_v2"] = "Compact v1 detected this rule; keep it in compact v2."
        elif rule_id in expected:
            next_row["execution_status"] = "unused"
            next_row["decision_reason_v2"] = "Expected by the task but not active; no patch was selected."
        else:
            next_row["execution_status"] = "unused"
            next_row["decision_reason_v2"] = "Not triggered by this execution case; keep the initial compact decision."
        next_row["patches"] = patches
        updated.append(next_row)
    return updated


def compact_rows_from_ledger(evidence_map: list[dict[str, object]], ledger: list[dict[str, object]], version: str) -> list[dict[str, object]]:
    rows_by_id = {str(row["rule_id"]): row for row in evidence_map}
    decision_key = f"decision_{version}"
    compact_rows: list[dict[str, object]] = []
    for entry in ledger:
        decision = str(entry[decision_key])
        if decision in {"keep", "compress", "patch"}:
            row = dict(rows_by_id[str(entry["rule_id"])])
            row["ledger_decision"] = decision
            row["ledger_reason"] = entry[f"decision_reason_{version}"]
            row["execution_status"] = entry["execution_status"]
            compact_rows.append(row)
    return compact_rows


def render_compact_skill(evidence_map: list[dict[str, object]], ledger: list[dict[str, object]], version: str) -> str:
    by_id = {rule.rule_id: rule for rule in RULES}
    rows = compact_rows_from_ledger(evidence_map, ledger, version)
    lines = [
        f"# API Review Compact Skill {version}",
        "",
        "Use this skill to review an API specification. The checklist is selected from rule_ledger decisions.",
        "",
        "## Checklist",
        "",
    ]
    for row in rows:
        rule = by_id[str(row["rule_id"])]
        lines.append(
            f"- [{rule.rule_id}] {rule.compact_check} "
            f"Decision: {row['ledger_decision']}; material: {row['status']}; execution: {row['execution_status']}."
        )
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


def render_repair_log(execution_report: dict[str, object], ledger: list[dict[str, object]]) -> str:
    missed = set(execution_report["missed_rules"])  # type: ignore[arg-type]
    ledger_by_id = {str(row["rule_id"]): row for row in ledger}
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
    for rule_id in sorted(missed):
        entry = ledger_by_id[rule_id]
        lines.extend(
            [
                f"### Patch {rule_id}",
                "",
                f"- Failure type: missing_rule",
                f"- Affected rule: {rule_id}",
                f"- Material status: {entry['material_status']}",
                f"- Decision: {entry['decision_v2']}",
                f"- Reason: {entry['decision_reason_v2']}",
                "",
            ]
        )
    if not missed:
        lines.append("- No patch required.")
    lines.append("")
    return "\n".join(lines)


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
    initial_ledger = build_initial_rule_ledger(evidence_map)
    full_skill = render_full_skill(evidence_map)
    compact_v1 = render_compact_skill(evidence_map, initial_ledger, "v1")
    execution_v1 = simulate_execution(case_text, compact_v1, "v1")
    rule_ledger = update_rule_ledger_with_execution(initial_ledger, execution_v1)
    repair_log = render_repair_log(execution_v1, rule_ledger)
    compact_v2 = render_compact_skill(evidence_map, rule_ledger, "v2")
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
    write_json(out_dir / "rule_ledger.json", rule_ledger)
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

    artifact_names = sorted(
        [*artifacts.keys(), "evidence_map.json", "rule_ledger.json", "execution_report_v1.json", "execution_report_v2.json", "cost_summary.json"]
    )
    write_json(out_dir / "manifest.json", build_manifest(args.run_id, args, artifact_names))

    print(json.dumps({"run_id": args.run_id, "output_dir": str(out_dir), "artifacts": artifact_names}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
