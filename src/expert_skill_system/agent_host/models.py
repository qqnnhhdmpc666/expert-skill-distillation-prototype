from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal


@dataclass(frozen=True)
class AgentHostRequest:
    bundle_digest: str
    task_id: str
    task: dict[str, Any]
    timeout_seconds: float = 120.0


@dataclass(frozen=True)
class AgentHostResult:
    schema_version: str = "agent_host_result.v1"
    host: str = ""
    host_version: str | None = None
    status: Literal["completed", "blocked", "failed", "timeout"] = "blocked"
    qualification_status: Literal["pass", "partial", "hard_blocked", "fail"] = "hard_blocked"
    bundle_digest: str = ""
    task_id: str = ""
    exit_code: int | None = None
    output: dict[str, Any] | None = None
    reason_codes: tuple[str, ...] = ()
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
