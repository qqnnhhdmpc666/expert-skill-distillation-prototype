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
    assert registry["task_count"] >= 4
    assert {task["task_id"] for task in tasks} >= {
        "dependency_use_triage_requests_demo",
        "dependency_use_triage_declared_not_used",
        "dependency_use_triage_version_not_affected",
        "dependency_use_triage_the_gan_zoo_public",
    }
    by_id = {task["task_id"]: task for task in tasks}
    public_task = by_id["dependency_use_triage_the_gan_zoo_public"]
    assert public_task["fixture_type"] == "public_repo_excerpt"
    assert public_task["source_url"] == "https://github.com/hindupuravinash/the-gan-zoo"
    assert public_task["commit_digest"] == "git-sha1:375f2be4a852ead8980c06b2a996893f0cb95713"


def test_repo_task_registry_summary_records_fixture_distribution() -> None:
    registry = load_repo_task_registry(REGISTRY)
    summary = registry_summary(registry)
    assert summary["fixture_type_distribution"]["local_public_like_demo"] >= 3
    assert summary["fixture_type_distribution"]["public_repo_excerpt"] == 1
    assert summary["registry_digest"].startswith("sha256:")
