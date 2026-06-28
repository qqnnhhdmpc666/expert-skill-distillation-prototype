from __future__ import annotations

import subprocess
from pathlib import Path

from expert_skill_system.agent_backends import AgentBackendRequest, MiniSweAgentSmokeAdapter


def _request(tmp_path: Path, *, bundle: bool = False) -> AgentBackendRequest:
    return AgentBackendRequest(
        backend_id="real_agent",
        task_id="smoke",
        workspace_path=str(tmp_path / "workspace"),
        bundle_path=str(tmp_path / "bundle") if bundle else None,
        skill_artifact_path="skill" if bundle else None,
        knowledge_manifest_path="knowledge" if bundle else None,
        budget={"timeout_seconds": 5},
        output_dir=str(tmp_path / "out"),
        condition_id="C5_active_runtime" if bundle else "C0_no_skill",
        lane="repo_level_dependency_use",
        bundle_digest="sha256:" + "1" * 64 if bundle else None,
        skill_artifact_digest="sha256:" + "2" * 64 if bundle else None,
        knowledge_manifest_digest="sha256:" + "3" * 64 if bundle else None,
    )


def test_mini_swe_adapter_executes_with_injected_runner(tmp_path: Path) -> None:
    def runner(command: list[str], cwd: Path, timeout_seconds: int) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(command, 0, stdout="mini smoke ok", stderr="")

    adapter = MiniSweAgentSmokeAdapter(executable="mini", command_runner=runner)
    result = adapter.run(_request(tmp_path, bundle=True))
    assert result.execution_status == "executed"
    assert result.claim_counted is True
    out = Path(result.output_dir)
    assert (out / "agent_run_manifest.json").exists()
    assert (out / "agent_output.json").exists()
    assert (out / "normalized_trajectory.jsonl").exists()
    assert (out / "bundle_injection_trace.json").exists()
    assert (out / "verifier_result.json").exists()


def test_mini_swe_adapter_unavailable_is_not_execution(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("APPDATA", str(tmp_path / "empty_appdata"))
    monkeypatch.setattr("expert_skill_system.agent_backends.swe_agent_smoke.importlib.util.find_spec", lambda name: None)
    monkeypatch.setattr("expert_skill_system.agent_backends.swe_agent_smoke.shutil.which", lambda name: None)
    adapter = MiniSweAgentSmokeAdapter()
    result = adapter.run(_request(tmp_path))
    assert result.execution_status == "unavailable"
    assert result.claim_counted is False
    assert result.not_counted_count == 1
    assert (Path(result.output_dir) / "normalized_trajectory.jsonl").exists()
