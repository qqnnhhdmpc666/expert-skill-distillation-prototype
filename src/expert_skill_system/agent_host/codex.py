from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from pathlib import Path

from ..core.canonical import sha256_json
from ..core.models import ArtifactRef
from ..registry.workspace import Workspace
from ..runtime import BundleBuilder
from .models import AgentHostRequest, AgentHostResult


class CodexAgentHost:
    """Bounded Codex CLI adapter over one immutable ReleaseBundle task package."""

    def __init__(self, workspace: Workspace, *, executable: str | None = None) -> None:
        self.workspace = workspace
        self.executable = executable or shutil.which("codex.cmd") or shutil.which("codex")

    def run(self, request: AgentHostRequest) -> AgentHostResult:
        if not self.executable:
            return self._blocked(request, "CODEX_BINARY_MISSING")
        bundle = BundleBuilder(self.workspace).load(request.bundle_digest)
        run_dir = self.workspace.root / "agent_host_runs" / request.task_id
        run_dir.mkdir(parents=True, exist_ok=True)
        artifact_ref = ArtifactRef.from_dict(bundle.manifest["agent_artifact_refs"][0])
        skill_bytes = self.workspace.artifacts.get_bytes(artifact_ref)
        (run_dir / "SKILL.md").write_bytes(skill_bytes)
        task_payload = {
            "schema_version": "agent_host_task.v1",
            "bundle_digest": request.bundle_digest,
            "task_id": request.task_id,
            "task": request.task,
            "knowledge_policy": "only supplied task evidence; no live retrieval",
        }
        (run_dir / "task.json").write_text(json.dumps(task_payload, ensure_ascii=False, indent=2), encoding="utf-8")
        schema = {
            "type": "object",
            "additionalProperties": False,
            "required": ["status", "decision", "evidence_used"],
            "properties": {
                "status": {"enum": ["completed", "unresolved"]},
                "decision": {"type": "string"},
                "evidence_used": {"type": "array", "items": {"type": "string"}},
            },
        }
        (run_dir / "output_schema.json").write_text(json.dumps(schema, indent=2), encoding="utf-8")
        output_path = run_dir / "agent_result.json"
        command = [
            self.executable,
            "--ask-for-approval",
            "never",
            "exec",
            "--ephemeral",
            "--skip-git-repo-check",
            "--sandbox",
            "read-only",
            "--output-schema",
            str(run_dir / "output_schema.json"),
            "--output-last-message",
            str(output_path),
            "-C",
            str(run_dir),
            "Read SKILL.md and task.json. Use only supplied evidence. Return the required JSON object.",
        ]
        started = time.perf_counter()
        try:
            completed = _run_bounded(command, timeout=request.timeout_seconds)
        except subprocess.TimeoutExpired as exc:
            return AgentHostResult(
                host="codex_cli",
                status="timeout",
                qualification_status="fail",
                bundle_digest=request.bundle_digest,
                task_id=request.task_id,
                reason_codes=("HOST_TIMEOUT",),
                evidence={"elapsed_ms": round((time.perf_counter() - started) * 1000, 3), "stderr": (exc.stderr or "")[-2000:]},
            )
        version = self._version()
        stderr_tail = completed.stderr[-4000:]
        evidence = {
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 3),
            "command_shape": [Path(command[0]).name, *command[1:10], "<paths-and-prompt-redacted>"],
            "task_digest": sha256_json(task_payload),
            "agent_artifact_digest": artifact_ref.digest,
            "stderr_tail": stderr_tail,
        }
        if completed.returncode != 0:
            reason = "CODEX_AUTH_OR_NETWORK_BLOCKED" if any(
                marker in stderr_tail.casefold()
                for marker in (
                    "not logged in",
                    "401",
                    "authentication",
                    "network",
                    "failed to connect",
                    "could not connect",
                    "stream disconnected",
                    "socket",
                    "访问套接字",
                )
            ) else "CODEX_EXEC_FAILED"
            return AgentHostResult(
                host="codex_cli", host_version=version, status="blocked" if reason.endswith("BLOCKED") else "failed",
                qualification_status="hard_blocked" if reason.endswith("BLOCKED") else "fail",
                bundle_digest=request.bundle_digest, task_id=request.task_id, exit_code=completed.returncode,
                reason_codes=(reason,), evidence=evidence,
            )
        try:
            output = json.loads(output_path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError) as exc:
            return AgentHostResult(
                host="codex_cli", host_version=version, status="failed", qualification_status="fail",
                bundle_digest=request.bundle_digest, task_id=request.task_id, exit_code=completed.returncode,
                reason_codes=("INVALID_HOST_OUTPUT", type(exc).__name__), evidence=evidence,
            )
        return AgentHostResult(
            host="codex_cli", host_version=version, status="completed", qualification_status="partial",
            bundle_digest=request.bundle_digest, task_id=request.task_id, exit_code=completed.returncode,
            output=output, reason_codes=("REAL_AGENT_EXECUTED_CONTRACT_NOT_EFFECTIVENESS",), evidence=evidence,
        )

    def _version(self) -> str | None:
        try:
            return subprocess.run([self.executable, "--version"], capture_output=True, text=True, timeout=10, check=False).stdout.strip()
        except (OSError, subprocess.TimeoutExpired):
            return None

    def _blocked(self, request: AgentHostRequest, reason: str) -> AgentHostResult:
        return AgentHostResult(
            host="codex_cli", status="blocked", qualification_status="hard_blocked",
            bundle_digest=request.bundle_digest, task_id=request.task_id, reason_codes=(reason,),
        )


def _run_bounded(command: list[str], *, timeout: float) -> subprocess.CompletedProcess[str]:
    flags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=os.environ.copy(),
        creationflags=flags,
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                capture_output=True,
                timeout=15,
                check=False,
            )
        else:
            process.kill()
        process.communicate(timeout=15)
        raise
    return subprocess.CompletedProcess(command, process.returncode, stdout, stderr)
