from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..core.canonical import sha256_bytes
from ..core.models import utc_now

ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class DistillationCase:
    case_dir: Path
    config: dict[str, Any]
    expert_material_v0: str
    expected_evidence_policy: dict[str, Any]
    seed_failure_cases: list[dict[str, Any]]
    task_registry: Path
    base_bundle_data_dir: Path


def load_distillation_case(case_dir: Path) -> DistillationCase:
    case_dir = case_dir.resolve()
    config = _read_json(case_dir / "distillation_config.json")
    expert_material_v0 = (case_dir / "expert_material_v0.md").read_text(encoding="utf-8")
    expected_evidence_policy = _read_json(case_dir / "expected_evidence_policy.json")
    seed_failure_cases = _read_jsonl(case_dir / "seed_failure_cases.jsonl")
    task_registry = _resolve_repo_path(config["task_registry"])
    base_bundle_data_dir = _resolve_repo_path(config["base_bundle_data_dir"])
    return DistillationCase(
        case_dir=case_dir,
        config=config,
        expert_material_v0=expert_material_v0,
        expected_evidence_policy=expected_evidence_policy,
        seed_failure_cases=seed_failure_cases,
        task_registry=task_registry,
        base_bundle_data_dir=base_bundle_data_dir,
    )


def write_variant_bundle_input(
    *,
    case: DistillationCase,
    output_dir: Path,
    expert_material: str,
    evidence_policy: dict[str, Any],
) -> Path:
    input_dir = output_dir / "bundle_input"
    input_dir.mkdir(parents=True, exist_ok=True)
    task_contract = _read_json(case.base_bundle_data_dir / "task_contract.json")
    task_contract = {**task_contract, "required_evidence": list(evidence_policy["required_evidence"])}
    knowledge_contract = _read_json(case.base_bundle_data_dir / "knowledge_contract.json")
    (input_dir / "expert_material.md").write_text(expert_material, encoding="utf-8")
    _write_json(input_dir / "task_contract.json", task_contract)
    _write_json(input_dir / "knowledge_contract.json", knowledge_contract)
    _write_json(input_dir / "evidence_policy.json", evidence_policy)
    return input_dir


def write_session_manifest(
    *,
    case: DistillationCase,
    state_dir: Path,
    output_dir: Path,
    baseline_variant: str,
    revised_variant: str,
) -> dict[str, Any]:
    payload = {
        "schema_version": "distillation_session_manifest.v1",
        "case_id": case.config["case_id"],
        "created_at": utc_now(),
        "case_dir": str(case.case_dir),
        "state_dir": str(state_dir),
        "output_dir": str(output_dir),
        "skill_family": case.config["skill_family"],
        "task_registry": str(case.task_registry),
        "baseline_variant": baseline_variant,
        "revised_variant": revised_variant,
        "expert_material_v0_hash": sha256_bytes(case.expert_material_v0.encode("utf-8")),
        "active_binding_isolation": "state_dir_only",
        "claim_boundary": case.config["claim_boundary"],
    }
    _write_json(output_dir / "distillation_session_manifest.json", payload)
    return payload


def _resolve_repo_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return (ROOT / path).resolve()


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
