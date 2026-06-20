from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields
from datetime import UTC, datetime
from typing import Any, ClassVar, Literal, TypeVar

T = TypeVar("T", bound="StrictModel")


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


@dataclass(frozen=True)
class StrictModel:
    schema_version: str
    SCHEMA_VERSION: ClassVar[str] = ""

    def __post_init__(self) -> None:
        if self.schema_version != self.SCHEMA_VERSION:
            raise ValueError(f"expected schema_version {self.SCHEMA_VERSION!r}, got {self.schema_version!r}")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def _strict_payload(cls, payload: dict[str, Any]) -> dict[str, Any]:
        expected = {item.name for item in fields(cls)}
        unknown = set(payload) - expected
        if unknown:
            raise ValueError(f"unknown fields for {cls.__name__}: {sorted(unknown)}")
        return payload


@dataclass(frozen=True)
class ArtifactRef(StrictModel):
    SCHEMA_VERSION: ClassVar[str] = "artifact_ref.v1"
    schema_version: str = SCHEMA_VERSION
    artifact_id: str = ""
    digest: str = ""
    media_type: str = "application/octet-stream"
    artifact_schema_version: str = "opaque.v1"
    size_bytes: int = 0

    def __post_init__(self) -> None:
        super().__post_init__()
        if not self.artifact_id or not self.digest.startswith("sha256:") or self.size_bytes < 0:
            raise ValueError("invalid ArtifactRef")

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ArtifactRef:
        return cls(**cls._strict_payload(payload))


@dataclass(frozen=True)
class StageResult(StrictModel):
    SCHEMA_VERSION: ClassVar[str] = "compiler_stage_result.v1"
    schema_version: str = SCHEMA_VERSION
    build_id: str = ""
    stage_id: str = ""
    status: Literal["complete", "partial", "blocked", "rejected"] = "complete"
    input_refs: tuple[dict[str, Any], ...] = ()
    output_refs: tuple[dict[str, Any], ...] = ()
    issue_refs: tuple[dict[str, Any], ...] = ()
    evidence_request_refs: tuple[dict[str, Any], ...] = ()
    quarantined_item_refs: tuple[dict[str, Any], ...] = ()
    model_call_refs: tuple[dict[str, Any], ...] = ()
    deterministic_tool_refs: tuple[dict[str, Any], ...] = ()
    metrics: dict[str, Any] = field(default_factory=dict)
    next_action: Literal["continue", "acquire_evidence", "rebuild", "stop"] = "continue"

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> StageResult:
        data = cls._strict_payload(payload)
        tuple_fields = {
            "input_refs",
            "output_refs",
            "issue_refs",
            "evidence_request_refs",
            "quarantined_item_refs",
            "model_call_refs",
            "deterministic_tool_refs",
        }
        normalized = {key: tuple(value) if key in tuple_fields else value for key, value in data.items()}
        return cls(**normalized)


@dataclass(frozen=True)
class DomainDecision:
    dependency_name: str
    normalized_name: str
    resolved_version: str | None
    advisory_id: str
    verdict: Literal["advisory_applicable", "advisory_not_applicable", "unresolved"]
    reason_codes: tuple[str, ...] = ()
    evidence_refs: tuple[dict[str, Any], ...] = ()

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> DomainDecision:
        expected = {item.name for item in fields(cls)}
        unknown = set(payload) - expected
        if unknown:
            raise ValueError(f"unknown DomainDecision fields: {sorted(unknown)}")
        data = dict(payload)
        data["reason_codes"] = tuple(data.get("reason_codes", ()))
        data["evidence_refs"] = tuple(data.get("evidence_refs", ()))
        return cls(**data)


@dataclass(frozen=True)
class DomainOutcome(StrictModel):
    SCHEMA_VERSION: ClassVar[str] = "python_advisory_outcome.v1"
    schema_version: str = SCHEMA_VERSION
    task_status: Literal["decision", "parse_error"] = "decision"
    decision: DomainDecision | None = None
    parse_diagnostics: tuple[dict[str, Any], ...] = ()

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.task_status == "decision" and self.decision is None:
            raise ValueError("decision is required when task_status=decision")
        if self.task_status == "parse_error" and not self.parse_diagnostics:
            raise ValueError("parse_diagnostics are required when task_status=parse_error")

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> DomainOutcome:
        data = dict(cls._strict_payload(payload))
        if isinstance(data.get("decision"), dict):
            data["decision"] = DomainDecision.from_dict(data["decision"])
        data["parse_diagnostics"] = tuple(data.get("parse_diagnostics", ()))
        return cls(**data)


@dataclass(frozen=True)
class FailureDetail:
    category: str
    reason_codes: tuple[str, ...] = ()
    retryable: bool = False

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> FailureDetail:
        expected = {item.name for item in fields(cls)}
        unknown = set(payload) - expected
        if unknown:
            raise ValueError(f"unknown FailureDetail fields: {sorted(unknown)}")
        data = dict(payload)
        data["reason_codes"] = tuple(data.get("reason_codes", ()))
        return cls(**data)


@dataclass(frozen=True)
class ExecutionEnvelope(StrictModel):
    SCHEMA_VERSION: ClassVar[str] = "execution_envelope.v1"
    schema_version: str = SCHEMA_VERSION
    execution_status: Literal["completed", "blocked", "runtime_failure"] = "completed"
    domain_outcome: DomainOutcome | None = None
    failure: FailureDetail | None = None
    session_id: str = ""
    bundle_digest: str = ""

    def __post_init__(self) -> None:
        super().__post_init__()
        if not self.session_id or not self.bundle_digest.startswith("sha256:"):
            raise ValueError("session_id and bundle_digest are required")
        if self.execution_status == "completed" and self.domain_outcome is None:
            raise ValueError("completed execution requires a domain outcome")
        if self.execution_status != "completed" and self.failure is None:
            raise ValueError("blocked/runtime_failure execution requires failure details")

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ExecutionEnvelope:
        data = dict(cls._strict_payload(payload))
        if isinstance(data.get("domain_outcome"), dict):
            data["domain_outcome"] = DomainOutcome.from_dict(data["domain_outcome"])
        if isinstance(data.get("failure"), dict):
            data["failure"] = FailureDetail.from_dict(data["failure"])
        return cls(**data)


@dataclass(frozen=True)
class ActiveBinding(StrictModel):
    SCHEMA_VERSION: ClassVar[str] = "active_binding.v1"
    schema_version: str = SCHEMA_VERSION
    binding_key: str = ""
    bundle_digest: str = ""
    generation: int = 0
    updated_at: str = ""

    def __post_init__(self) -> None:
        super().__post_init__()
        if not self.binding_key or not self.bundle_digest.startswith("sha256:") or self.generation < 1:
            raise ValueError("invalid ActiveBinding")


@dataclass(frozen=True)
class DeploymentEvent(StrictModel):
    SCHEMA_VERSION: ClassVar[str] = "deployment_event.v1"
    schema_version: str = SCHEMA_VERSION
    event_id: str = ""
    event_type: Literal["promote", "reject", "rollback"] = "promote"
    binding_key: str = ""
    from_digest: str | None = None
    to_digest: str | None = None
    generation_before: int = 0
    generation_after: int = 0
    reason_codes: tuple[str, ...] = ()
    created_at: str = ""

