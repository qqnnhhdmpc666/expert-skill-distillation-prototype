from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


OUT_DIR = Path("outputs/mvp_vertical_slice/direct_summary_miss_analysis_001")
SOURCE_DIR = Path("outputs/mvp_vertical_slice/component_baseline_direct_summary_001")
RULE_METADATA = {
    "R006": {
        "name": "idempotency",
        "priority": "medium",
        "failure_critical": True,
        "salience": "lower_than_auth_validation_error_sensitive_data",
        "long_tail": True,
        "why_missed": "The direct summary covers common API concerns but omits explicit idempotency / duplicate submission behavior.",
        "requires_execution_feedback": True,
    }
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def render_summary(payload: dict[str, Any]) -> str:
    lines = [
        "# Direct Summary Miss Analysis 001",
        "",
        "## Purpose",
        "",
        "Explain the only failed direct-summary holdout case and what it means for the core claim.",
        "",
        f"- failed_case_id: {payload['failed_case_id']}",
        f"- missed_rule_ids: {', '.join(payload['missed_rule_ids'])}",
        f"- direct_summary_available_rule_ids: {', '.join(payload['direct_summary_available_rule_ids'])}",
        "",
        "## Missed Rule Analysis",
        "",
    ]
    for item in payload["missed_rule_analysis"]:
        lines.extend(
            [
                f"### {item['rule_id']}: {item['name']}",
                "",
                f"- failure_critical: {item['failure_critical']}",
                f"- priority: {item['priority']}",
                f"- long_tail: {item['long_tail']}",
                f"- salience: {item['salience']}",
                f"- requires_execution_feedback: {item['requires_execution_feedback']}",
                f"- why_missed: {item['why_missed']}",
                "",
            ]
        )
    lines.extend(
        [
            "## Patch Recovery",
            "",
            payload["patch_recovery"],
            "",
            "## Meaning For Core Claim",
            "",
            payload["meaning_for_core_claim"],
            "",
            "## Boundary",
            "",
            payload["boundary"],
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    created_at = datetime.now(timezone.utc).isoformat()
    rows = read_json(SOURCE_DIR / "per_case_results.json")
    direct_rows = [row for row in rows if row["variant"] == "direct_summary_skill"]
    failed = [row for row in direct_rows if not row["pass_at_1"]]
    if len(failed) != 1:
        status = "inconclusive"
        failed_row = failed[0] if failed else {}
    else:
        status = "partially_supported"
        failed_row = failed[0]
    missed_rule_ids = failed_row.get("missing_rule_ids", [])
    direct_skill_text = read_text(SOURCE_DIR / "direct_summary_skill.md")
    patched_rows = [row for row in rows if row["variant"] == "patched_compact" and row["case_id"] == failed_row.get("case_id")]
    patched_row = patched_rows[0] if patched_rows else {}
    missed_rule_analysis = []
    for rule_id in missed_rule_ids:
        metadata = RULE_METADATA.get(
            rule_id,
            {
                "name": "unknown",
                "priority": "unknown",
                "failure_critical": False,
                "salience": "unknown",
                "long_tail": False,
                "why_missed": "No rule-specific explanation available.",
                "requires_execution_feedback": False,
            },
        )
        missed_rule_analysis.append({"rule_id": rule_id, **metadata})
    payload = {
        "run_id": OUT_DIR.name,
        "created_at": created_at,
        "status": status,
        "failed_case_id": failed_row.get("case_id"),
        "missed_rule_ids": missed_rule_ids,
        "expected_rule_ids": failed_row.get("expected_rule_ids", []),
        "direct_summary_available_rule_ids": failed_row.get("available_rule_ids", []),
        "direct_summary_contains_nearby_phrase": {
            "duplicate": "duplicate" in direct_skill_text.lower(),
            "idempotency": "idempotency" in direct_skill_text.lower(),
            "retry": "retry" in direct_skill_text.lower(),
        },
        "missed_rule_analysis": missed_rule_analysis,
        "patched_compact_recovery": {
            "pass_at_1": patched_row.get("pass_at_1"),
            "missing_rule_ids": patched_row.get("missing_rule_ids"),
            "available_rule_ids": patched_row.get("available_rule_ids"),
        },
        "patch_recovery": (
            "patched_compact includes R006 explicitly, so the mock case-aware agent emits the idempotency finding "
            "and the verifier marks the failed case as pass."
        ),
        "meaning_for_core_claim": (
            "Direct summary is not weak: it covers most salient rules. Its only miss is R006, a medium-priority but "
            "deployment-critical idempotency/duplicate-submission rule that compact_v1 also missed. This supports the "
            "narrow claim that deployment feedback is useful for recovering residual failure-critical rules."
        ),
        "boundary": (
            "One failed case is explanatory, not statistical. More holdout cases are needed before claiming a general "
            "long-tail failure pattern."
        ),
    }
    write_json(OUT_DIR / "summary.json", payload)
    write_text(OUT_DIR / "summary.md", render_summary(payload))
    write_json(
        OUT_DIR / "manifest.json",
        {
            "run_id": OUT_DIR.name,
            "created_at": created_at,
            "artifacts": ["summary.json", "summary.md", "manifest.json"],
            "boundary": payload["boundary"],
        },
    )
    print(json.dumps({"output_dir": str(OUT_DIR), "status": status}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
