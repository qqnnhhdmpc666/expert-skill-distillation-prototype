from __future__ import annotations

import json
from pathlib import Path

from scripts.run_real_expert_material_pilot import BASELINES
from scripts.run_real_expert_material_pilot import main as run_real_expert_material_pilot

CASE_ROOT = Path("data/real_expert_material_pilot/repo_dependency_use_triage_v1")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_real_expert_material_pilot_minimal_slice(tmp_path: Path) -> None:
    output = tmp_path / "outputs" / "real_expert_material_pilot" / "repo_dependency_use_triage_v1"
    state_dir = tmp_path / "state"
    reports_dir = tmp_path / "reports"
    status = run_real_expert_material_pilot(
        [
            "--case-root",
            str(CASE_ROOT),
            "--output",
            str(output),
            "--state-dir",
            str(state_dir),
            "--reports-dir",
            str(reports_dir),
        ]
    )
    assert status == 0

    aggregate = read_json(output / "aggregate_summary.json")
    per_lane = read_json(output / "per_lane_summary.json")
    comparison = read_json(output / "baseline_comparison.json")

    assert aggregate["pilot_protocol_status"] == "pass"
    assert aggregate["osv_lane_status"] == "pass"
    assert aggregate["repo_level_lane_status"] == "partial"
    assert aggregate["repo_level_public_excerpt_count"] == 1
    assert aggregate["full_public_repo_level_evaluation"] == "not_claimed"
    assert aggregate["anti_leakage_status"] == "pass"
    assert aggregate["claim_boundary_status"] == "pass"
    assert aggregate["no_skill_reference_backend_contains_default_triage_logic"] is True
    assert aggregate["heldout_feedback_used_for_revision"] is False
    assert aggregate["same_task_split"] is True
    assert aggregate["same_allowed_knowledge_snapshot"] is True
    assert aggregate["same_runtime_backend"] is True
    assert aggregate["same_budget"] is True

    assert set(per_lane) >= {"osv_advisory_version", "repo_level_dependency_use"}
    assert per_lane["osv_advisory_version"]["case_count"] == 7
    assert per_lane["repo_level_dependency_use"]["full_public_repo_level_evaluation"] == "not_claimed"

    assert comparison["baseline_comparison_status"] == "pass"
    assert comparison["four_baseline_comparison"] == "pass"
    assert comparison["heldout_feedback_used_for_revision"] is False
    for baseline in BASELINES:
        assert comparison["baseline_validity"][baseline]["status"] == "valid"

    status_report = (reports_dir / "REAL_EXPERT_MATERIAL_PILOT_STATUS.md").read_text(encoding="utf-8")
    assert "repo_level_lane_status: `partial`" in status_report
    assert "compiler_superiority: `not_evaluated`" in status_report


def test_baseline_access_manifests_and_anti_leakage(tmp_path: Path) -> None:
    output = tmp_path / "outputs"
    reports_dir = tmp_path / "reports"
    status = run_real_expert_material_pilot(
        [
            "--case-root",
            str(CASE_ROOT),
            "--output",
            str(output),
            "--state-dir",
            str(tmp_path / "state"),
            "--reports-dir",
            str(reports_dir),
        ]
    )
    assert status == 0

    for baseline in BASELINES:
        baseline_dir = output / "baselines" / baseline
        access = read_json(baseline_dir / "input_access_manifest.json")
        forbidden = read_json(baseline_dir / "forbidden_access_check.json")
        assert forbidden["status"] == "pass"
        assert forbidden["heldout_gold_read"] is False
        assert forbidden["v1_revision_artifacts_read"] is False
        assert forbidden["distillation_intermediate_outputs_read"] is False
        assert forbidden["other_baseline_outputs_read"] is False
        assert "data/public_osv_pilot/gold.jsonl" in access["forbidden_inputs"]
        assert access["shared_invariants"]["heldout_feedback_used_for_revision"] is False

    no_skill = read_json(output / "baselines" / "no_skill" / "input_access_manifest.json")
    assert "data/repo_level_bundle/expert_material.md" not in no_skill["allowed_inputs"]
    assert no_skill["expert_material_access"] == "forbidden"
    assert no_skill["distillation_generated_knowledge_artifacts"] == []

    direct = read_json(output / "baselines" / "direct_to_skill_ir" / "input_access_manifest.json")
    assert direct["expert_material_access"] == "one_stage_source_material_to_skill_ir"
    assert direct["shared_allowed_knowledge_snapshot"]
    assert direct["distillation_generated_knowledge_artifacts"] == []
    direct_skill = read_json(output / "baselines" / "direct_to_skill_ir" / "direct_skill_ir.json")
    assert direct_skill["generation_mode"] == "one_stage_source_material_to_skill_ir"
    assert "heldout_gold" in direct_skill["forbidden_inputs"]

    full_material = read_json(output / "baselines" / "full_material" / "input_access_manifest.json")
    assert "data/repo_level_bundle/expert_material.md" in full_material["allowed_inputs"]
    assert full_material["expert_material_access"] == "complete_source_visible_material"

    audit = read_json(output / "anti_leakage_audit.json")
    assert audit["anti_leakage_status"] == "pass"
    assert audit["prediction_logic_scan"]["disallowed_prediction_branches"] == []
