from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from .harbor_adapter import execution_report_from_harbor_snapshot, load_harbor_replay_snapshot
from .capability_registry import CAPABILITY_SPECS
from .schemas import ExecutionReport, SkillPackage
from .task_cases import ControlledTaskCase


@dataclass(frozen=True)
class RunnerContext:
    scenario_id: str
    backend: str
    target_dir: Path
    output_dir: Path
    attempt_id: str = "A1"
    skill_package: SkillPackage | None = None
    task_case: ControlledTaskCase | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RunnerResult:
    report: ExecutionReport
    output_path: Path | None = None
    stdout_path: Path | None = None
    stderr_path: Path | None = None
    metadata_path: Path | None = None
    artifact_paths: dict[str, Path] = field(default_factory=dict)


class BackendRunner(Protocol):
    name: str

    def run(self, context: RunnerContext) -> RunnerResult:
        """Execute one attempt and return a normalized report."""


def summarize_runner_context(context: RunnerContext) -> dict[str, Any]:
    return {
        "scenario_id": context.scenario_id,
        "backend": context.backend,
        "target_dir": str(context.target_dir),
        "output_dir": str(context.output_dir),
        "attempt_id": context.attempt_id,
        "skill_package": context.skill_package.to_dict() if context.skill_package is not None else None,
        "task_case": context.task_case.case_id if context.task_case is not None else None,
        "metadata": dict(context.metadata),
    }


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def _run_subprocess(command: list[str], *, cwd: Path, stdout_path: Path, stderr_path: Path) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(command, cwd=cwd, check=True, capture_output=True, text=True)
    _write_text(stdout_path, completed.stdout)
    _write_text(stderr_path, completed.stderr)
    return completed


def _apply_attempt_defect(item: dict[str, Any], defect: str | None, targeted: set[str]) -> dict[str, Any]:
    capability_id = str(item.get("capability_id", ""))
    target_hit = not targeted or capability_id in targeted
    if not defect or not target_hit:
        return item
    if defect in {"ownership_boundary_missing", "weak_evidence", "target_context_missing"}:
        item["evidence_span"] = ""
    if defect == "output_contract_error":
        item.pop("recommended_fix", None)
    return item


def _target_bound_evidence(capability_id: str, target_text: str) -> str:
    cap = CAPABILITY_SPECS[capability_id]
    normalized = target_text.strip()
    if not normalized:
        return cap.evidence_hint
    sentences = [segment.strip() for segment in normalized.split(".") if segment.strip()]
    for sentence in sentences:
        lowered = sentence.lower()
        if all(needle.lower() in lowered for needle in cap.detector_needles[:1]):
            return sentence
        if any(needle.lower() in lowered for needle in cap.detector_needles):
            return sentence
    for needle in cap.detector_needles:
        index = normalized.lower().find(needle.lower())
        if index >= 0:
            start = max(0, index - 32)
            end = min(len(normalized), index + max(len(needle), 64))
            return normalized[start:end].strip()
    return cap.evidence_hint


def resolve_task_conditioned_activation(skill_package: SkillPackage, task_case: ControlledTaskCase | None) -> dict[str, Any]:
    task_family = task_case.task_family if task_case is not None else ""
    metadata = dict(skill_package.metadata or {})
    groups = metadata.get("capability_groups", [])
    guard_name = str(metadata.get("out_of_scope_group") or "out_of_scope_guard")
    supported_families = {str(item) for item in metadata.get("supported_task_families", [])}
    normalized_groups: list[dict[str, Any]] = []
    for group in groups:
        if not isinstance(group, dict):
            continue
        normalized_groups.append(
            {
                "name": str(group.get("name") or ""),
                "task_families": tuple(str(item) for item in group.get("task_families", []) if str(item).strip()),
                "capabilities": tuple(str(item) for item in group.get("capabilities", []) if str(item).strip()),
            }
        )
    for group in normalized_groups:
        if task_family and task_family in group["task_families"]:
            return {
                "task_family": task_family,
                "activated_capability_group": group["name"] or "matched_group",
                "capabilities": group["capabilities"],
                "out_of_scope": False,
                "unsupported_task_family": None,
                "supported_task_families": sorted(supported_families or {item for entry in normalized_groups for item in entry["task_families"]}),
            }
    if not normalized_groups and task_family and skill_package.task_family == task_family:
        return {
            "task_family": task_family,
            "activated_capability_group": "package_default",
            "capabilities": tuple(skill_package.capabilities),
            "out_of_scope": False,
            "unsupported_task_family": None,
            "supported_task_families": [task_family],
        }
    return {
        "task_family": task_family,
        "activated_capability_group": guard_name,
        "capabilities": (),
        "out_of_scope": True,
        "unsupported_task_family": task_family or "unknown_task_family",
        "supported_task_families": sorted(supported_families or {item for entry in normalized_groups for item in entry["task_families"]}),
    }


