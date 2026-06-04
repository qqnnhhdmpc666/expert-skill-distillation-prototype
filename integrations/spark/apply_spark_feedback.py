from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


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


def estimate_tokens(text: str) -> int:
    return max(1, round(len(text) / 4)) if text else 0


def compact_check_for(row: dict[str, Any]) -> str:
    checks = {
        "R001": "Check whether authentication method, roles/scopes, and auth failure behavior are explicit.",
        "R002": "Check required fields, optional defaults, type, range, length, and enum constraints.",
        "R003": "Check error codes for validation, auth, permission, not found, duplicate, and server errors.",
        "R004": "Check for token, secret, stack trace, full phone or identity exposure in responses.",
        "R005": "Check consistent envelope fields: code, message, request_id, and data.",
        "R006": "Check whether mutation endpoints document idempotency or duplicate submission handling.",
        "R007": "Check request_id, trace metadata, and audit logging expectations.",
    }
    return checks.get(str(row["rule_id"]), str(row["rule_text"]))


def apply_spark_feedback(ledger: list[dict[str, Any]], spark_report: dict[str, Any]) -> list[dict[str, Any]]:
    diagnosis = spark_report.get("diagnosis") or {}
    affected_rule_ids = set(diagnosis.get("affected_rule_ids") or [])
    patch_ready = bool(diagnosis.get("patch_ready"))
    failure_type = str(spark_report.get("failure_type") or "unknown_failure")
    updated: list[dict[str, Any]] = []
    for row in ledger:
        next_row = dict(row)
        patches = list(row.get("patches") or [])
        rule_id = str(row["rule_id"])
        if patch_ready and rule_id in affected_rule_ids:
            next_row["execution_status"] = "failure_critical"
            next_row["cost_status"] = "compact_patch"
            next_row["decision_v2"] = "patch"
            next_row["decision_reason_v2"] = (
                f"SPARK execution feedback marked {rule_id} as affected by {failure_type}; "
                "patch it into compact skill v2."
            )
            patches.append(
                {
                    "patch_id": f"SPARK-{rule_id}-v2",
                    "source": "execution_report_spark.json",
                    "failure_type": failure_type,
                    "action": "patch_into_compact_v2",
                    "reason": f"SPARK diagnosis listed {rule_id} as an affected rule.",
                }
            )
        next_row["patches"] = patches
        updated.append(next_row)
    return updated


def reset_ledger_to_v1(ledger: list[dict[str, Any]]) -> list[dict[str, Any]]:
    reset: list[dict[str, Any]] = []
    for row in ledger:
        next_row = dict(row)
        next_row["execution_status"] = "not_observed"
        next_row["cost_status"] = "compact_keep" if row.get("decision_v1") in {"keep", "compress"} else "compact_drop"
        next_row["decision_v2"] = row.get("decision_v1", "drop")
        next_row["decision_reason_v2"] = "Reset to v1 decision before applying SPARK-compatible feedback."
        next_row["patches"] = []
        reset.append(next_row)
    return reset


def render_compact_skill(evidence_map: list[dict[str, Any]], ledger: list[dict[str, Any]]) -> str:
    evidence_by_rule = {str(row["rule_id"]): row for row in evidence_map}
    lines = [
        "# API Review Compact Skill v2 from SPARK Feedback",
        "",
        "Use this skill to review an API specification. This version is generated from rule_ledger decisions after SPARK-compatible execution feedback.",
        "",
        "## Checklist",
        "",
    ]
    for entry in ledger:
        decision = str(entry.get("decision_v2"))
        if decision not in {"keep", "compress", "patch"}:
            continue
        rule_id = str(entry["rule_id"])
        material_status = evidence_by_rule.get(rule_id, {}).get("status", entry.get("material_status"))
        lines.append(
            f"- [{rule_id}] {compact_check_for(entry)} "
            f"Decision: {decision}; material: {material_status}; execution: {entry.get('execution_status')}."
        )
    lines.extend(
        [
            "",
            "## Output Format",
            "",
            "Return JSON only with `passed`, `failed_rules`, `findings`, and `suggested_patch`.",
            "",
        ]
    )
    return "\n".join(lines)


