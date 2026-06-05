from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


REQUIRED_RULE_IDS = ["R001", "R002", "R003", "R004", "R005", "R006"]
VALID_CONFIDENCE = {"low", "medium", "high"}
VALID_SEVERITY = {"low", "medium", "high"}
RULE_TERMS = {
    "R001": ["auth", "login", "role", "scope", "authorization", "permission"],
    "R002": ["request", "field", "required", "type", "range", "length", "enum"],
    "R003": ["error", "code", "validation", "auth", "duplicate", "server"],
    "R004": ["token", "secret", "trace", "phone", "identity", "personal"],
    "R005": ["response", "envelope", "code", "message", "request_id", "data"],
    "R006": ["post", "put", "patch", "mutation", "idempot", "duplicate"],
}
TEMPLATE_PATTERNS = ["finding text", "spec excerpt", "placeholder", "todo", "n/a", "rule id only"]


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


def template_like(text: str) -> bool:
    lowered = text.strip().lower()
    if len(lowered) < 6:
        return True
    return any(pattern in lowered for pattern in TEMPLATE_PATTERNS)


def case_relevant(text: str, case_text: str, rule_id: str) -> bool:
    terms = RULE_TERMS.get(rule_id, [])
    lowered_case = case_text.lower()
    available = [term for term in terms if term.lower() in lowered_case]
    return has_any(text, available or terms)


def verify_trace(review_path: Path, case_path: Path) -> dict[str, Any]:
    case_text = read_text(case_path)
    try:
        payload = read_json(review_path)
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "passed": False,
            "failure_type": "output_format_error",
            "trace_errors": [f"review JSON could not be parsed: {exc}"],
            "missing_rule_ids": REQUIRED_RULE_IDS,
        }
    if not isinstance(payload, dict):
        return {
            "passed": False,
            "failure_type": "output_format_error",
            "trace_errors": ["review must be a JSON object"],
            "missing_rule_ids": REQUIRED_RULE_IDS,
        }
    findings = payload.get("findings")
    applications = payload.get("rule_applications")
    trace_errors: list[str] = []
    if not isinstance(findings, list):
        trace_errors.append("findings must be a list")
        findings = []
    if not isinstance(applications, list):
        trace_errors.append("rule_applications must be a list")
        applications = []

    findings_by_id: dict[str, dict[str, Any]] = {}
    seen_rule_ids: set[str] = set()
    for idx, finding in enumerate(findings):
        if not isinstance(finding, dict):
            trace_errors.append(f"finding[{idx}] is not an object")
            continue
        finding_id = str(finding.get("id") or f"F{idx + 1}")
        rule_id = str(finding.get("rule_id", ""))
        issue = str(finding.get("issue") or finding.get("message") or "")
        evidence = str(finding.get("evidence") or "")
        severity = str(finding.get("severity") or "").lower()
        if not re.fullmatch(r"R\d{3}", rule_id):
            trace_errors.append(f"finding[{idx}] has invalid rule_id")
        else:
            seen_rule_ids.add(rule_id)
        if severity not in VALID_SEVERITY:
            trace_errors.append(f"finding[{idx}] has invalid severity")
        if template_like(issue) or template_like(evidence):
            trace_errors.append(f"finding[{idx}] {rule_id or 'unknown'} has template-like issue/evidence")
        if rule_id in REQUIRED_RULE_IDS and not case_relevant(f"{issue} {evidence}", case_text, rule_id):
            trace_errors.append(f"finding[{idx}] {rule_id} lacks case-relevant trigger terms")
        findings_by_id[finding_id] = finding | {"id": finding_id}

    applications_by_finding: dict[str, dict[str, Any]] = {}
    application_rule_ids: set[str] = set()
    for idx, app in enumerate(applications):
        if not isinstance(app, dict):
            trace_errors.append(f"rule_applications[{idx}] is not an object")
            continue
        rule_id = str(app.get("rule_id", ""))
        finding_id = str(app.get("finding_id", ""))
        trigger = str(app.get("trigger_condition_found") or "")
        evidence_span = str(app.get("evidence_span") or "")
        confidence = str(app.get("confidence") or "").lower()
        applicable = app.get("applicable")
        if rule_id in REQUIRED_RULE_IDS:
            application_rule_ids.add(rule_id)
        else:
            trace_errors.append(f"rule_applications[{idx}] has invalid or unexpected rule_id")
        if applicable is not True:
            trace_errors.append(f"rule_applications[{idx}] {rule_id} must mark applicable=true for reported findings")
        if finding_id not in findings_by_id:
            trace_errors.append(f"rule_applications[{idx}] {rule_id} does not point to an existing finding_id")
        elif str(findings_by_id[finding_id].get("rule_id")) != rule_id:
            trace_errors.append(f"rule_applications[{idx}] {rule_id} does not match finding {finding_id}")
        if confidence not in VALID_CONFIDENCE:
            trace_errors.append(f"rule_applications[{idx}] {rule_id} has invalid confidence")
        if template_like(trigger) or template_like(evidence_span):
            trace_errors.append(f"rule_applications[{idx}] {rule_id} has template-like trigger/evidence")
        if not case_relevant(f"{trigger} {evidence_span}", case_text, rule_id):
            trace_errors.append(f"rule_applications[{idx}] {rule_id} lacks case-relevant trigger/evidence")
        applications_by_finding[finding_id] = app

    for finding_id, finding in findings_by_id.items():
        if finding_id not in applications_by_finding:
            trace_errors.append(f"finding {finding_id} has no supporting rule_application")

    missing_rule_ids = [rule_id for rule_id in REQUIRED_RULE_IDS if rule_id not in seen_rule_ids]
    missing_application_rule_ids = [rule_id for rule_id in REQUIRED_RULE_IDS if rule_id not in application_rule_ids]
    if missing_rule_ids:
        trace_errors.append(f"missing findings for {' '.join(missing_rule_ids)}")
    if missing_application_rule_ids:
        trace_errors.append(f"missing rule_applications for {' '.join(missing_application_rule_ids)}")

    passed = not trace_errors
    return {
        "passed": passed,
        "reward": 1.0 if passed else 0.0,
        "failure_type": "none" if passed else "rule_application_trace_error",
        "missing_rule_ids": missing_rule_ids,
        "missing_application_rule_ids": missing_application_rule_ids,
        "trace_errors": trace_errors,
        "seen_rule_ids": sorted(seen_rule_ids),
        "application_rule_ids": sorted(application_rule_ids),
        "message": "trace verifier passed" if passed else "; ".join(trace_errors),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify rule-application trace for API review output.")
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--case", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = verify_trace(args.review, args.case)
    write_json(args.output, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

