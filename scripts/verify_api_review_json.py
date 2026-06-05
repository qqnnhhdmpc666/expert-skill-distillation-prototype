from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


REQUIRED_RULE_IDS = ["R001", "R002", "R003", "R004", "R005", "R006"]
REQUIRED_FINDING_FIELDS = ["rule_id", "issue", "severity", "evidence"]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def verify_review(path: Path) -> dict[str, Any]:
    try:
        payload = read_json(path)
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "passed": False,
            "reward": 0.0,
            "failure_type": "output_format_error",
            "missing_rule_ids": REQUIRED_RULE_IDS,
            "message": f"review.json could not be parsed: {exc}",
        }
    findings = payload.get("findings") if isinstance(payload, dict) else None
    if not isinstance(findings, list):
        return {
            "passed": False,
            "reward": 0.0,
            "failure_type": "output_format_error",
            "missing_rule_ids": REQUIRED_RULE_IDS,
            "message": "review.json must contain a findings array.",
        }
    field_errors: list[str] = []
    seen_rule_ids: set[str] = set()
    for index, finding in enumerate(findings):
        if not isinstance(finding, dict):
            field_errors.append(f"finding[{index}] is not an object")
            continue
        missing_fields = [field for field in REQUIRED_FINDING_FIELDS if field not in finding]
        if missing_fields:
            field_errors.append(f"finding[{index}] missing fields: {', '.join(missing_fields)}")
        rule_id = str(finding.get("rule_id", ""))
        if re.fullmatch(r"R\d{3}", rule_id):
            seen_rule_ids.add(rule_id)
    if field_errors:
        return {
            "passed": False,
            "reward": 0.0,
            "failure_type": "output_format_error",
            "missing_rule_ids": [rule_id for rule_id in REQUIRED_RULE_IDS if rule_id not in seen_rule_ids],
            "message": "; ".join(field_errors),
        }
    missing_rule_ids = [rule_id for rule_id in REQUIRED_RULE_IDS if rule_id not in seen_rule_ids]
    if missing_rule_ids:
        return {
            "passed": False,
            "reward": 0.0,
            "failure_type": "missing_rule",
            "missing_rule_ids": missing_rule_ids,
            "message": f"missing expected findings for {' '.join(missing_rule_ids)}",
        }
    return {
        "passed": True,
        "reward": 1.0,
        "failure_type": "none",
        "missing_rule_ids": [],
        "message": "review.json covers required rule ids R001-R006",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify an API review JSON with the same rule-id contract as Harbor test.sh.")
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = verify_review(args.review)
    write_json(args.output, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