def render_repair_log(spark_report: dict[str, Any], patched_ledger: list[dict[str, Any]]) -> str:
    diagnosis = spark_report.get("diagnosis") or {}
    affected_rule_ids = set(diagnosis.get("affected_rule_ids") or [])
    ledger_by_id = {str(row["rule_id"]): row for row in patched_ledger}
    lines = [
        "# SPARK Feedback Repair Log",
        "",
        "## Source Execution Report",
        "",
        f"- Task: {spark_report.get('task_name')}",
        f"- Passed: {spark_report.get('passed')}",
        f"- Failure type: {spark_report.get('failure_type')}",
        f"- Patch ready: {diagnosis.get('patch_ready')}",
        f"- Affected rules: {', '.join(sorted(affected_rule_ids)) if affected_rule_ids else 'none'}",
        "",
        "## Rule-level Patches",
        "",
    ]
    if not affected_rule_ids:
        lines.append("- No affected rules were reported; no rule patch was applied.")
    for rule_id in sorted(affected_rule_ids):
        row = ledger_by_id.get(rule_id)
        if not row:
            lines.append(f"- {rule_id}: reported by SPARK but not found in rule ledger.")
            continue
        lines.extend(
            [
                f"### {rule_id}",
                "",
                f"- Decision: {row.get('decision_v2')}",
                f"- Execution status: {row.get('execution_status')}",
                f"- Cost status: {row.get('cost_status')}",
                f"- Reason: {row.get('decision_reason_v2')}",
                "",
            ]
        )
    lines.append("")
    return "\n".join(lines)


def build_cost_summary(full_skill: str, compact_v1: str, compact_v2: str, spark_report: dict[str, Any]) -> dict[str, Any]:
    full_tokens = estimate_tokens(full_skill)
    compact_v1_tokens = estimate_tokens(compact_v1)
    compact_v2_tokens = estimate_tokens(compact_v2)
    return {
        "token_estimator": "round(characters / 4)",
        "full_skill_tokens": full_tokens,
        "compact_skill_v1_tokens": compact_v1_tokens,
        "compact_skill_v2_from_spark_tokens": compact_v2_tokens,
        "compression_ratio_v1": round(compact_v1_tokens / full_tokens, 3) if full_tokens else None,
        "compression_ratio_v2_from_spark": round(compact_v2_tokens / full_tokens, 3) if full_tokens else None,
        "spark_execution": {
            "passed": spark_report.get("passed"),
            "failure_type": spark_report.get("failure_type"),
            "affected_rule_ids": (spark_report.get("diagnosis") or {}).get("affected_rule_ids", []),
            "patch_ready": (spark_report.get("diagnosis") or {}).get("patch_ready", False),
            "input_tokens": (spark_report.get("cost") or {}).get("input_tokens"),
            "output_tokens": (spark_report.get("cost") or {}).get("output_tokens"),
            "total_time_s": (spark_report.get("cost") or {}).get("total_time_s"),
        },
    }


