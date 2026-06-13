import json
from pathlib import Path

from skill_deployment import distill_skill_bundle, project_case_capabilities, select_controlled_task_cases


ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = ROOT / "data" / "task_cases"


def test_project_case_capabilities_selects_from_expert_material_keywords() -> None:
    case = select_controlled_task_cases(DATA_ROOT, "upload")[0]

    projections = project_case_capabilities(case)

    assert {item.capability_id for item in projections} == {
        "UPLOAD_TYPE_MAGIC",
        "UPLOAD_PATH_ISOLATION",
        "UPLOAD_AUDIT_RETENTION",
    }
    assert all(item.score > 0 for item in projections)
    assert all(item.source_case_id == "upload_security_001" for item in projections)


def test_distill_skill_bundle_writes_installable_task_conditioned_package(tmp_path: Path) -> None:
    cases = select_controlled_task_cases(DATA_ROOT, "upload,config,api_review,auth")

    summary = distill_skill_bundle(
        skill_id="secure_code_review_distilled_test",
        version="v1",
        cases=cases,
        output_dir=tmp_path / "secure_code_review_distilled_test",
        title="Test Distilled Skill",
    )

    output_dir = Path(summary["output_dir"])
    version_dir = Path(summary["version_dir"])
    manifest = json.loads((version_dir / "manifest.json").read_text(encoding="utf-8"))
    groups = manifest["metadata"]["capability_groups"]

    assert output_dir.exists()
    assert (output_dir / "SKILL.md").exists()
    assert (version_dir / "SKILL.md").exists()
    assert (version_dir / "provenance" / "distillation_trace.json").exists()
    assert {group["name"] for group in groups} >= {
        "upload_security",
        "config_security",
        "api_or_code_review",
        "auth_access_control",
        "out_of_scope_guard",
    }
    assert set(manifest["metadata"]["supported_task_families"]) == {
        "upload_security",
        "config_security",
        "api_or_code_review",
        "auth_access_control",
    }
