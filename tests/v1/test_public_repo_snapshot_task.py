from __future__ import annotations

import hashlib
import json
from pathlib import Path

from expert_skill_system.evaluation.repo_evidence_collector import validate_repo_file_digests
from expert_skill_system.evaluation.repo_security_task import (
    load_repo_security_task,
    load_runtime_task_view,
    run_dependency_use_triage,
)
from expert_skill_system.evaluation.repo_security_verifier import verify_dependency_use_prediction

TASK_DIR = Path("data/repo_security_tasks/dependency_use_triage_the_gan_zoo_public")


def test_public_repo_excerpt_has_immutable_traceable_provenance() -> None:
    task = load_repo_security_task(TASK_DIR)
    manifest = json.loads((TASK_DIR / "repo_snapshot_manifest.json").read_text(encoding="utf-8"))

    assert task["public_source"]["fixture_type"] == "public_repo_excerpt"
    assert task["commit_digest"] == "git-sha1:375f2be4a852ead8980c06b2a996893f0cb95713"
    assert manifest["source_tree_digest"] == "git-sha1:1d14483f75314b681832854d7d766db179d6b788"
    assert manifest["license"] == "MIT"

    checks = validate_repo_file_digests(task_dir=TASK_DIR, repo_manifest=manifest)
    assert checks
    assert all(item["digest_match"] and item["line_count_match"] for item in checks)

    for item in manifest["files"]:
        content = (TASK_DIR / "repo_snapshot" / item["path"]).read_bytes()
        git_blob = hashlib.sha1(f"blob {len(content)}\0".encode() + content).hexdigest()  # noqa: S324
        assert git_blob == item["upstream_git_blob"]
        assert item["source_url"].startswith(
            "https://github.com/hindupuravinash/the-gan-zoo/blob/375f2be4a852ead8980c06b2a996893f0cb95713/"
        )


def test_public_repo_excerpt_runtime_view_excludes_hidden_gold() -> None:
    view = load_runtime_task_view(TASK_DIR)
    rendered = json.dumps(view, sort_keys=True)
    assert "hidden_gold" not in rendered
    assert "verifier_expected_answer" not in rendered
    assert "375f2be4a852ead8980c06b2a996893f0cb95713" in rendered


def test_public_repo_excerpt_runs_with_repo_and_advisory_evidence(tmp_path: Path) -> None:
    result = run_dependency_use_triage(TASK_DIR, tmp_path / "public-task")
    prediction = json.loads(Path(result["prediction_path"]).read_text(encoding="utf-8"))
    verifier = json.loads(Path(result["verifier_result_path"]).read_text(encoding="utf-8"))

    assert result["verifier_pass"] is True
    assert prediction["decision"] == "dependency_used_and_affected"
    assert prediction["declared_version"] == "2.19.1"
    assert {item["evidence_type"] for item in prediction["evidence"]} >= {
        "dependency_declaration",
        "resolved_version",
        "import_use_site",
        "advisory_affected_range",
        "decision_evidence",
    }
    assert all(check["passed"] for check in verifier["checks"])
    provenance = json.loads(
        (tmp_path / "public-task" / "trajectory_evidence" / "provenance.json").read_text(encoding="utf-8")
    )
    assert provenance["fixture_type"] == "public_repo_excerpt"
    assert provenance["commit_digest"] == "git-sha1:375f2be4a852ead8980c06b2a996893f0cb95713"
    assert provenance["repo_snapshot_content_digest"] == (
        "sha256:4fa32e652b51130309c78b9d4f52a3020bd5930b289a015e5dc6626c90286ccb"
    )
    assert provenance["repo_snapshot_manifest_digest"].startswith("sha256:")


def test_public_repo_excerpt_rejects_advisory_only_prediction(tmp_path: Path) -> None:
    task = load_repo_security_task(TASK_DIR)
    result = run_dependency_use_triage(TASK_DIR, tmp_path / "valid")
    prediction = json.loads(Path(result["prediction_path"]).read_text(encoding="utf-8"))
    prediction["evidence"] = [
        item
        for item in prediction["evidence"]
        if item["evidence_type"] in {"advisory_affected_range", "decision_evidence"}
    ]

    verifier = verify_dependency_use_prediction(task, prediction, task_dir=TASK_DIR)
    assert verifier["verifier_pass"] is False
    assert verifier["failure_category"] == "evidence_error"
