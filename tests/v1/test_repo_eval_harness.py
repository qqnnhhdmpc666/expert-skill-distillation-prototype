from __future__ import annotations

import json
from pathlib import Path

import pytest

from expert_skill_system.evaluation.repo_eval_harness import run_repo_level_eval
from expert_skill_system.runtime.release_bundle_resolver import BundleResolutionError

REGISTRY = Path("data/repo_security_tasks/registry.json")


def test_repo_eval_harness_runs_registry_with_explicit_partial_bundle(tmp_path: Path) -> None:
    output = tmp_path / "run"
    summary = run_repo_level_eval(
        task_registry=REGISTRY,
        output_dir=output,
        state_dir=tmp_path / "state",
        use_active_binding=True,
        allow_local_manifest_only=True,
    )
    assert summary["task_count"] == 3
    assert summary["pass_count"] == 3
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
    ]:
        task_dir = output / "tasks" / task_id
        assert (task_dir / "prediction.json").exists()
        assert (task_dir / "verifier_result.json").exists()
        assert (task_dir / "trajectory_evidence" / "outcome.json").exists()
        assert (task_dir / "repo_evidence.json").exists()
    aggregate = json.loads((output / "aggregate_report.json").read_text(encoding="utf-8"))
    assert aggregate["fixture_type_distribution"]["local_public_like_demo"] == 3


def test_repo_eval_harness_fails_without_real_or_partial_bundle(tmp_path: Path) -> None:
    with pytest.raises(BundleResolutionError):
        run_repo_level_eval(
            task_registry=REGISTRY,
            output_dir=tmp_path / "run",
            state_dir=tmp_path / "state",
            use_active_binding=True,
        )
