import json
from pathlib import Path

from skill_deployment import MaterialSource, distill_material_skill_bundle, distill_skill_bundle, project_case_capabilities, project_material_capabilities, select_controlled_task_cases


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


def test_project_material_capabilities_supports_public_like_materials() -> None:
    material = MaterialSource(
        source_id="public_upload_material_001",
        task_family="upload_security",
        title="Public upload guidance",
        material_text="Validate file type and signature, rename uploaded files, store them outside the web root, and keep audit logging for uploads.",
    )

    projections = project_material_capabilities(material)

    assert {item.capability_id for item in projections} == {
        "UPLOAD_TYPE_MAGIC",
        "UPLOAD_PATH_ISOLATION",
        "UPLOAD_AUDIT_RETENTION",
    }


def test_distill_material_skill_bundle_writes_open_material_package(tmp_path: Path) -> None:
    materials = [
        MaterialSource(
            source_id="public_upload_material_001",
            task_family="upload_security",
            title="Public upload guidance",
            material_text="Validate file type and signature, rename uploaded files, and store them outside the web root.",
        ),
        MaterialSource(
            source_id="public_upload_logging_material_001",
            task_family="upload_security",
            title="Public upload audit guidance",
            material_text="Submission and processing of user-generated content, especially file uploads, should be logged with audit retention.",
        ),
        MaterialSource(
            source_id="public_auth_material_001",
            task_family="auth_access_control",
            title="Public auth guidance",
            material_text="Enforce authorization on every request, apply least privilege, check object ownership, and avoid revealing identifiers in errors.",
        ),
    ]

    summary = distill_material_skill_bundle(
        skill_id="secure_code_review_open_material_test",
        version="v1",
        materials=materials,
        output_dir=tmp_path / "secure_code_review_open_material_test",
    )

    version_dir = Path(summary["version_dir"])
    manifest = json.loads((version_dir / "manifest.json").read_text(encoding="utf-8"))
    skill_text = (version_dir / "SKILL.md").read_text(encoding="utf-8")
    upload_group = next(group for group in manifest["metadata"]["capability_groups"] if group["name"] == "upload_security")

    assert (version_dir / "provenance" / "source_materials_manifest.json").exists()
    assert set(manifest["metadata"]["supported_task_families"]) == {"upload_security", "auth_access_control"}
    assert set(upload_group["capabilities"]) == {"UPLOAD_TYPE_MAGIC", "UPLOAD_PATH_ISOLATION", "UPLOAD_AUDIT_RETENTION"}
    assert "review_rule:" in skill_text
    assert "distilled_public_lesson:" in skill_text
