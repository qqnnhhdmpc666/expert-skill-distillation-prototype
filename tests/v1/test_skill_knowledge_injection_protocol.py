from __future__ import annotations

from pathlib import Path

from expert_skill_system.runtime.skill_knowledge_injection import build_injection_manifests

TASK_DIR = Path("data/repo_security_tasks/dependency_use_triage_requests_demo")


def test_skill_knowledge_injection_keeps_runtime_and_hidden_paths_separate(tmp_path: Path) -> None:
    manifests = build_injection_manifests(task_dir=TASK_DIR, condition_id="C5_active_runtime", output_dir=tmp_path)
    condition = manifests["condition_manifest"]
    assert condition["skill_enabled"] is True
    assert condition["knowledge_enabled"] is True
    assert any("runtime_task_view.json" in path for path in condition["runtime_visible_paths"])
    assert any("allowed_knowledge.json" in path for path in condition["runtime_visible_paths"])
    assert all("task.json" not in path for path in condition["runtime_visible_paths"])
    assert all("hidden_gold" not in path for path in condition["runtime_visible_paths"])
    assert any("evaluator_only_gold" in path for path in condition["hidden_evaluator_paths"])
    assert (tmp_path / "runtime_task_view.json").exists()
    assert (tmp_path / "condition_manifest.json").exists()
    assert manifests["knowledge_manifest"]["knowledge_access_policy"] == "read_allowed_snapshot_only"


def test_skill_only_condition_disables_knowledge_access(tmp_path: Path) -> None:
    manifests = build_injection_manifests(task_dir=TASK_DIR, condition_id="C2_skill_only", output_dir=tmp_path)
    assert manifests["skill_manifest"]["skill_enabled"] is True
    assert manifests["knowledge_manifest"]["knowledge_enabled"] is False
