from __future__ import annotations

import json
from pathlib import Path

from expert_skill_system.distillation.multi_defect_session import load_multi_defect_cases
from scripts.run_distillation_loop_v1 import main as run_distillation_loop_v1

CASE_ROOT = Path("data/distillation_cases/repo_dependency_use_triage_v1")


def test_v1_case_metadata_declares_expected_attribution_targets() -> None:
    cases = load_multi_defect_cases(CASE_ROOT)
    expected = {case.defect_id: case.expected_attribution for case in cases}

    assert expected["D1_skill_missing_rule"]["repair_target"] == "skill_rule"
    assert expected["D2_skill_overgeneralized_rule"]["failure_type"] == "skill_overgeneralized_rule"
    assert expected["D3_knowledge_gap"]["repair_target"] == "knowledge_projection"
    assert expected["D4_evidence_binding_gap"]["repair_target"] == "evidence_binding_plan"


def test_v1_attribution_matches_expected_defect_types(tmp_path: Path) -> None:
    output_dir = tmp_path / "v1-output"
    run_distillation_loop_v1(
        [
            "--case-root",
            str(CASE_ROOT),
            "--state-dir",
            str(tmp_path / "v1-state"),
            "--output",
            str(output_dir),
        ]
    )
    expected = {
        "D1_skill_missing_rule": ("skill_missing_rule", "skill_rule"),
        "D2_skill_overgeneralized_rule": ("skill_overgeneralized_rule", "skill_rule"),
        "D3_knowledge_gap": ("knowledge_gap", "knowledge_projection"),
        "D4_evidence_binding_gap": ("evidence_binding_gap", "evidence_binding_plan"),
    }
    for defect_id, (failure_type, repair_target) in expected.items():
        records = _read_jsonl(output_dir / "cases" / defect_id / "failure_attribution.jsonl")
        assert any(record["failure_type"] == failure_type and record["repair_target"] == repair_target for record in records)
        revision = _read_json(output_dir / "cases" / defect_id / "revision_plan.json")
        assert revision["task_specific_patch"] is False
        assert revision["patched_task_answers"] == []
        assert revision["applies_to_task_family"] == "dependency_use_triage"


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
