import json

from skill_deployment.artifacts import check_artifact_manifest


def test_artifact_manifest_accepts_existing_artifacts(tmp_path) -> None:
    (tmp_path / "summary.json").write_text("{}", encoding="utf-8")
    (tmp_path / "manifest.json").write_text(
        json.dumps({"run_id": "x", "created_at": "now", "artifacts": ["summary.json"]}),
        encoding="utf-8",
    )

    result = check_artifact_manifest(tmp_path)

    assert result.ok is True
    assert result.missing_artifacts == ()


def test_artifact_manifest_reports_missing_artifact(tmp_path) -> None:
    (tmp_path / "manifest.json").write_text(
        json.dumps({"run_id": "x", "created_at": "now", "artifacts": ["summary.json"]}),
        encoding="utf-8",
    )

    result = check_artifact_manifest(tmp_path)

    assert result.ok is False
    assert result.missing_artifacts == ("summary.json",)
