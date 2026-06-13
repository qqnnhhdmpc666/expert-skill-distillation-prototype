from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class ExecutionRequest:
    scenario: str
    stage: str
    skill_dir: Path | None
    target_dir: Path
    output_dir: Path


@dataclass(frozen=True)
class ExecutionResult:
    backend_type: str
    output_path: Path
    trace_path: Path
    stdout_path: Path
    metadata_path: Path


class ExecutionBackend(Protocol):
    backend_type: str

    def run(self, request: ExecutionRequest) -> ExecutionResult:
        """Execute one agent attempt and write output, trace, stdout, and metadata artifacts."""
