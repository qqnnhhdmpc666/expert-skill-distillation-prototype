from __future__ import annotations

import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

import pytest

from expert_skill_system.cli import main
from expert_skill_system.evaluation.repo_eval_harness import run_repo_level_eval
from expert_skill_system.runtime.release_bundle_resolver import BundleResolutionError

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REGISTRY = Path("data/repo_security_tasks/registry.json")
DATA_ROOT = PROJECT_ROOT / "data" / "v1_walking_skeleton"
BUNDLE_KEYS = [
    "bundle_attachment_mode",
    "bundle_digest",
    "skill_digest",
    "skill_artifact_digest",
    "knowledge_projection_digest",
    "knowledge_access_binding_digest",
]


def test_repo_eval_harness_runs_registry_with_explicit_partial_bundle(tmp_path: Path) -> None:
    output = tmp_path / "run"
    summary = run_repo_level_eval(
        task_registry=REGISTRY,
        output_dir=output,
        state_dir=tmp_path / "state",
        use_active_binding=True,
        allow_local_manifest_only=True,
    )
    assert summary["task_count"] == 4
    assert summary["pass_count"] == 4
    assert summary["bundle_attachment_mode"] == "partial_local_manifest_only"
    assert (output / "run_manifest.json").exists()
    assert (output / "bundle_resolution.json").exists()
    assert (output / "task_results.jsonl").exists()
    assert (output / "aggregate_report.json").exists()
    assert (output / "aggregate_report.md").exists()
    for task_id in [
        "dependency_use_triage_requests_demo",
        "dependency_use_triage_declared_not_used",
        "dependency_use_triage_version_not_affected",
        "dependency_use_triage_the_gan_zoo_public",
    ]:
        task_dir = output / "tasks" / task_id
        assert (task_dir / "prediction.json").exists()
        assert (task_dir / "verifier_result.json").exists()
        assert (task_dir / "trajectory_evidence" / "outcome.json").exists()
        assert (task_dir / "repo_evidence.json").exists()
    aggregate = json.loads((output / "aggregate_report.json").read_text(encoding="utf-8"))
    assert aggregate["fixture_type_distribution"]["local_public_like_demo"] == 3
    assert aggregate["fixture_type_distribution"]["public_repo_excerpt"] == 1
    assert aggregate["bundle_attachment_mode"] == "partial_local_manifest_only"
    run_manifest = json.loads((output / "run_manifest.json").read_text(encoding="utf-8"))
    public_source = next(
        item for item in run_manifest["task_sources"] if item["task_id"] == "dependency_use_triage_the_gan_zoo_public"
    )
    assert public_source["commit_digest"] == "git-sha1:375f2be4a852ead8980c06b2a996893f0cb95713"
    assert public_source["fixture_type"] == "public_repo_excerpt"
    task_result = json.loads((output / "task_results.jsonl").read_text(encoding="utf-8").splitlines()[0])
    assert task_result["bundle_attachment_mode"] == "partial_local_manifest_only"
    task_results = [
        json.loads(line) for line in (output / "task_results.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    public_result = next(row for row in task_results if row["task_id"] == "dependency_use_triage_the_gan_zoo_public")
    assert public_result["source_url"] == "https://github.com/hindupuravinash/the-gan-zoo"
    public_provenance = json.loads(
        (
            output
            / "tasks"
            / "dependency_use_triage_the_gan_zoo_public"
            / "trajectory_evidence"
            / "provenance.json"
        ).read_text(encoding="utf-8")
    )
    assert public_provenance["fixture_type"] == "public_repo_excerpt"
    assert public_provenance["repo_snapshot_content_digest"] == (
        "sha256:4fa32e652b51130309c78b9d4f52a3020bd5930b289a015e5dc6626c90286ccb"
    )
    task_dir = output / "tasks" / "dependency_use_triage_requests_demo"
    assert json.loads((task_dir / "bundle_manifest.json").read_text(encoding="utf-8"))[
        "bundle_attachment_mode"
    ] == "partial_local_manifest_only"
    assert json.loads((task_dir / "trajectory_evidence" / "bundle_manifest.json").read_text(encoding="utf-8"))[
        "bundle_attachment_mode"
    ] == "partial_local_manifest_only"
    assert json.loads((task_dir / "trajectory_evidence" / "provenance.json").read_text(encoding="utf-8"))[
        "bundle_attachment_mode"
    ] == "partial_local_manifest_only"


def test_repo_eval_harness_propagates_real_bundle_provenance(tmp_path: Path) -> None:
    state = _build_active_bundle_state(tmp_path)
    output = tmp_path / "run"
    summary = run_repo_level_eval(
        task_registry=REGISTRY,
        output_dir=output,
        state_dir=state,
        use_active_binding=True,
    )
    assert summary["task_count"] == 4
    assert summary["pass_count"] == 4
    assert summary["bundle_attachment_mode"] == "real_release_bundle_pinned"

    bundle_resolution = json.loads((output / "bundle_resolution.json").read_text(encoding="utf-8"))
    expected = {key: bundle_resolution[key] for key in BUNDLE_KEYS}
    assert expected["bundle_attachment_mode"] == "real_release_bundle_pinned"
    assert all(expected[key] and str(expected[key]).startswith("sha256:") for key in BUNDLE_KEYS if key != "bundle_attachment_mode")

    for path in [
        output / "run_manifest.json",
        output / "run_summary.json",
        output / "run_provenance.json",
        output / "aggregate_report.json",
    ]:
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert {key: payload[key] for key in BUNDLE_KEYS} == expected

    for line in (output / "task_results.jsonl").read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        assert {key: row[key] for key in BUNDLE_KEYS} == expected

    for task_id in [
        "dependency_use_triage_requests_demo",
        "dependency_use_triage_declared_not_used",
        "dependency_use_triage_version_not_affected",
        "dependency_use_triage_the_gan_zoo_public",
    ]:
        task_dir = output / "tasks" / task_id
        for relative in [
            "bundle_manifest.json",
            "condition_manifest.json",
            "trajectory_evidence/bundle_manifest.json",
            "trajectory_evidence/provenance.json",
        ]:
            payload = json.loads((task_dir / relative).read_text(encoding="utf-8"))
            assert {key: payload[key] for key in BUNDLE_KEYS} == expected


def test_repo_eval_harness_fails_without_real_or_partial_bundle(tmp_path: Path) -> None:
    with pytest.raises(BundleResolutionError):
        run_repo_level_eval(
            task_registry=REGISTRY,
            output_dir=tmp_path / "run",
            state_dir=tmp_path / "state",
            use_active_binding=True,
        )


def _build_active_bundle_state(tmp_path: Path) -> Path:
    state = tmp_path / ".eskill"
    with redirect_stdout(StringIO()):
        assert main(["--state-dir", str(state), "demo", "--data-dir", str(DATA_ROOT)]) == 0
    return state
