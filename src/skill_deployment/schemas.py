from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class TaskCase:
    """Minimal task-case schema used by the controlled API-review family."""

    case_id: str
    input_text: str
    expected_rule_ids: tuple[str, ...]
    negative_rule_ids: tuple[str, ...] = ()
    false_positive_controls: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    source_dir: str | None = None

    @classmethod
    def from_directory(cls, case_dir: Path) -> "TaskCase":
        input_path = case_dir / "case.md"
        expected_path = case_dir / "expected.json"
        if not input_path.exists():
            raise ValueError(f"{case_dir} is missing case.md input")
        if not expected_path.exists():
            raise ValueError(f"{case_dir} is missing expected.json")
        payload = json.loads(expected_path.read_text(encoding="utf-8"))
        metadata = payload.get("metadata")
        if metadata is None and "notes" in payload:
            metadata = {"notes": payload["notes"]}
        case = cls(
            case_id=str(payload.get("case_id") or case_dir.name),
            input_text=input_path.read_text(encoding="utf-8"),
            expected_rule_ids=tuple(str(rule_id) for rule_id in payload.get("expected_rule_ids", [])),
            negative_rule_ids=tuple(str(rule_id) for rule_id in payload.get("negative_rule_ids", [])),
            false_positive_controls=tuple(str(rule_id) for rule_id in payload.get("false_positive_controls", [])),
            metadata=dict(metadata or {}),
            source_dir=str(case_dir),
        )
        case.validate()
        return case

    def validate(self) -> None:
        if not self.case_id.strip():
            raise ValueError("case_id must be non-empty")
        if not self.input_text.strip():
            raise ValueError(f"{self.case_id}: input_text must be non-empty")
        if not isinstance(self.expected_rule_ids, tuple):
            raise ValueError(f"{self.case_id}: expected_rule_ids must be a tuple")
        if not self.negative_rule_ids and not self.false_positive_controls:
            raise ValueError(f"{self.case_id}: negative_rule_ids or false_positive_controls must be provided")
        if not self.metadata:
            raise ValueError(f"{self.case_id}: metadata must be provided")


def load_task_cases(root: Path) -> list[TaskCase]:
    return [TaskCase.from_directory(path) for path in sorted(root.iterdir()) if path.is_dir()]

