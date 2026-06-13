from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ControlledTaskCase:
    case_id: str
    aliases: tuple[str, ...]
    title: str
    task_family: str
    expert_material: str
    target_asset: str
    expected_capabilities: tuple[str, ...]
    v1_capabilities: tuple[str, ...]
    typical_feedback: str
    typical_repair: str
    verifier_contract: dict[str, Any]
    a1_defect: str
    defect_capabilities: tuple[str, ...]
    negative_control: bool = False
    metadata: dict[str, Any] | None = None
    source_dir: str | None = None


TaskCase = ControlledTaskCase


@dataclass(frozen=True)
class LegacyHoldoutTaskCase:
    case_id: str
    input_text: str
    expected_rule_ids: tuple[str, ...]
    negative_rule_ids: tuple[str, ...] = ()
    false_positive_controls: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    source_dir: str | None = None

    @classmethod
    def from_directory(cls, case_dir: Path) -> "LegacyHoldoutTaskCase":
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


REQUIRED_CASE_FIELDS = (
    "case_id",
    "title",
    "task_family",
    "expected_capabilities",
    "v1_capabilities",
    "typical_feedback",
    "typical_repair",
)


def load_json_yaml(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_required_text(path: Path) -> str:
    if not path.exists():
        raise ValueError(f"missing required task case file: {path}")
    return path.read_text(encoding="utf-8", errors="replace").strip()


def aliases_for_case(case_id: str, family: str) -> tuple[str, ...]:
    aliases = {case_id, family}
    for value in (case_id, family):
        if value.endswith("_001"):
            aliases.add(value[:-4])
        if "_" in value:
            aliases.add(value.split("_", 1)[0])
            parts = value.split("_")
            if len(parts) >= 2:
                aliases.add("_".join(parts[:2]))
    if case_id.startswith("api_review") or family == "api_or_code_review":
        aliases.update({"api_review", "api", "code_review"})
    return tuple(sorted(aliases))


def validate_controlled_task_case_dir(case_dir: Path) -> dict[str, Any]:
    errors: list[str] = []
    required_files = (
        "case.yaml",
        "source_materials/expert_material.md",
        "target_asset/target.md",
        "expected_behavior.yaml",
        "verifier_contract.yaml",
    )
    for rel_path in required_files:
        if not (case_dir / rel_path).exists():
            errors.append(f"missing {rel_path}")
    case_data: dict[str, Any] = {}
    if (case_dir / "case.yaml").exists():
        try:
            case_data = load_json_yaml(case_dir / "case.yaml")
        except json.JSONDecodeError as exc:
            errors.append(f"case.yaml is not JSON-compatible YAML: {exc}")
    for field in REQUIRED_CASE_FIELDS:
        if field not in case_data:
            errors.append(f"case.yaml missing {field}")
    expected = case_data.get("expected_capabilities", [])
    v1 = case_data.get("v1_capabilities", [])
    is_negative_control = bool(case_data.get("negative_control"))
    if not isinstance(expected, list) or (not expected and not is_negative_control):
        errors.append("expected_capabilities must be a non-empty list")
    if not isinstance(v1, list):
        errors.append("v1_capabilities must be a list")
    verifier_contract_path = case_dir / "verifier_contract.yaml"
    verifier_contract = {}
    if verifier_contract_path.exists():
        try:
            verifier_contract = load_json_yaml(verifier_contract_path)
        except json.JSONDecodeError as exc:
            errors.append(f"verifier_contract.yaml is not JSON-compatible YAML: {exc}")
    return {
        "case_dir": str(case_dir),
        "case_id": case_data.get("case_id", case_dir.name),
        "task_family": case_data.get("task_family"),
        "status": "ok" if not errors else "error",
        "errors": errors,
        "expected_capabilities": expected if isinstance(expected, list) else [],
        "negative_control": is_negative_control,
        "verifier_contract": verifier_contract,
    }


def controlled_task_case_from_directory(case_dir: Path) -> ControlledTaskCase:
    result = validate_controlled_task_case_dir(case_dir)
    if result["errors"]:
        raise ValueError(f"invalid task case at {case_dir}: {result['errors']}")
    case_data = load_json_yaml(case_dir / "case.yaml")
    case_id = str(case_data["case_id"])
    family = str(case_data["task_family"])
    return ControlledTaskCase(
        case_id=case_id,
        aliases=aliases_for_case(case_id, family),
        title=str(case_data["title"]),
        task_family=family,
        expert_material=read_required_text(case_dir / "source_materials" / "expert_material.md"),
        target_asset=read_required_text(case_dir / "target_asset" / "target.md"),
        expected_capabilities=tuple(str(item) for item in case_data["expected_capabilities"]),
        v1_capabilities=tuple(str(item) for item in case_data["v1_capabilities"]),
        typical_feedback=str(case_data.get("typical_feedback", "missing_capability")),
        typical_repair=str(case_data.get("typical_repair", "")),
        verifier_contract=result["verifier_contract"],
        a1_defect=str(case_data.get("a1_defect", case_data.get("typical_feedback", "missing_capability"))),
        defect_capabilities=tuple(str(item) for item in case_data.get("defect_capabilities", [])),
        negative_control=bool(case_data.get("negative_control")),
        metadata={str(key): value for key, value in case_data.items() if key not in REQUIRED_CASE_FIELDS},
        source_dir=str(case_dir),
    )


def load_controlled_task_cases(root: Path, *, include_negative_controls: bool = False) -> list[ControlledTaskCase]:
    cases: list[ControlledTaskCase] = []
    for case_dir in sorted(item for item in root.iterdir() if item.is_dir()):
        if not (case_dir / "case.yaml").exists():
            continue
        case = controlled_task_case_from_directory(case_dir)
        if case.negative_control and not include_negative_controls:
            continue
        cases.append(case)
    return cases


def select_controlled_task_cases(root: Path, names: str, *, include_negative_controls: bool = False) -> list[ControlledTaskCase]:
    requested = {item.strip() for item in names.split(",") if item.strip()}
    cases = load_controlled_task_cases(root, include_negative_controls=include_negative_controls)
    selected: list[ControlledTaskCase] = []
    for case in cases:
        if case.case_id in requested or any(alias in requested for alias in case.aliases):
            selected.append(case)
    known_names = {case.case_id for case in selected} | {alias for case in selected for alias in case.aliases}
    unknown = requested - known_names
    if unknown:
        raise ValueError(f"unknown scenarios: {sorted(unknown)}")
    return selected


def load_legacy_holdout_task_cases(root: Path) -> list[LegacyHoldoutTaskCase]:
    return [LegacyHoldoutTaskCase.from_directory(path) for path in sorted(root.iterdir()) if path.is_dir()]
