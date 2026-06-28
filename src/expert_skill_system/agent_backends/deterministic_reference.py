from __future__ import annotations

import json
from pathlib import Path

from ..evaluation.repo_security_task import run_dependency_use_triage
from .base import AgentBackendRequest, AgentBackendResult, NormalizedTrajectoryEvent, write_required_agent_artifacts


class DeterministicReferenceAdapter:
    backend_id = "deterministic_reference"

    def run(self, request: AgentBackendRequest) -> AgentBackendResult:
        output_dir = Path(request.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        task_dir_text = request.task_payload.get("task_dir")
        if not task_dir_text:
            return self._dry_run(request, "no_repo_task_dir_for_lane")
        result = run_dependency_use_triage(
            Path(task_dir_text),
            output_dir / "repo_task_run",
            condition_id=request.condition_id,
            bundle_resolution=request.task_payload.get("bundle_resolution"),
        )
        verifier = json.loads(Path(result["verifier_result_path"]).read_text(encoding="utf-8"))
        trajectory = [
            NormalizedTrajectoryEvent.make(
                step_index=0,
                actor="runtime",
                event_type="tool_call",
                content_ref="repo_security_task.run_dependency_use_triage",
                bundle_related=bool(request.bundle_digest),
            ),
            NormalizedTrajectoryEvent.make(
                step_index=1,
                actor="verifier",
                event_type="verifier_result",
                content_ref=str(result["verifier_result_path"]),
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
                "execution_status": "executed",
                "bundle_digest": request.bundle_digest,
            },
            agent_output={
                "schema_version": "agent_output.v1",
                "backend_id": self.backend_id,
                "status": "completed",
                "repo_task_result": result,
            },
            verifier_result={
                "schema_version": "open_world_verifier_result.v1",
                "status": "completed",
                "verifier_pass": bool(result["verifier_pass"]),
                "source_verifier": verifier,
            },
            trajectory=trajectory,
        )
        return AgentBackendResult(
            backend_id=self.backend_id,
            task_id=request.task_id,
            lane=request.lane,
            condition_id=request.condition_id,
            execution_status="executed",
            output_dir=str(output_dir),
            pass_count=1 if result["verifier_pass"] else 0,
            fail_count=0 if result["verifier_pass"] else 1,
            artifact_paths=artifacts,
            bundle_injected=bool(request.bundle_digest),
            trajectory_available=True,
            verifier_available=True,
            claim_counted=True,
        )

    def _dry_run(self, request: AgentBackendRequest, reason: str) -> AgentBackendResult:
        output_dir = Path(request.output_dir)
        trajectory = [
            NormalizedTrajectoryEvent.make(
                step_index=0,
                actor="runtime",
                event_type="error",
                content_ref=reason,
                allowed_by_policy=True,
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
                "execution_status": "dry_run",
                "reason": reason,
            },
            agent_output={"schema_version": "agent_output.v1", "status": "dry_run", "reason": reason},
            verifier_result={
                "schema_version": "open_world_verifier_result.v1",
                "status": "dry_run_contract_only",
                "verifier_pass": False,
            },
            trajectory=trajectory,
        )
        return AgentBackendResult(
            backend_id=self.backend_id,
            task_id=request.task_id,
            lane=request.lane,
            condition_id=request.condition_id,
            execution_status="dry_run",
            output_dir=str(output_dir),
            not_counted_count=1,
            reason=reason,
            artifact_paths=artifacts,
            trajectory_available=True,
            verifier_available=True,
            claim_counted=False,
        )
