from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

ExecutionStatus = Literal["executed", "dry_run", "unavailable", "blocked", "failed"]
Actor = Literal["agent", "runtime", "tool", "verifier"]
EventType = Literal["message", "command", "file_read", "file_write", "tool_call", "verifier_result", "error"]


@dataclass(frozen=True)
class AgentBackendRequest:
    backend_id: str
    task_id: str
    workspace_path: str
    bundle_path: str | None
    skill_artifact_path: str | None
    knowledge_manifest_path: str | None
    budget: dict[str, Any]
    output_dir: str
    condition_id: str
    lane: str
    task_payload: dict[str, Any] = field(default_factory=dict)
    bundle_digest: str | None = None
    skill_artifact_digest: str | None = None
    knowledge_manifest_digest: str | None = None


@dataclass(frozen=True)
class NormalizedTrajectoryEvent:
    step_index: int
    actor: Actor
    event_type: EventType
    content_ref: str
    timestamp: str
    allowed_by_policy: bool
    bundle_related: bool
    knowledge_source_ref: str | None = None

    @staticmethod
    def make(
        *,
        step_index: int,
        actor: Actor,
        event_type: EventType,
        content_ref: str,
        allowed_by_policy: bool = True,
        bundle_related: bool = False,
        knowledge_source_ref: str | None = None,
    ) -> NormalizedTrajectoryEvent:
        return NormalizedTrajectoryEvent(
            step_index=step_index,
            actor=actor,
            event_type=event_type,
            content_ref=content_ref,
            timestamp=datetime.now(UTC).isoformat(),
            allowed_by_policy=allowed_by_policy,
            bundle_related=bundle_related,
            knowledge_source_ref=knowledge_source_ref,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AgentBackendResult:
    backend_id: str
    task_id: str
    lane: str
    condition_id: str
    execution_status: ExecutionStatus
    output_dir: str
    pass_count: int = 0
    fail_count: int = 0
    not_counted_count: int = 0
    exit_code: int | None = None
    runtime_seconds: float | None = None
    backend_status: str | None = None
    reason: str | None = None
    command: list[str] = field(default_factory=list)
    artifact_paths: dict[str, str] = field(default_factory=dict)
    bundle_injected: bool = False
    forbidden_access_pass: bool = True
    trajectory_available: bool = False
    verifier_available: bool = False
    claim_counted: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows) + "\n", encoding="utf-8")


def write_required_agent_artifacts(
    *,
    output_dir: Path,
    request: AgentBackendRequest,
    run_manifest: dict[str, Any],
    agent_output: dict[str, Any],
    verifier_result: dict[str, Any],
    trajectory: list[NormalizedTrajectoryEvent],
    bundle_injection_trace: dict[str, Any] | None = None,
) -> dict[str, str]:
    write_json(output_dir / "agent_run_manifest.json", run_manifest)
    write_json(output_dir / "agent_output.json", agent_output)
    write_json(output_dir / "verifier_result.json", verifier_result)
    write_jsonl(output_dir / "normalized_trajectory.jsonl", [event.to_dict() for event in trajectory])
    paths = {
        "agent_run_manifest": str(output_dir / "agent_run_manifest.json"),
        "agent_output": str(output_dir / "agent_output.json"),
        "verifier_result": str(output_dir / "verifier_result.json"),
        "normalized_trajectory": str(output_dir / "normalized_trajectory.jsonl"),
    }
    if bundle_injection_trace is not None:
        write_json(output_dir / "bundle_injection_trace.json", bundle_injection_trace)
        paths["bundle_injection_trace"] = str(output_dir / "bundle_injection_trace.json")
    write_json(
        output_dir / "request_contract.json",
        {
            "schema_version": "agent_backend_request_contract.v1",
            "request": asdict(request),
        },
    )
    paths["request_contract"] = str(output_dir / "request_contract.json")
    return paths
