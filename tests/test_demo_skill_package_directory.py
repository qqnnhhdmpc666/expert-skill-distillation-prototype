import json
import sys
from types import SimpleNamespace

sys.modules.setdefault("streamlit", SimpleNamespace())
from demo.streamlit_app import build_run, package_directory_files, scenario_by_id, target_asset_files


def test_upload_skill_package_has_deployable_directory_contract() -> None:
    scenario = scenario_by_id("upload")
    pkg = build_run(scenario)["pkg_v2"]
    files = package_directory_files(pkg, scenario)

    assert "manifest.yaml" in files
    assert "SKILL.md" in files
    assert "contracts/output_schema.json" in files
    assert "contracts/verifier_contract.yaml" in files
    assert "trace_policy.yaml" in files
    assert "rules/R005_upload_type_and_storage.yaml" in files
    assert "rules/R006_audit_logging_retention.yaml" in files

    manifest = files["manifest.yaml"]
    assert "schema_version: 0.2.0" in manifest
    assert 'package_id: "upload/v2"' in manifest
    assert "entrypoint: SKILL.md" in manifest
    assert "source_materials: source_materials/*" in manifest
    assert "target_asset: target_asset/*" in manifest
    assert "task_spec: task_spec/task_spec.json" in manifest

    output_schema = json.loads(files["contracts/output_schema.json"])
    assert output_schema["additionalProperties"] is False
    assert output_schema["properties"]["findings"]["items"]["additionalProperties"] is False


def test_upload_target_asset_is_split_into_reviewable_files() -> None:
    scenario = scenario_by_id("upload")
    files = target_asset_files(scenario)

    assert set(files) == {
        "target_asset/task_brief.md",
        "target_asset/api.yaml",
        "target_asset/app.py",
        "target_asset/config.yaml",
    }
    assert "/upload" in files["target_asset/api.yaml"]
    assert "def upload" in files["target_asset/app.py"]
    assert "audit_log_retention_days" in files["target_asset/config.yaml"]
