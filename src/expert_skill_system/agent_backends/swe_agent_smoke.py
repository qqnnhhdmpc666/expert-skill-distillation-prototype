from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from ..core.canonical import sha256_bytes
from .base import (
    AgentBackendRequest,
    AgentBackendResult,
    NormalizedTrajectoryEvent,
    write_json,
    write_required_agent_artifacts,
)

CommandRunner = Callable[[list[str], Path, int], subprocess.CompletedProcess[str]]


class MiniSweAgentSmokeAdapter:
    backend_id = "mini_swe_agent"

    def __init__(self, *, executable: str | None = None, command_runner: CommandRunner | None = None) -> None:
        self.executable = executable
        self.command_runner = command_runner or _run_command

    def probe(self) -> dict[str, Any]:
        user_scripts = Path(os.environ.get("APPDATA", "")) / "Python" / f"Python{sys.version_info.major}{sys.version_info.minor}" / "Scripts"
        probe_commands = [["mini", "--help"], ["mini-swe-agent", "--help"]]
        probe_results = []
        executable = self.executable
        for command in probe_commands:
            found = shutil.which(command[0])
            if found is None:
                candidate = user_scripts / f"{command[0]}.exe"
                found = str(candidate) if candidate.exists() else None
            probe_results.append({"command": command, "found": found is not None, "path": found})
            if executable is None and found is not None:
                executable = found
        import_probe_result = {
            "minisweagent": importlib.util.find_spec("minisweagent") is not None,
            "mini_swe_agent": importlib.util.find_spec("mini_swe_agent") is not None,
        }
        import_available = any(import_probe_result.values())
        status = "available" if executable or import_available else "unavailable_environment"
        return {
            "schema_version": "mini_swe_agent_probe.v1",
            "backend_id": self.backend_id,
            "backend_status": status,
            "executable": executable,
            "execution_mode": "cli" if executable else ("python_api_subprocess" if import_available else "unavailable"),
            "probe_commands": probe_commands,
            "probe_results": probe_results,
            "import_probe_result": import_probe_result,
            "install_hint": "python -m pip install mini-swe-agent",
        }

    def run(self, request: AgentBackendRequest) -> AgentBackendResult:
        output_dir = Path(request.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        injection = self._bundle_injection_trace(request)
        probe = self.probe()
        write_json(output_dir / "backend_probe.json", probe)
        if probe["backend_status"] != "available":
            return self._unavailable(request, output_dir, injection, probe)
        workspace = output_dir / "workspace"
        workspace.mkdir(parents=True, exist_ok=True)
        prompt_path = workspace / "task.md"
        prompt_path.write_text(self._prompt(request), encoding="utf-8")
        if request.bundle_digest:
            bundle_ref = workspace / "bundle_ref.json"
            write_json(
                bundle_ref,
                {
                    "bundle_digest": request.bundle_digest,
                    "skill_artifact_digest": request.skill_artifact_digest,
                    "knowledge_manifest_digest": request.knowledge_manifest_digest,
                },
            )
        smoke_script = (workspace / "mini_swe_agent_smoke.py").resolve()
        trajectory_path = (workspace / "mini_swe_agent_trajectory.json").resolve()
        result_path = (workspace / "mini_swe_agent_result.json").resolve()
        prompt_path = prompt_path.resolve()
        smoke_script.write_text(_SMOKE_SCRIPT, encoding="utf-8")
        command = [sys.executable, str(smoke_script), str(trajectory_path), str(result_path), str(prompt_path)]
        started = time.perf_counter()
        try:
            completed = self.command_runner(command, workspace, int(request.budget.get("timeout_seconds", 30)))
        except (OSError, subprocess.TimeoutExpired) as exc:
            elapsed = round(time.perf_counter() - started, 3)
            return self._failed_after_launch(request, output_dir, injection, command, elapsed, exc)
        elapsed = round(time.perf_counter() - started, 3)
        stdout_path = output_dir / "stdout.txt"
        stderr_path = output_dir / "stderr.txt"
        stdout_text = _clean_captured_text(completed.stdout or "")
        stderr_text = _clean_captured_text(completed.stderr or "")
        stdout_path.write_text(stdout_text, encoding="utf-8")
        stderr_path.write_text(stderr_text, encoding="utf-8")
        status = "executed" if completed.returncode == 0 else "failed"
        verifier_status = "completed" if completed.returncode == 0 else "execution_failed"
        trajectory = [
            NormalizedTrajectoryEvent.make(
                step_index=0,
                actor="runtime",
                event_type="file_write",
                content_ref=str(prompt_path),
                bundle_related=bool(request.bundle_digest),
            ),
            NormalizedTrajectoryEvent.make(
                step_index=1,
                actor="agent",
                event_type="command",
                content_ref=" ".join(command),
                bundle_related=bool(request.bundle_digest),
            ),
            NormalizedTrajectoryEvent.make(
                step_index=2,
                actor="verifier",
                event_type="verifier_result" if completed.returncode == 0 else "error",
                content_ref=str(stdout_path if completed.returncode == 0 else stderr_path),
                bundle_related=bool(request.bundle_digest),
            ),
        ]
        artifacts = write_required_agent_artifacts(
            output_dir=output_dir,
            request=request,
            run_manifest={
                "schema_version": "agent_run_manifest.v1",
                "backend_id": self.backend_id,
                "task_id": request.task_id,
                "condition_id": request.condition_id,
                "execution_status": status,
                "command": command,
                "exit_code": completed.returncode,
                "runtime_seconds": elapsed,
                "real_agent_smoke": True,
            },
            agent_output={
                "schema_version": "agent_output.v1",
                "backend_id": self.backend_id,
                "status": status,
                "stdout_ref": str(stdout_path),
                "stderr_ref": str(stderr_path),
                "mini_swe_agent_trajectory_ref": str(trajectory_path),
                "mini_swe_agent_result_ref": str(result_path),
                "stdout_digest": sha256_bytes(stdout_text.encode("utf-8")),
            },
            verifier_result={
                "schema_version": "open_world_verifier_result.v1",
                "status": verifier_status,
                "verifier_pass": completed.returncode == 0,
                "exit_code": completed.returncode,
            },
            trajectory=trajectory,
            bundle_injection_trace=injection,
        )
        return AgentBackendResult(
            backend_id=self.backend_id,
            task_id=request.task_id,
            lane=request.lane,
            condition_id=request.condition_id,
            execution_status="executed" if completed.returncode == 0 else "failed",
            output_dir=str(output_dir),
            pass_count=1 if completed.returncode == 0 else 0,
            fail_count=0 if completed.returncode == 0 else 1,
            exit_code=completed.returncode,
            runtime_seconds=elapsed,
            backend_status="executed" if completed.returncode == 0 else "execution_failed",
            command=command,
            artifact_paths=artifacts,
            bundle_injected=bool(request.bundle_digest),
            trajectory_available=True,
            verifier_available=True,
            claim_counted=completed.returncode == 0,
        )

    def _prompt(self, request: AgentBackendRequest) -> str:
        lines = [
            "# Open-World Integration v0 Smoke Task",
            "",
            f"- task_id: {request.task_id}",
            f"- condition_id: {request.condition_id}",
            "- This is a backend execution smoke, not an effectiveness benchmark.",
        ]
        if request.bundle_digest:
            lines.extend(
                [
                    "- Bundle artifacts are exposed through workspace bundle_ref.json.",
                    f"- bundle_digest: {request.bundle_digest}",
                ]
            )
        else:
            lines.append("- No Bundle, Skill artifact, or Knowledge manifest is visible for this condition.")
        return "\n".join(lines) + "\n"

    def _bundle_injection_trace(self, request: AgentBackendRequest) -> dict[str, Any]:
        bundle_visible = bool(request.bundle_digest)
        return {
            "schema_version": "bundle_injection_trace.v1",
            "bundle_digest": request.bundle_digest,
            "skill_artifact_digest": request.skill_artifact_digest,
            "knowledge_manifest_digest": request.knowledge_manifest_digest,
            "injection_mode": "workspace_file" if bundle_visible else "none",
            "agent_backend": self.backend_id,
            "forbidden_sources_excluded": True,
            "bundle_visible_to_agent": bundle_visible,
            "skill_artifact_visible_to_agent": bundle_visible,
            "knowledge_manifest_visible_to_agent": bundle_visible,
            "agent_prompt_or_workspace_contains_bundle_ref": bundle_visible,
        }

    def _unavailable(
        self, request: AgentBackendRequest, output_dir: Path, injection: dict[str, Any], probe: dict[str, Any]
    ) -> AgentBackendResult:
        trajectory = [
            NormalizedTrajectoryEvent.make(
                step_index=0,
                actor="runtime",
                event_type="error",
                content_ref="mini_swe_agent_unavailable_environment",
                bundle_related=bool(request.bundle_digest),
            )
        ]
        artifacts = write_required_agent_artifacts(
            output_dir=output_dir,
            request=request,
            run_manifest={
                "schema_version": "agent_run_manifest.v1",
                "backend_id": self.backend_id,
                "task_id": request.task_id,
                "condition_id": request.condition_id,
                "execution_status": "unavailable",
                "backend_status": "unavailable_environment",
                **probe,
            },
            agent_output={"schema_version": "agent_output.v1", "status": "unavailable_environment", **probe},
            verifier_result={
                "schema_version": "open_world_verifier_result.v1",
                "status": "unavailable_environment",
                "verifier_pass": False,
            },
            trajectory=trajectory,
            bundle_injection_trace=injection,
        )
        return AgentBackendResult(
            backend_id=self.backend_id,
            task_id=request.task_id,
            lane=request.lane,
            condition_id=request.condition_id,
            execution_status="unavailable",
            output_dir=str(output_dir),
            not_counted_count=1,
            backend_status="unavailable_environment",
            reason="mini_swe_agent_not_installed_or_not_on_path",
            artifact_paths=artifacts,
            bundle_injected=bool(request.bundle_digest),
            trajectory_available=True,
            verifier_available=True,
            claim_counted=False,
        )

    def _failed_after_launch(
        self,
        request: AgentBackendRequest,
        output_dir: Path,
        injection: dict[str, Any],
        command: list[str],
        elapsed: float,
        exc: OSError | subprocess.TimeoutExpired,
    ) -> AgentBackendResult:
        stderr_summary = str(exc)[-2000:]
        trajectory = [
            NormalizedTrajectoryEvent.make(
                step_index=0,
                actor="agent",
                event_type="command",
                content_ref=" ".join(command),
                bundle_related=bool(request.bundle_digest),
            ),
            NormalizedTrajectoryEvent.make(
                step_index=1,
                actor="agent",
                event_type="error",
                content_ref=stderr_summary,
                bundle_related=bool(request.bundle_digest),
            ),
        ]
        artifacts = write_required_agent_artifacts(
            output_dir=output_dir,
            request=request,
            run_manifest={
                "schema_version": "agent_run_manifest.v1",
                "backend_id": self.backend_id,
                "task_id": request.task_id,
                "condition_id": request.condition_id,
                "execution_status": "failed",
                "command": command,
                "runtime_seconds": elapsed,
                "stderr_summary": stderr_summary,
            },
            agent_output={"schema_version": "agent_output.v1", "status": "failed", "stderr_summary": stderr_summary},
            verifier_result={
                "schema_version": "open_world_verifier_result.v1",
                "status": "execution_failed",
                "verifier_pass": False,
            },
            trajectory=trajectory,
            bundle_injection_trace=injection,
        )
        return AgentBackendResult(
            backend_id=self.backend_id,
            task_id=request.task_id,
            lane=request.lane,
            condition_id=request.condition_id,
            execution_status="failed",
            output_dir=str(output_dir),
            fail_count=1,
            runtime_seconds=elapsed,
            backend_status="execution_failed",
            reason=stderr_summary,
            command=command,
            artifact_paths=artifacts,
            bundle_injected=bool(request.bundle_digest),
            trajectory_available=True,
            verifier_available=True,
            claim_counted=False,
        )


def _run_command(command: list[str], cwd: Path, timeout_seconds: int) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    env["MSWEA_CONFIGURED"] = "true"
    return subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout_seconds,
        check=False,
        env=env,
    )


