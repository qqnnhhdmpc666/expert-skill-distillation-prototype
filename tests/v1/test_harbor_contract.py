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


def test_wsl_runtime_is_discovered_before_reporting_missing(monkeypatch) -> None:
    def fake_which(command: str) -> str | None:
        return "C:/Windows/System32/wsl.exe" if command == "wsl" else None

    monkeypatch.setattr("expert_skill_system.evaluation.harbor.shutil.which", fake_which)
    monkeypatch.setattr(
        "expert_skill_system.evaluation.harbor._wsl_distributions",
        lambda: ["Ubuntu-24.04-Codex"],
    )

    def fake_wsl_commands(distributions: list[str], command: str) -> list[str]:
        path = "/usr/bin/docker" if command == "docker" else "/opt/spark/harbor/.venv/bin/harbor"
        return [f"{distributions[0]}:{path}"]

    monkeypatch.setattr("expert_skill_system.evaluation.harbor._wsl_commands", fake_wsl_commands)
    result = qualify_harbor()
    assert result.status == "partial"
    assert result.wsl_harbor_commands
    assert result.wsl_docker_commands
    assert "HARBOR_COMMAND_MISSING" not in result.reason_codes
    assert "DOCKER_COMMAND_MISSING" not in result.reason_codes
