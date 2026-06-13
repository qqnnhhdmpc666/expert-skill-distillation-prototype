from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .schemas import ExecutionReport


@dataclass(frozen=True)
class HarborReplaySnapshot:
    replay_id: str
    replay_root: Path
    attempt_id: str
    security_report_path: Path
    verifier_report_path: Path | None
    reward_path: Path | None
    target_reads_path: Path | None
    skill_manifest_path: Path | None
    backend_metadata_path: Path | None
    summary_path: Path | None

    def artifact_paths(self) -> dict[str, Path]:
        artifacts: dict[str, Path] = {
            "security_report": self.security_report_path,
        }
        if self.verifier_report_path is not None:
            artifacts["verifier_report"] = self.verifier_report_path
        if self.reward_path is not None:
            artifacts["reward"] = self.reward_path
        if self.target_reads_path is not None:
            artifacts["target_reads"] = self.target_reads_path
        if self.skill_manifest_path is not None:
            artifacts["skill_manifest"] = self.skill_manifest_path
        if self.backend_metadata_path is not None:
            artifacts["backend_metadata"] = self.backend_metadata_path
        if self.summary_path is not None:
            artifacts["summary"] = self.summary_path
        return artifacts


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def attempt_dir_for(replay_root: Path, attempt_id: str) -> Path:
    normalized = attempt_id.strip().upper()
    if normalized not in {"A1", "A2"}:
        raise ValueError(f"Harbor replay adapter supports only A1/A2 attempts, got: {attempt_id}")
    return replay_root / normalized


def load_harbor_replay_snapshot(replay_root: Path, attempt_id: str, *, replay_id: str) -> HarborReplaySnapshot:
    attempt_dir = attempt_dir_for(replay_root, attempt_id)
    if not attempt_dir.exists():
        raise FileNotFoundError(f"Harbor replay attempt directory missing: {attempt_dir}")
    security_report_path = attempt_dir / "security_report.json"
    if not security_report_path.exists():
        raise FileNotFoundError(f"Harbor replay security report missing: {security_report_path}")
    verifier_report_path = attempt_dir / "verifier_report.json"
    reward_path = attempt_dir / "reward.json"
    target_reads_path = attempt_dir / "target_reads.json"
    skill_manifest_path = attempt_dir / "skill_manifest.json"
    backend_metadata_path = attempt_dir / "backend_metadata.json"
    summary_path = replay_root / "summary.json"
    return HarborReplaySnapshot(
        replay_id=replay_id,
        replay_root=replay_root,
        attempt_id=attempt_id,
        security_report_path=security_report_path,
        verifier_report_path=verifier_report_path if verifier_report_path.exists() else None,
        reward_path=reward_path if reward_path.exists() else None,
        target_reads_path=target_reads_path if target_reads_path.exists() else None,
        skill_manifest_path=skill_manifest_path if skill_manifest_path.exists() else None,
        backend_metadata_path=backend_metadata_path if backend_metadata_path.exists() else None,
        summary_path=summary_path if summary_path.exists() else None,
    )


def execution_report_from_harbor_snapshot(snapshot: HarborReplaySnapshot, *, backend_name: str) -> ExecutionReport:
    payload = load_json(snapshot.security_report_path)
    findings = payload.get("findings", [])
    if not isinstance(findings, list):
        raise ValueError(f"Harbor replay findings must be a list: {snapshot.security_report_path}")
    return ExecutionReport(
        attempt=snapshot.attempt_id,
        backend=backend_name,
        findings=tuple(dict(item) for item in findings if isinstance(item, dict)),
    )
