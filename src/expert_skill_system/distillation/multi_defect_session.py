from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class MultiDefectCase:
    case_dir: Path
    defect_id: str
    config: dict[str, Any]
    expert_material_v0: str
    baseline_policy: dict[str, Any]
    expected_repair_policy: dict[str, Any]
    expected_attribution: dict[str, Any]
    seed_failure_cases: list[dict[str, Any]]
    task_registry: Path
    base_bundle_data_dir: Path


def load_multi_defect_cases(case_root: Path) -> list[MultiDefectCase]:
    case_root = case_root.resolve()
    cases_dir = case_root / "cases"
    rows = []
    for case_dir in sorted(path for path in cases_dir.iterdir() if path.is_dir()):
        config = _read_json(case_dir / "distillation_config.json")
        rows.append(
            MultiDefectCase(
                case_dir=case_dir,
                defect_id=str(config["defect_id"]),
                config=config,
                expert_material_v0=(case_dir / "expert_material_v0.md").read_text(encoding="utf-8"),
                baseline_policy=dict(config["baseline_evidence_policy"]),
                expected_repair_policy=_read_json(case_dir / "expected_repair_policy.json"),
                expected_attribution=_read_json(case_dir / "expected_attribution.json"),
                seed_failure_cases=_read_jsonl(case_dir / "seed_failure_cases.jsonl"),
                task_registry=_resolve_repo_path(config["task_registry"]),
                base_bundle_data_dir=_resolve_repo_path(config["base_bundle_data_dir"]),
            )
        )
    if not rows:
        raise ValueError(f"no v1 distillation cases found under {cases_dir}")
    return rows


def write_variant_bundle_input(
    *,
    case: MultiDefectCase,
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


def _resolve_repo_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return (ROOT / path).resolve()


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