class OfflineDeterministicRunner:
    name = "offline_deterministic"

    def run(self, context: RunnerContext) -> RunnerResult:
        if context.task_case is None:
            raise ValueError("OfflineDeterministicRunner requires task_case in RunnerContext")
        activation = None
        capabilities: list[str] = []
        notes: list[str] = []
        if context.skill_package is not None:
            activation = resolve_task_conditioned_activation(context.skill_package, context.task_case)
            capabilities = list(activation["capabilities"])
            context.metadata["task_family"] = activation["task_family"]
            context.metadata["activated_capability_group"] = activation["activated_capability_group"]
            context.metadata["supported_task_families"] = list(activation["supported_task_families"])
            context.metadata["out_of_scope"] = bool(activation["out_of_scope"])
            if activation["unsupported_task_family"]:
                context.metadata["unsupported_task_family"] = activation["unsupported_task_family"]
            if activation["out_of_scope"]:
                notes.extend(
                    [
                        "out_of_scope",
                        f"unsupported_task_family:{activation['unsupported_task_family']}",
                        f"activated_capability_group:{activation['activated_capability_group']}",
                    ]
                )
            else:
                notes.append(f"activated_capability_group:{activation['activated_capability_group']}")
        defect = str(context.metadata.get("defect") or "").strip() or None
        targeted = set(context.task_case.defect_capabilities)
        if defect == "ownership_boundary_missing" and not targeted:
            targeted.add("AUTH_OBJECT_OWNERSHIP")
        if defect == "output_contract_error" and not targeted:
            targeted.add("API_OVERBROAD_RISK")
        findings: list[dict[str, Any]] = []
        for capability_id in capabilities:
            cap = CAPABILITY_SPECS[capability_id]
            item = {
                "capability_id": capability_id,
                "issue": cap.title,
                "evidence_span": _target_bound_evidence(capability_id, context.task_case.target_asset),
                "recommended_fix": cap.fix_hint,
            }
            findings.append(_apply_attempt_defect(item, defect, targeted))
        report = ExecutionReport(
            attempt=context.attempt_id,
            backend=self.name,
            findings=tuple(findings),
            notes=tuple(notes),
        )
        output_path = context.output_dir / "agent_output.json"
        _write_json(output_path, report.to_dict())
        _write_text(context.output_dir / "stdout.log", f"{self.name} emitted {len(findings)} findings\n")
        _write_json(
            context.output_dir / "backend_metadata.json",
            {
                "backend_type": self.name,
                "attempt_id": context.attempt_id,
                "task_case": context.task_case.case_id,
                "generated_by": "src/skill_deployment/runner.py::OfflineDeterministicRunner",
                "task_family": context.metadata.get("task_family"),
                "activated_capability_group": context.metadata.get("activated_capability_group"),
                "out_of_scope": context.metadata.get("out_of_scope"),
                "unsupported_task_family": context.metadata.get("unsupported_task_family"),
            },
        )
        return RunnerResult(
            report=report,
            output_path=output_path,
            stdout_path=context.output_dir / "stdout.log",
            metadata_path=context.output_dir / "backend_metadata.json",
        )