def render_spark_feedback_report(cost_summary: dict[str, Any], spark_report: dict[str, Any]) -> str:
    spark_execution = cost_summary["spark_execution"]
    affected = spark_execution.get("affected_rule_ids") or []
    lines = [
        "# SPARK Feedback Closed-loop Report",
        "",
        "## Positioning",
        "",
        "This run demonstrates the structural bridge from SPARK-compatible execution feedback to rule-level compact skill repair. The failure input is currently a fixture, so this proves interface behavior rather than real-task effectiveness.",
        "",
        "## Feedback Signal",
        "",
        f"- Task: {spark_report.get('task_name')}",
        f"- Passed: {spark_execution.get('passed')}",
        f"- Failure type: {spark_execution.get('failure_type')}",
        f"- Patch ready: {spark_execution.get('patch_ready')}",
        f"- Affected rules: {', '.join(affected) if affected else 'none'}",
        "",
        "## Cost Summary",
        "",
        f"- Full skill tokens: {cost_summary['full_skill_tokens']}",
        f"- Compact v1 tokens: {cost_summary['compact_skill_v1_tokens']}",
        f"- Compact v2 from SPARK tokens: {cost_summary['compact_skill_v2_from_spark_tokens']}",
        f"- Compact v1 ratio: {cost_summary['compression_ratio_v1']}",
        f"- Compact v2 from SPARK ratio: {cost_summary['compression_ratio_v2_from_spark']}",
        "",
        "## Interpretation",
        "",
        "SPARK-compatible feedback now changes the rule ledger and therefore changes the generated compact skill. The next step is replacing the fixture with a real Harbor API-review task.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply SPARK-compatible execution feedback to the MVP rule ledger.")
    parser.add_argument("--source-run-dir", type=Path, required=True, help="MVP run dir containing full_skill, compact v1, evidence_map, and rule_ledger.")
    parser.add_argument("--spark-report", type=Path, required=True, help="execution_report_spark.json from convert_spark_artifacts.py.")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--created-at", default=None)
    args = parser.parse_args()

    source_run_dir = args.source_run_dir
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    full_skill = read_text(source_run_dir / "full_skill.md")
    compact_v1 = read_text(source_run_dir / "compact_skill_v1.md")
    evidence_map = read_json(source_run_dir / "evidence_map.json")
    rule_ledger = reset_ledger_to_v1(read_json(source_run_dir / "rule_ledger.json"))
    spark_report = read_json(args.spark_report)
    patched_ledger = apply_spark_feedback(rule_ledger, spark_report)
    compact_v2 = render_compact_skill(evidence_map, patched_ledger)
    repair_log = render_repair_log(spark_report, patched_ledger)
    cost_summary = build_cost_summary(full_skill, compact_v1, compact_v2, spark_report)
    spark_feedback_report = render_spark_feedback_report(cost_summary, spark_report)

    shutil.copy2(source_run_dir / "full_skill.md", output_dir / "full_skill.md")
    shutil.copy2(source_run_dir / "compact_skill_v1.md", output_dir / "compact_skill_v1.md")
    shutil.copy2(source_run_dir / "evidence_map.json", output_dir / "evidence_map.json")
    write_json(output_dir / "rule_ledger.json", rule_ledger)
    write_json(output_dir / "execution_report_spark.json", spark_report)
    write_json(output_dir / "rule_ledger_patched.json", patched_ledger)
    write_text(output_dir / "repair_log_spark.md", repair_log)
    write_text(output_dir / "compact_skill_v2.md", compact_v2)
    write_json(output_dir / "cost_summary.json", cost_summary)
    write_text(output_dir / "spark_feedback_report.md", spark_feedback_report)
    artifacts = [
        "full_skill.md",
        "compact_skill_v1.md",
        "evidence_map.json",
        "rule_ledger.json",
        "execution_report_spark.json",
        "rule_ledger_patched.json",
        "repair_log_spark.md",
        "compact_skill_v2.md",
        "cost_summary.json",
        "spark_feedback_report.md",
    ]
    write_json(
        output_dir / "manifest.json",
        {
            "run_id": output_dir.name,
            "created_at": args.created_at or datetime.now(timezone.utc).isoformat(),
            "source_run_dir": str(source_run_dir),
            "spark_report": str(args.spark_report),
            "artifacts": artifacts,
            "note": "SPARK-compatible feedback applied to rule_ledger; fixture-backed unless spark_report comes from a real Harbor task.",
        },
    )
    print(json.dumps({"output_dir": str(output_dir), "artifacts": artifacts}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
