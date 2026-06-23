from __future__ import annotations

from pathlib import Path

from expert_skill_system.evaluation.repo_security_task import load_task_package

TASK_DIR = Path("data/repo_security_tasks/dependency_use_triage_requests_demo")


def test_repo_security_task_separates_runtime_fields_from_gold() -> None:
    package = load_task_package(TASK_DIR)
    assert package["task"]["task_type"] == "dependency_use_triage"
    assert "hidden_gold" in package["task"]
    assert "hidden_gold" not in package["runtime_visible_task"]
    assert package["repo_snapshot_manifest"]["files"]
    assert package["allowed_knowledge"]["knowledge_sources"][0]["source_id"] == "PYSEC-2018-28"
