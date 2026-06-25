from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def build_repo_run_report(*, task_results: list[dict[str, Any]], bundle_resolution: dict[str, Any], registry: dict[str, Any]) -> dict[str, Any]:
    fixture_distribution: dict[str, int] = {}
    for task in registry["tasks"]:
        fixture_distribution[task["fixture_type"]] = fixture_distribution.get(task["fixture_type"], 0) + 1
    pass_count = sum(bool(row.get("verifier_pass")) for row in task_results)
    failure_categories = [row.get("failure_category") for row in task_results if row.get("failure_category")]
    partial_bundle_count = 1 if bundle_resolution["bundle_attachment_mode"] == "partial_local_manifest_only" else 0
    real_bundle_count = 1 if bundle_resolution["bundle_attachment_mode"] == "real_release_bundle_pinned" else 0
    return {
        "schema_version": "repo_level_eval_aggregate_report.v1",
        "task_count": len(task_results),
        "pass_count": pass_count,
        "fail_count": len(task_results) - pass_count,
        "schema_fail_count": sum(1 for item in failure_categories if item == "schema_error"),
        "verifier_fail_count": sum(1 for row in task_results if row.get("verifier_pass") is False),
        "runtime_failure_count": sum(1 for row in task_results if row.get("runtime_status") == "runtime_failure"),
        "partial_bundle_count": partial_bundle_count,
        "real_bundle_count": real_bundle_count,
        "fixture_type_distribution": fixture_distribution,
        "evidence_resolution_failures": sum(1 for item in failure_categories if item == "evidence_error"),
        "hidden_gold_leakage_failures": sum(1 for item in failure_categories if item == "oracle_leakage"),
        "bundle_attachment_mode": bundle_resolution["bundle_attachment_mode"],
        "bundle_digest": bundle_resolution.get("bundle_digest"),
        "skill_digest": bundle_resolution.get("skill_digest"),
        "skill_artifact_digest": bundle_resolution.get("skill_artifact_digest"),
        "knowledge_projection_digest": bundle_resolution.get("knowledge_projection_digest"),
        "knowledge_access_binding_digest": bundle_resolution.get("knowledge_access_binding_digest"),
        "claim_boundary": {
            "system_harness_result": "implemented" if task_results else "failed",
            "task_verifier_result": "local deterministic verifier only",
            "bundle_attachment_status": bundle_resolution["bundle_attachment_mode"],
            "compiler_superiority": "not_evaluated",
            "vulnerability_discovery_claim": "not_claimed",
        },
        "task_results": task_results,
    }


def render_repo_run_report_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Repo-Level Evaluation Run Report",
        "",
        "## Summary",
        "",
        f"- task_count: `{report['task_count']}`",
        f"- pass_count: `{report['pass_count']}`",
        f"- fail_count: `{report['fail_count']}`",
        f"- bundle_attachment_mode: `{report['bundle_attachment_mode']}`",
        f"- bundle_digest: `{report['bundle_digest']}`",
        f"- skill_digest: `{report['skill_digest']}`",
        f"- skill_artifact_digest: `{report['skill_artifact_digest']}`",
        f"- knowledge_projection_digest: `{report['knowledge_projection_digest']}`",
        f"- knowledge_access_binding_digest: `{report['knowledge_access_binding_digest']}`",
        f"- fixture_type_distribution: `{json.dumps(report['fixture_type_distribution'], sort_keys=True)}`",
        "",
        "## Failure Counters",
        "",
        f"- schema_fail_count: `{report['schema_fail_count']}`",
        f"- verifier_fail_count: `{report['verifier_fail_count']}`",
        f"- runtime_failure_count: `{report['runtime_failure_count']}`",
        f"- evidence_resolution_failures: `{report['evidence_resolution_failures']}`",
        f"- hidden_gold_leakage_failures: `{report['hidden_gold_leakage_failures']}`",
        "",
        "## Claim Boundary",
        "",
        "- This is a reproducible local repo-level evaluation harness.",
        "- It does not prove compiler superiority.",
        "- It does not claim general vulnerability discovery.",
        "- It does not claim AgentHost, OpenHands, SWE-agent, Harbor, or production scanner effectiveness.",
        "",
        "## Tasks",
        "",
        "| task_id | verifier_pass | decision | failure_category | bundle_attachment_mode |",
        "|---|---:|---|---|---|",
    ]
    for row in report["task_results"]:
        lines.append(
            f"| `{row['task_id']}` | `{row['verifier_pass']}` | `{row.get('decision')}` | `{row.get('failure_category')}` | `{report['bundle_attachment_mode']}` |"
        )
    return "\n".join(lines).rstrip() + "\n"


def write_repo_run_report(output_dir: Path, report: dict[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "aggregate_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    (output_dir / "aggregate_report.md").write_text(render_repo_run_report_markdown(report), encoding="utf-8")
