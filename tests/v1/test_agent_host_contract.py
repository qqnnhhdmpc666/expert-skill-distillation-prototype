from __future__ import annotations

import subprocess
from pathlib import Path
from types import SimpleNamespace

from expert_skill_system.agent_host import AgentHostRequest, CodexAgentHost, OpenHandsHostAdapter


def _request() -> AgentHostRequest:
    return AgentHostRequest(bundle_digest="sha256:" + "a" * 64, task_id="qualification", task={"input": "bounded"})


def test_missing_codex_binary_is_a_hard_block_not_a_local_agent_pass(tmp_path: Path) -> None:
    workspace = SimpleNamespace(root=tmp_path)
    host = CodexAgentHost(workspace, executable=None)
    host.executable = None
    result = host.run(_request())
    assert result.status == "blocked"
    assert result.qualification_status == "hard_blocked"
    assert result.reason_codes == ("CODEX_BINARY_MISSING",)


def test_codex_timeout_is_recorded_as_failure(monkeypatch, tmp_path: Path) -> None:
    artifact_ref = {
        "schema_version": "artifact_ref.v1",
        "artifact_id": "agent",
        "digest": "sha256:" + "b" * 64,
        "media_type": "text/markdown",
        "artifact_schema_version": "agent_skill_artifact.v1",
        "size_bytes": 8,
    }
    workspace = SimpleNamespace(
        root=tmp_path,
        artifacts=SimpleNamespace(get_bytes=lambda ref: b"# Skill\n"),
    )
    monkeypatch.setattr(
        "expert_skill_system.agent_host.codex.BundleBuilder.load",
        lambda self, digest: SimpleNamespace(bundle_digest=digest, manifest={"agent_artifact_refs": [artifact_ref]}),
    )

    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=args[0], timeout=1, stderr="bounded timeout")

    monkeypatch.setattr("expert_skill_system.agent_host.codex._run_bounded", timeout)
    host = CodexAgentHost(workspace, executable="codex.cmd")
    result = host.run(_request())
    assert result.status == "timeout"
    assert result.qualification_status == "fail"
    assert "HOST_TIMEOUT" in result.reason_codes


def test_openhands_probe_does_not_count_missing_binary_as_qualification(monkeypatch) -> None:
    monkeypatch.setattr("expert_skill_system.agent_host.openhands.shutil.which", lambda command: None)
    result = OpenHandsHostAdapter.probe()
    assert result.status == "hard_blocked"
    assert result.reason == "OPENHANDS_BINARY_MISSING"