def _clean_captured_text(text: str) -> str:
    if not text:
        return ""
    lines = [line.rstrip() for line in text.splitlines()]
    return "\n".join(lines) + ("\n" if text.endswith(("\n", "\r")) else "")


_SMOKE_SCRIPT = r'''
from __future__ import annotations

import json
import sys
from pathlib import Path

from minisweagent.agents.default import DefaultAgent
from minisweagent.environments.local import LocalEnvironment
from minisweagent.models.test_models import DeterministicModel, make_output


trajectory_path = Path(sys.argv[1])
result_path = Path(sys.argv[2])
prompt_path = Path(sys.argv[3])
workspace = trajectory_path.parent
task_text = prompt_path.read_text(encoding="utf-8")

model = DeterministicModel(
    outputs=[
        make_output(
            "I will complete the open-world integration smoke task.",
            [{"command": "echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT"}],
            cost=0.0,
        )
    ]
)
env = LocalEnvironment(cwd=str(workspace), timeout=10)
agent = DefaultAgent(
    model,
    env,
    system_template="You are a mini-SWE-agent smoke-test agent.",
    instance_template="Task: {{task}}",
    step_limit=2,
    cost_limit=1,
    output_path=trajectory_path,
)
result = agent.run(task_text)
result_path.write_text(json.dumps({"status": "completed", "result": result}, indent=2), encoding="utf-8")
print(json.dumps({"mini_swe_agent_smoke": "executed", "result": result}, sort_keys=True))
'''
