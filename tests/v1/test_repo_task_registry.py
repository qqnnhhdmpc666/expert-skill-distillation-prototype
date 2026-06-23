from __future__ import annotations

from pathlib import Path

from expert_skill_system.evaluation.repo_task_registry import (
    load_repo_task_registry,
    registry_summary,
    select_registry_tasks,
)

REGISTRY = Path("data/repo_security_tasks/registry.json")


def test_repo_task_registry_lists_runnable_tasks() -> None:
    registry = load_repo_task_registry(REGISTRY)
    tasks = select_registry_tasks(registry)
    assert registry["task_count"] >= 3
    assert {task["task_id"] for task in tasks} >= {
        "dependency_use_triage_requests_demo",
        "dependency_use_triage_declared_not_used",
        "dependency_use_triage_version_not_affected",
    }
    assert all(task["fixture_type"] == "local_public_like_demo" for task in tasks)


def test_repo_task_registry_summary_records_fixture_distribution() -> None:
    registry = load_repo_task_registry(REGISTRY)
    summary = registry_summary(registry)
    assert summary["fixture_type_distribution"]["local_public_like_demo"] >= 3
    assert summary["registry_digest"].startswith("sha256:")
