from pathlib import Path

from skill_deployment import controlled_task_case_from_directory, select_controlled_task_cases, validate_controlled_task_case_dir


ROOT = Path("data/task_cases")


def test_controlled_task_case_loader_reads_positive_case() -> None:
    case = controlled_task_case_from_directory(ROOT / "upload_security_001")

    assert case.case_id == "upload_security_001"
    assert case.task_family == "upload_security"
    assert "UPLOAD_TYPE_MAGIC" in case.expected_capabilities
    assert case.negative_control is False


def test_controlled_task_case_validation_allows_negative_control() -> None:
    payload = validate_controlled_task_case_dir(ROOT / "config_security_false_positive_control")

    assert payload["status"] == "ok"
    assert payload["negative_control"] is True
    assert payload["expected_capabilities"] == []


def test_select_controlled_task_cases_resolves_alias() -> None:
    selected = select_controlled_task_cases(ROOT, "upload")

    assert len(selected) == 1
    assert selected[0].case_id == "upload_security_001"


def test_controlled_task_case_validation_rejects_malformed_case(tmp_path: Path) -> None:
    case_dir = tmp_path / "broken_case"
    (case_dir / "source_materials").mkdir(parents=True)
    (case_dir / "target_asset").mkdir(parents=True)
    (case_dir / "source_materials" / "expert_material.md").write_text("x", encoding="utf-8")
    (case_dir / "target_asset" / "target.md").write_text("y", encoding="utf-8")
    (case_dir / "case.yaml").write_text('{"case_id":"broken","title":"Broken","task_family":"demo","expected_capabilities":[],"v1_capabilities":[]}', encoding="utf-8")

    payload = validate_controlled_task_case_dir(case_dir)

    assert payload["status"] == "error"
    assert any("missing expected_behavior.yaml" in error or "case.yaml missing typical_feedback" in error for error in payload["errors"])
