from __future__ import annotations

from pathlib import Path

from expert_skill_system.evaluation.harbor import qualify_harbor, write_harbor_task_contract


def test_harbor_contract_forbids_replay(tmp_path: Path) -> None:
    target = tmp_path / "task.yaml"
    write_harbor_task_contract(target)
    content = target.read_text(encoding="utf-8")
    assert "replay_allowed: false" in content
    assert "execution_envelope: required" in content


def test_missing_runtime_is_not_reported_as_harbor_pass(monkeypatch) -> None:
    monkeypatch.setattr("expert_skill_system.evaluation.harbor.shutil.which", lambda command: None)
    result = qualify_harbor()
    assert result.status == "hard_blocked_by_missing_runtime"
    assert result.replay_used is False
    assert "HARBOR_COMMAND_MISSING" in result.reason_codes