class NonOracleLocalSemanticRunner:
    name = "non_oracle_local_semantic"

    def __init__(self, *, project_root: Path) -> None:
        self.project_root = project_root

    def run(self, context: RunnerContext) -> RunnerResult:
        output_path = context.output_dir / "agent_output.json"
        stdout_path = context.output_dir / "stdout.log"
        stderr_path = context.output_dir / "stderr.log"
        metadata_path = context.output_dir / "backend_metadata.json"
        if context.skill_package is None:
            report = ExecutionReport(attempt=context.attempt_id, backend=self.name, findings=())
            _write_json(output_path, report.to_dict())
            _write_text(stdout_path, "A0 no-skill baseline emitted no findings.\n")
            _write_json(metadata_path, {"backend_type": self.name, "stage": context.attempt_id})
            return RunnerResult(report=report, output_path=output_path, stdout_path=stdout_path, metadata_path=metadata_path)

        skill_dir = context.metadata.get("skill_dir")
        if not skill_dir:
            raise ValueError("NonOracleLocalSemanticRunner requires metadata['skill_dir']")
        active_capabilities = context.metadata.get("active_capabilities")
        if active_capabilities is None and context.task_case is not None:
            activation = resolve_task_conditioned_activation(context.skill_package, context.task_case)
            active_capabilities = list(activation["capabilities"])
            context.metadata["task_family"] = activation["task_family"]
            context.metadata["activated_capability_group"] = activation["activated_capability_group"]
            context.metadata["supported_task_families"] = list(activation["supported_task_families"])
            context.metadata["out_of_scope"] = bool(activation["out_of_scope"])
            if activation["unsupported_task_family"]:
                context.metadata["unsupported_task_family"] = activation["unsupported_task_family"]
        command = [
            sys.executable,
            str(self.project_root / "agents" / "non_oracle_local_security_agent.py"),
            "--skill",
            str(skill_dir),
            "--target",
            str(context.target_dir),
            "--out",
            str(context.output_dir),
        ]
        if active_capabilities is not None:
            command.extend(["--active-capabilities", ",".join(str(item) for item in active_capabilities)])
        _run_subprocess(command, cwd=self.project_root, stdout_path=stdout_path, stderr_path=stderr_path)
        payload = json.loads(output_path.read_text(encoding="utf-8"))
        payload["attempt"] = context.attempt_id
        payload["backend"] = self.name
        _write_json(output_path, payload)
        report = ExecutionReport.from_dict(payload)
        return RunnerResult(
            report=report,
            output_path=output_path,
            stdout_path=stdout_path,
            stderr_path=stderr_path,
            metadata_path=metadata_path if metadata_path.exists() else None,
        )


