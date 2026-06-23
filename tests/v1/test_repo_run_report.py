from __future__ import annotations

import json
from pathlib import Path

from expert_skill_system.evaluation.repo_run_report import (
    build_repo_run_report,
    render_repo_run_report_markdown,
    write_repo_run_report,
)
from expert_skill_system.evaluation.repo_task_registry import load_repo_task_registry


def test_repo_run_report_separates_bundle_and_task_status(tmp_path: Path) -> None:
    registry = load_repo_task_registry(Path("data/repo_security_tasks/registry.json"))
    report = build_repo_run_report(
        task_results=[
            {
                "task_id": "dependency_use_triage_requests_demo",
                "verifier_pass": True,
                "failure_category": None,
                "decision": "dependency_used_and_affected",
            }
        ],
        bundle_resolution={"bundle_attachment_mode": "partial_local_manifest_only"},
        registry=registry,
    )
    assert report["pass_count"] == 1
    assert report["partial_bundle_count"] == 1
    assert report["claim_boundary"]["compiler_superiority"] == "not_evaluated"
    markdown = render_repo_run_report_markdown(report)
    assert "does not prove compiler superiority" in markdown
    write_repo_run_report(tmp_path, report)
    assert json.loads((tmp_path / "aggregate_report.json").read_text(encoding="utf-8"))["task_count"] == 1
    assert (tmp_path / "aggregate_report.md").exists()
