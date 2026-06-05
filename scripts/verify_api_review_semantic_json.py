from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


REQUIRED_RULE_IDS = ["R001", "R002", "R003", "R004", "R005", "R006"]
REQUIRED_FINDING_FIELDS = ["rule_id", "issue", "severity", "evidence"]
RULE_TRIGGER_TERMS = {
    "R001": ["auth", "login", "role", "scope", "permission", "authorization"],
    "R002": ["required", "optional", "type", "range", "length", "enum", "field"],
    "R003": ["error", "code", "invalid", "unauthorized", "duplicate", "server"],
    "R004": ["token", "secret", "trace", "phone", "identity", "personal"],
    "R005": ["envelope", "code", "message", "request_id", "data"],
    "R006": ["post", "put", "patch", "idempot", "duplicate", "submission"],
}
CASE_TRIGGER_TERMS = {
    "R001": ["login", "role", "scope", "authorization", "auth"],
    "R002": ["request", "field", "required", "type", "enum", "length"],
    "R003": ["error", "code", "server", "invalid", "duplicate"],
    "R004": ["access_token", "internal_trace", "phone", "identity", "sensitive"],
    "R005": ["code", "message", "data", "request_id", "response"],
    "R006": ["post", "put", "patch", "idempotency", "duplicate"],
}
TEMPLATE_PATTERNS = [
    "finding text",
    "spec excerpt",
    "todo",
    "n/a",
    "placeholder",
    "example finding",
]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def has_any(text: str, terms: list[str]) -> bool:
    lowered = text.lower()
    return any(term.lower() in lowered for term in terms)


def is_template_text(text: str) -> bool:
    stripped = text.strip().lower()
    if len(stripped) < 8:
        return True
    return any(pattern in stripped for pattern in TEMPLATE_PATTERNS)


def verify_review_semantic(review_path: Path, case_path: Path) -> dict[str, Any]:
    case_text = read_text(case_path)
    case_lower = case_text.lower()
    try:
        payload = read_json(review_path)
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "passed": False,
            "reward": 0.0,
            "failure_type": "output_format_error",
            "missing_rule_ids": REQUIRED_RULE_IDS,
            "semantic_errors": [f"review.json could not be parsed: {exc}"],
            "message": f"review.json could not be parsed: {exc}",
        }
    findings = payload.get("findings") if isinstance(payload, dict) else None
    if not isinstance(findings, list):
        return {
            "passed": False,
            "reward": 0.0,
            "failure_type": "output_format_error",
            "missing_rule_ids": REQUIRED_RULE_IDS,
            "semantic_errors": ["review.json must contain a findings array"],
            "message": "review.json must contain a findings array.",
        }

    seen_rule_ids: set[str] = set()
    semantic_errors: list[str] = []
    per_finding: list[dict[str, Any]] = []
    for index, finding in enumerate(findings):
        if not isinstance(finding, dict):
            semantic_errors.append(f"finding[{index}] is not an object")
            continue
        missing_fields = [field for field in REQUIRED_FINDING_FIELDS if not str(finding.get(field, "")).strip()]
        rule_id = str(finding.get("rule_id", ""))
        issue = str(finding.get("issue") or finding.get("message") or "")
        evidence = str(finding.get("evidence") or "")
        finding_text = f"{issue} {evidence}"
        field_ok = not missing_fields and re.fullmatch(r"R\d{3}", rule_id) is not None
        if re.fullmatch(r"R\d{3}", rule_id):
            seen_rule_ids.add(rule_id)
        rule_terms = RULE_TRIGGER_TERMS.get(rule_id, [])
        case_terms = CASE_TRIGGER_TERMS.get(rule_id, [])
        has_rule_trigger = has_any(finding_text, rule_terms)
        has_case_related_trigger = has_any(finding_text, [term for term in case_terms if term in case_lower] or case_terms)
        template_like = is_template_text(issue) or is_template_text(evidence)
        finding_ok = field_ok and has_rule_trigger and has_case_related_trigger and not template_like
        if missing_fields:
            semantic_errors.append(f"finding[{index}] missing fields: {', '.join(missing_fields)}")
        if rule_id in REQUIRED_RULE_IDS and not has_rule_trigger:
            semantic_errors.append(f"finding[{index}] {rule_id} lacks rule trigger terms")
        if rule_id in REQUIRED_RULE_IDS and not has_case_related_trigger:
            semantic_errors.append(f"finding[{index}] {rule_id} lacks case-related trigger terms")
        if template_like:
            semantic_errors.append(f"finding[{index}] {rule_id or 'unknown'} looks template-like")
        per_finding.append(
            {
                "index": index,
                "rule_id": rule_id,
                "field_ok": field_ok,
                "has_rule_trigger": has_rule_trigger,
                "has_case_related_trigger": has_case_related_trigger,
                "template_like": template_like,
                "semantic_ok": finding_ok,
            }
        )
    missing_rule_ids = [rule_id for rule_id in REQUIRED_RULE_IDS if rule_id not in seen_rule_ids]
    if missing_rule_ids:
        semantic_errors.append(f"missing expected findings for {' '.join(missing_rule_ids)}")
    passed = not missing_rule_ids and not semantic_errors
    failure_type = "none" if passed else ("missing_rule" if missing_rule_ids else "semantic_content_error")
    return {
        "passed": passed,
        "reward": 1.0 if passed else 0.0,
        "failure_type": failure_type,
        "missing_rule_ids": missing_rule_ids,
        "semantic_errors": semantic_errors,
        "per_finding": per_finding,
        "message": "semantic verifier passed" if passed else "; ".join(semantic_errors),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Stricter local semantic verifier for API review JSON.")
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--case", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = verify_review_semantic(args.review, args.case)
    write_json(args.output, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
