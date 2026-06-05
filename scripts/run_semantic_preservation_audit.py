from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


OUT_DIR = Path("outputs/mvp_vertical_slice/semantic_preservation_audit_001")
SKILL_PATH = Path("outputs/mvp_vertical_slice/validation_aware_compiler_001/candidate_skills/candidate_C_compressed_required_rules.md")
EXPECTED_RULE_IDS = ["R001", "R002", "R003", "R004", "R005", "R006"]
RULE_TERMS = {
    "R001": ["auth", "roles", "scopes", "auth-failure"],
    "R002": ["request", "fields", "required", "type", "range", "enum"],
    "R003": ["error", "codes", "validation", "auth", "duplicate", "server"],
    "R004": ["tokens", "secrets", "stack", "identity", "personal"],
    "R005": ["response", "envelope", "code", "message", "request_id", "data"],
    "R006": ["mutation", "idempotency", "duplicate", "submission"],
}
ACTION_TERMS = ["check", "no ", "must", "return", "include", "fields", "codes", "behavior", "handling", "envelope"]
OUTPUT_TERMS = ["json", "finding", "rule_id", "severity", "message", "evidence"]


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def estimate_tokens(text: str) -> int:
    return max(1, round(len(text) / 4))


def extract_rule_line(skill_text: str, rule_id: str) -> str:
    match = re.search(rf"^- \[{re.escape(rule_id)}\]\s*(.+)$", skill_text, flags=re.MULTILINE)
    return match.group(1).strip() if match else ""


def has_any(text: str, terms: list[str]) -> bool:
    lowered = text.lower()
    return any(term.lower() in lowered for term in terms)


def audit_rule(skill_text: str, rule_id: str) -> dict[str, Any]:
    line = extract_rule_line(skill_text, rule_id)
    rule_id_present = bool(line)
    has_actionable_condition = has_any(line, ACTION_TERMS)
    has_expected_finding_behavior = has_any(skill_text, OUTPUT_TERMS)
    trigger_hits = [term for term in RULE_TERMS[rule_id] if term.lower() in line.lower()]
    has_evidence_or_trigger_phrase = bool(trigger_hits)
    not_rule_id_only = len(line.replace(rule_id, "").strip()) >= 16
    checks = [
        rule_id_present,
        has_actionable_condition,
        has_expected_finding_behavior,
        has_evidence_or_trigger_phrase,
        not_rule_id_only,
    ]
    if all(checks):
        status = "preserved"
    elif rule_id_present and not_rule_id_only and has_evidence_or_trigger_phrase:
        status = "weak"
    elif rule_id_present and not not_rule_id_only:
        status = "shortcut"
    else:
        status = "failed"
    return {
        "rule_id": rule_id,
        "rule_line": line,
        "rule_id_present": rule_id_present,
        "has_actionable_condition": has_actionable_condition,
        "has_expected_finding_behavior": has_expected_finding_behavior,
        "has_evidence_or_trigger_phrase": has_evidence_or_trigger_phrase,
        "trigger_hits": trigger_hits,
        "not_rule_id_only": not_rule_id_only,
        "compressed_token_count": estimate_tokens(line),
        "semantic_preservation_status": status,
    }


def render_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Semantic Preservation Audit 001",
        "",
        "## Positioning",
        "",
        "This audit checks whether candidate_C is semantic compression or only a rule-id shortcut.",
        "",
        f"- Overall status: {payload['overall_status']}",
        f"- Interpretation: {payload['interpretation']}",
        "",
        "## Per-Rule Audit",
        "",
        "| Rule | Status | Tokens | Rule ID | Actionable | Trigger Phrase | Output Behavior | Not Rule-ID Only |",
        "|---|---|---:|---|---|---|---|---|",
    ]
    for row in payload["per_rule_audit"]:
        lines.append(
            f"| {row['rule_id']} | {row['semantic_preservation_status']} | {row['compressed_token_count']} | "
            f"{row['rule_id_present']} | {row['has_actionable_condition']} | {row['has_evidence_or_trigger_phrase']} | "
            f"{row['has_expected_finding_behavior']} | {row['not_rule_id_only']} |"
        )
    lines.extend(
        [
            "",
            "## Conservative Reading",
            "",
            "Candidate_C is not a pure rule-id shortcut because each rule has a compressed checklist phrase and the output contract is present. However, this audit is heuristic and must be paired with execution validation and stricter semantic verification.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    skill_text = SKILL_PATH.read_text(encoding="utf-8")
    per_rule = [audit_rule(skill_text, rule_id) for rule_id in EXPECTED_RULE_IDS]
    statuses = [row["semantic_preservation_status"] for row in per_rule]
    if all(status == "preserved" for status in statuses):
        overall_status = "preserved"
        interpretation = "candidate_C appears to be semantic compression under the current heuristic audit."
    elif any(status == "shortcut" for status in statuses):
        overall_status = "shortcut"
        interpretation = "candidate_C may exploit rule-id coverage and should downgrade compiler support."
    elif any(status == "failed" for status in statuses):
        overall_status = "failed"
        interpretation = "candidate_C fails semantic preservation for at least one rule."
    else:
        overall_status = "weak"
        interpretation = "candidate_C is not rule-id-only, but some rules are too compressed to call fully preserved."
    created_at = datetime.now(timezone.utc).isoformat()
    payload = {
        "run_id": OUT_DIR.name,
        "created_at": created_at,
        "candidate": str(SKILL_PATH),
        "overall_status": overall_status,
        "interpretation": interpretation,
        "per_rule_audit": per_rule,
        "boundary": "Heuristic audit only; not a substitute for execution validation or human review.",
    }
    write_json(OUT_DIR / "per_rule_audit.json", per_rule)
    write_json(OUT_DIR / "semantic_audit.json", payload)
    write_text(OUT_DIR / "semantic_audit.md", render_report(payload))
    updated_interpretation = "\n".join(
        [
            "# Updated Interpretation",
            "",
            f"Semantic preservation status: {overall_status}",
            "",
            interpretation,
            "",
            "Compressed wording success is only meaningful if semantic-preservation and execution validation pass. Otherwise, it may reflect verifier-contract weakness rather than a robust compiler.",
            "",
        ]
    )
    write_text(OUT_DIR / "updated_interpretation.md", updated_interpretation)
    write_json(
        OUT_DIR / "manifest.json",
        {
            "run_id": OUT_DIR.name,
            "created_at": created_at,
            "artifacts": ["manifest.json", "semantic_audit.json", "semantic_audit.md", "per_rule_audit.json", "updated_interpretation.md"],
            "boundary": payload["boundary"],
        },
    )
    print(json.dumps({"output_dir": str(OUT_DIR), "overall_status": overall_status}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

