from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


FINDING_TEMPLATES = {
    "R001": {
        "issue": "The API only says login is required and does not document roles, scopes, or authorization failure behavior.",
        "severity": "high",
        "evidence": "Notes mention login but do not specify roles, scopes, or authorization failure behavior.",
    },
    "R002": {
        "issue": "Request fields lack required/optional markers and validation constraints.",
        "severity": "high",
        "evidence": "Request body lists fields without required/optional status, type constraints, ranges, lengths, or enum values.",
    },
    "R003": {
        "issue": "Error code coverage is incomplete.",
        "severity": "high",
        "evidence": "Error table only includes success and generic server/system error.",
    },
    "R004": {
        "issue": "Response exposes sensitive or internal information.",
        "severity": "high",
        "evidence": "Response contains sensitive personal data, token-like fields, or internal implementation details.",
    },
    "R005": {
        "issue": "Response envelope lacks request_id.",
        "severity": "medium",
        "evidence": "Response includes code, message, and data but no request_id.",
    },
    "R006": {
        "issue": "Mutation endpoint does not explain idempotency or duplicate submission behavior.",
        "severity": "medium",
        "evidence": "Endpoint uses POST/PUT/PATCH but does not document idempotency or duplicate handling.",
    },
}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def extract_rule_ids(compact_skill: str) -> list[str]:
    return sorted(set(re.findall(r"\[(R00[1-6])\]", compact_skill)))


def build_finding(rule_id: str, case_text: str) -> dict[str, str]:
    template = FINDING_TEMPLATES[rule_id]
    finding = {"rule_id": rule_id, **template}
    if rule_id == "R004":
        lowered = case_text.lower()
        if "access_token" in lowered:
            finding["evidence"] = "Response contains access_token."
        elif "internal_trace" in lowered or "customer_phone" in lowered:
            finding["evidence"] = "Response contains internal_trace or customer_phone."
    if rule_id == "R006":
        endpoint_match = re.search(r"`((POST|PUT|PATCH)\s+[^`]+)`", case_text)
        if endpoint_match:
            finding["evidence"] = f"Endpoint is {endpoint_match.group(1)}."
    return finding


def main() -> int:
    parser = argparse.ArgumentParser(description="Mock API review agent driven by compact skill rule IDs.")
    parser.add_argument("--compact-skill", type=Path, required=True)
    parser.add_argument("--case", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    compact_skill = read_text(args.compact_skill)
    case_text = read_text(args.case)
    rule_ids = extract_rule_ids(compact_skill)
    findings = [build_finding(rule_id, case_text) for rule_id in rule_ids]
    payload = {"findings": findings}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"rules": rule_ids, "output": str(args.output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