class LiveLLMSecurityRunner:
    name = "live_llm_text"

    def __init__(self, *, project_root: Path) -> None:
        self.project_root = project_root

    def run(self, context: RunnerContext) -> RunnerResult:
        output_path = context.output_dir / "security_report.json"
        stdout_path = context.output_dir / "stdout.log"
        stderr_path = context.output_dir / "stderr.log"
        metadata_path = context.output_dir / "backend_metadata.json"
        if context.skill_package is None:
            report = ExecutionReport(attempt=context.attempt_id, backend=self.name, findings=())
            _write_json(output_path, {"attempt": context.attempt_id, "backend": self.name, "findings": []})
            _write_text(stdout_path, "A0 no-skill baseline emitted no findings.\n")
            _write_text(stderr_path, "")
            _write_json(
                metadata_path,
                {
                    "backend_type": self.name,
                    "llm": True,
                    "stage": context.attempt_id,
                    "status": "baseline_no_skill",
                    "base_url_present": bool(os.environ.get("OPENAI_BASE_URL")),
                    "api_key_present": bool(os.environ.get("OPENAI_API_KEY")),
                    "model": os.environ.get("MODEL") or os.environ.get("OPENAI_MODEL"),
                },
            )
            return RunnerResult(report=report, output_path=output_path, stdout_path=stdout_path, stderr_path=stderr_path, metadata_path=metadata_path)

        skill_dir = context.metadata.get("skill_dir")
        if not skill_dir:
            raise ValueError("LiveLLMSecurityRunner requires metadata['skill_dir']")
        active_capabilities = context.metadata.get("active_capabilities")
        if active_capabilities is None and context.task_case is not None:
            activation = resolve_task_conditioned_activation(context.skill_package, context.task_case)
            active_capabilities = list(activation["capabilities"])
            context.metadata["task_family"] = activation["task_family"]
            context.metadata["activated_capability_group"] = activation["activated_capability_group"]
            context.metadata["supported_task_families"] = list(activation["supported_task_families"])
            context.metadata["out_of_scope"] = bool(activation["out_of_scope"])
            if activation["unsupported_task_family"]:
                context.metadata["unsupported_task_family"] = activation["unsupported_task_family"]
        command = [
            sys.executable,
            str(self.project_root / "agents" / "llm_security_agent.py"),
            "--skill",
            str(skill_dir),
            "--target",
            str(context.target_dir),
            "--out",
            str(context.output_dir),
        ]
        if context.metadata.get("base_url"):
            command.extend(["--base-url", str(context.metadata["base_url"])])
        if context.metadata.get("api_key"):
            command.extend(["--api-key", str(context.metadata["api_key"])])
        if context.metadata.get("model"):
            command.extend(["--model", str(context.metadata["model"])])
        if context.metadata.get("temperature") is not None:
            command.extend(["--temperature", str(context.metadata["temperature"])])
        if context.metadata.get("timeout") is not None:
            command.extend(["--timeout", str(context.metadata["timeout"])])
        if context.metadata.get("task_label"):
            command.extend(["--task-label", str(context.metadata["task_label"])])
        if context.metadata.get("contract_mode"):
            command.extend(["--contract-mode", str(context.metadata["contract_mode"])])
        if context.metadata.get("prompt_addendum"):
            command.extend(["--prompt-addendum", str(context.metadata["prompt_addendum"])])
        if active_capabilities is not None:
            command.extend(["--active-capabilities", ",".join(str(item) for item in active_capabilities)])
        _run_subprocess(command, cwd=self.project_root, stdout_path=stdout_path, stderr_path=stderr_path)
        payload = json.loads(output_path.read_text(encoding="utf-8"))
        payload["attempt"] = context.attempt_id
        payload["backend"] = self.name
        _write_json(output_path, payload)
        report = ExecutionReport.from_dict(payload)
        return RunnerResult(
            report=report,
            output_path=output_path,
            stdout_path=stdout_path,
            stderr_path=stderr_path,
            metadata_path=metadata_path if metadata_path.exists() else None,
        )


class HarborReplayRunner:
    def __init__(self, *, name: str, replay_root: Path) -> None:
        self.name = name
        self.replay_root = replay_root

    def run(self, context: RunnerContext) -> RunnerResult:
        attempt_id = context.metadata.get("replay_attempt") or context.attempt_id
        snapshot = load_harbor_replay_snapshot(self.replay_root, str(attempt_id), replay_id=self.name)
        report = execution_report_from_harbor_snapshot(snapshot, backend_name=self.name)
        return RunnerResult(
            report=report,
            output_path=snapshot.security_report_path,
            metadata_path=snapshot.backend_metadata_path,
            artifact_paths=snapshot.artifact_paths(),
        )


def get_backend_runner(name: str, *, project_root: Path) -> BackendRunner:
    if name == "offline_deterministic":
        return OfflineDeterministicRunner()
    if name == "non_oracle_local_semantic":
        return NonOracleLocalSemanticRunner(project_root=project_root)
    if name == "live_llm_text":
        return LiveLLMSecurityRunner(project_root=project_root)
    if name == "harbor_llm_repair_upload_replay":
        return HarborReplayRunner(name=name, replay_root=project_root / "outputs" / "harbor_llm_repair_loop_upload_001")
    if name == "harbor_llm_repair_config_replay":
        return HarborReplayRunner(name=name, replay_root=project_root / "outputs" / "harbor_llm_repair_loop_config_001")
    raise ValueError(f"unsupported backend runner: {name}")
