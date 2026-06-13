from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from .task_cases import ControlledTaskCase as TaskCase


@dataclass(frozen=True)
class SkillPackage:
    skill_id: str
    version: str
    task_family: str
    capabilities: tuple[str, ...]
    output_contract: tuple[str, ...] = ()
    trace_contract: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.skill_id.strip():
            raise ValueError("skill_id must be non-empty")
        if not self.version.strip():
            raise ValueError("version must be non-empty")
        if not self.task_family.strip():
            raise ValueError("task_family must be non-empty")
        if not self.capabilities:
            raise ValueError("capabilities must be non-empty")

    def to_dict(self) -> dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "version": self.version,
            "task_family": self.task_family,
            "capabilities": list(self.capabilities),
            "output_contract": list(self.output_contract),
            "trace_contract": list(self.trace_contract),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "SkillPackage":
        instance = cls(
            skill_id=str(payload["skill_id"]),
            version=str(payload["version"]),
            task_family=str(payload["task_family"]),
            capabilities=tuple(str(item) for item in payload.get("capabilities", [])),
            output_contract=tuple(str(item) for item in payload.get("output_contract", [])),
            trace_contract=tuple(str(item) for item in payload.get("trace_contract", [])),
            metadata=dict(payload.get("metadata", {})),
        )
        instance.validate()
        return instance


@dataclass(frozen=True)
class ExecutionReport:
    attempt: str
    backend: str
    findings: tuple[dict[str, Any], ...]
    notes: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.attempt.strip():
            raise ValueError("attempt must be non-empty")
        if not self.backend.strip():
            raise ValueError("backend must be non-empty")

    def to_dict(self) -> dict[str, Any]:
        return {
            "attempt": self.attempt,
            "backend": self.backend,
            "findings": [dict(item) for item in self.findings],
            "notes": list(self.notes),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ExecutionReport":
        instance = cls(
            attempt=str(payload["attempt"]),
            backend=str(payload["backend"]),
            findings=tuple(dict(item) for item in payload.get("findings", [])),
            notes=tuple(str(item) for item in payload.get("notes", [])),
        )
        instance.validate()
        return instance


@dataclass(frozen=True)
class VerifierReport:
    passed: bool
    feedback_type: str
    missing_capabilities: tuple[str, ...] = ()
    false_positive_capabilities: tuple[str, ...] = ()
    schema_errors: tuple[str, ...] = ()
    weak_evidence_capabilities: tuple[str, ...] = ()
    unsupported_evidence_capabilities: tuple[str, ...] = ()
    scores: dict[str, float] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.feedback_type.strip():
            raise ValueError("feedback_type must be non-empty")

    def to_dict(self) -> dict[str, Any]:
        return {
            "pass": self.passed,
            "feedback_type": self.feedback_type,
            "missing_capabilities": list(self.missing_capabilities),
            "false_positive_capabilities": list(self.false_positive_capabilities),
            "schema_errors": list(self.schema_errors),
            "weak_evidence_capabilities": list(self.weak_evidence_capabilities),
            "unsupported_evidence_capabilities": list(self.unsupported_evidence_capabilities),
            "scores": dict(self.scores),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "VerifierReport":
        instance = cls(
            passed=bool(payload.get("pass", payload.get("passed", False))),
            feedback_type=str(payload["feedback_type"]),
            missing_capabilities=tuple(str(item) for item in payload.get("missing_capabilities", [])),
            false_positive_capabilities=tuple(str(item) for item in payload.get("false_positive_capabilities", [])),
            schema_errors=tuple(str(item) for item in payload.get("schema_errors", [])),
            weak_evidence_capabilities=tuple(str(item) for item in payload.get("weak_evidence_capabilities", [])),
            unsupported_evidence_capabilities=tuple(str(item) for item in payload.get("unsupported_evidence_capabilities", [])),
            scores={str(key): float(value) for key, value in dict(payload.get("scores", {})).items()},
        )
        instance.validate()
        return instance


@dataclass(frozen=True)
class PatchPlan:
    feedback_type: str
    repair_action: str
    before_capabilities: tuple[str, ...] = ()
    after_capabilities: tuple[str, ...] = ()
    details: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.feedback_type.strip():
            raise ValueError("feedback_type must be non-empty")
        if not self.repair_action.strip():
            raise ValueError("repair_action must be non-empty")

    def to_dict(self) -> dict[str, Any]:
        return {
            "feedback_type": self.feedback_type,
            "repair_action": self.repair_action,
            "before_capabilities": list(self.before_capabilities),
            "after_capabilities": list(self.after_capabilities),
            **dict(self.details),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "PatchPlan":
        reserved = {"feedback_type", "repair_action", "before_capabilities", "after_capabilities"}
        instance = cls(
            feedback_type=str(payload["feedback_type"]),
            repair_action=str(payload["repair_action"]),
            before_capabilities=tuple(str(item) for item in payload.get("before_capabilities", [])),
            after_capabilities=tuple(str(item) for item in payload.get("after_capabilities", [])),
            details={str(key): value for key, value in payload.items() if key not in reserved},
        )
        instance.validate()
        return instance


@dataclass(frozen=True)
class GateDecision:
    decision: Literal["accept", "accept_no_change", "reject"]
    intervention: Literal["soft", "hard"]
    reason: str
    scores: dict[str, float] = field(default_factory=dict)
    refs: dict[str, str] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.reason.strip():
            raise ValueError("reason must be non-empty")

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "decision": self.decision,
            "intervention": self.intervention,
            "reason": self.reason,
            "scores": dict(self.scores),
        }
        payload.update(dict(self.refs))
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "GateDecision":
        reserved = {"decision", "intervention", "reason", "scores"}
        instance = cls(
            decision=str(payload["decision"]),
            intervention=str(payload["intervention"]),
            reason=str(payload["reason"]),
            scores={str(key): float(value) for key, value in dict(payload.get("scores", {})).items()},
            refs={str(key): str(value) for key, value in payload.items() if key not in reserved},
        )
        instance.validate()
        return instance


@dataclass(frozen=True)
class TraceRecord:
    event: str
    capability_id: str | None = None
    evidence_span: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.event.strip():
            raise ValueError("event must be non-empty")

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"event": self.event}
        if self.capability_id is not None:
            result["capability_id"] = self.capability_id
        if self.evidence_span is not None:
            result["evidence_span"] = self.evidence_span
        result.update(dict(self.payload))
        return result

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "TraceRecord":
        reserved = {"event", "capability_id", "evidence_span"}
        instance = cls(
            event=str(payload["event"]),
            capability_id=str(payload["capability_id"]) if payload.get("capability_id") is not None else None,
            evidence_span=str(payload["evidence_span"]) if payload.get("evidence_span") is not None else None,
            payload={str(key): value for key, value in payload.items() if key not in reserved},
        )
        instance.validate()
        return instance
