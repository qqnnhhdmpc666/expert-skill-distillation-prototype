from __future__ import annotations

import json
from pathlib import Path

from scripts.run_distillation_loop_v1 import main as run_distillation_loop_v1

CASE_ROOT = Path("data/distillation_cases/repo_dependency_use_triage_v1")


def test_distillation_feedback_loop_v1_runs_all_defects(tmp_path: Path) -> None:
    output_dir = tmp_path / "v1-output"
    status = run_distillation_loop_v1(
        [
            "--case-root",
            str(CASE_ROOT),
            "--state-dir",
            str(tmp_path / "v1-state"),
            "--output",
            str(output_dir),
        ]
    )

    assert status == 0
    aggregate = _read_json(output_dir / "v1_aggregate_report.json")
    assert aggregate["distillation_feedback_loop_v1"] == "pass"
    assert aggregate["defect_count"] == 4
    assert aggregate["promoted_count"] == 4
    assert set(aggregate["failure_attribution_types"]) == {
        "evidence_binding_gap",
        "knowledge_gap",
        "skill_missing_rule",
        "skill_overgeneralized_rule",
    }
    for row in aggregate["case_results"]:
        assert row["digest_changed"] is True
        assert row["revised_pass_count"] == 4
        assert row["promotion_decision"] == "promote"
        assert row["expected_attribution_matched"] is True
        assert row["seeded_counterexample_pass"] is True


def test_distillation_feedback_loop_v1_records_expected_baseline_behaviors(tmp_path: Path) -> None:
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

    assert _prediction(output_dir, "D1_skill_missing_rule", "baseline_run", "dependency_use_triage_declared_not_used")[
        "decision"
    ] == "dependency_used_and_affected"
    assert _prediction(output_dir, "D2_skill_overgeneralized_rule", "baseline_run", "dependency_use_triage_version_not_affected")[
        "decision"
    ] == "dependency_used_and_affected"
    assert _prediction(output_dir, "D3_knowledge_gap", "baseline_run", "dependency_use_triage_requests_demo")[
        "decision"
    ] == "unresolved"
    assert _prediction(output_dir, "D4_evidence_binding_gap", "baseline_run", "dependency_use_triage_requests_demo")[
        "decision"
    ] == "dependency_present_not_used"

    assert _prediction(output_dir, "D2_skill_overgeneralized_rule", "revised_run", "dependency_use_triage_version_not_affected")[
        "decision"
    ] == "dependency_used_not_affected"
    assert _prediction(output_dir, "D3_knowledge_gap", "revised_run", "dependency_use_triage_requests_demo")[
        "decision"
    ] == "dependency_used_and_affected"
    assert _prediction(output_dir, "D4_evidence_binding_gap", "revised_run", "dependency_use_triage_requests_demo")[
        "decision"
    ] == "dependency_used_and_affected"


def _prediction(output_dir: Path, defect_id: str, run_id: str, task_id: str) -> dict:
    return _read_json(output_dir / "cases" / defect_id / run_id / "tasks" / task_id / "prediction.json")


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
