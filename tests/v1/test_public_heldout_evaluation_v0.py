from __future__ import annotations

import json
from pathlib import Path

from scripts.run_public_heldout_evaluation_v0 import main as run_public_heldout


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_public_heldout_evaluation_v0_outputs_and_status(tmp_path: Path) -> None:
    output = tmp_path / "public_heldout"
    reports = tmp_path / "reports"
    status = run_public_heldout(
        [
            "--output",
            str(output),
            "--state-dir",
            str(tmp_path / "state"),
            "--reports-dir",
            str(reports),
        ]
    )
    assert status == 0

    aggregate = read_json(output / "aggregate_summary.json")
    per_lane = read_json(output / "per_lane_summary.json")
    matrix = read_json(output / "backend_condition_lane_effect_matrix.json")
    search_log = read_json(output / "public_excerpt_candidate_search_log.json")
    audit = read_json(output / "anti_leakage_audit.json")
    claim_boundary = read_json(output / "claim_boundary.json")
    swe_manifest = read_json(output / "swe_bench_micro_lane_manifest.json")

    assert search_log["screened_candidate_count"] <= 12
    accepted_a = [item for item in search_log["candidates"] if item["accepted"] and item["quality_tier"] == "A"]
    assert aggregate["accepted_candidate_count"] == 1
    assert aggregate["excluded_candidate_count"] == 11
    assert aggregate["clean_public_excerpt_count"] == len({item["repo_url"] for item in accepted_a})
    assert aggregate["distinct_public_repo_count"] == 1

    assert aggregate["repo_level_heldout_set_status"] == "partial"
    assert aggregate["public_heldout_evaluation_v0_status"] == "partial"
    assert aggregate["anti_leakage_status"] == "pass"
    assert aggregate["claim_boundary_status"] == "pass"

    repo_lane = per_lane["repo_level_dependency_use"]
    assert repo_lane["repo_level_public_excerpt_count"] == 1
    assert repo_lane["repo_level_heldout_set_status"] == "partial"
    assert repo_lane["target_clean_distinct_repos"] == 3

    assert swe_manifest["official_harness_executed"] is False
    assert swe_manifest["official_swe_bench_performance"] == "not_claimed"
    assert swe_manifest["public_benchmark_execution"] == "not_pass"
    assert swe_manifest["gold_patch_visible_to_agent"] is False
    assert swe_manifest["test_patch_visible_to_agent"] is False

    rows = matrix["rows"]
    assert len(rows) == 8
    assert {
        (row["lane"], row["backend"], row["condition"])
        for row in rows
    } == {
        (lane, backend, condition)
        for lane in {"repo_level_dependency_use", "swe_bench_micro"}
        for backend in {"deterministic_reference", "mini_swe_agent"}
        for condition in {"no_skill", "distillation_loop_v1_bundle"}
    }
    for row in rows:
        assert row["trajectory_available"] is True
        assert row["verifier_available"] is True
        if row["execution_status"] in {"dry_run", "unavailable", "blocked"}:
            assert row["claim_counted"] is False
            assert row["pass_count"] == 0
        if row["backend"] == "mini_swe_agent":
            assert row["claim_counted"] is False

    assert audit["anti_leakage_status"] == "pass"
    assert audit["runtime_visible_evaluator_gold_violations"] == []
    assert audit["heldout_feedback_used_for_revision"] is False
    assert audit["prediction_logic_scan"]["status"] == "pass"
    assert claim_boundary["compiler_superiority"] == "not_evaluated"
    assert claim_boundary["official_swe_bench_performance"] == "not_claimed"
    assert claim_boundary["production_readiness"] == "not_claimed"

    effect_report = (reports / "PUBLIC_HELDOUT_EVALUATION_V0_EFFECT_INTERPRETATION.md").read_text(encoding="utf-8")
    assert "effect_observed" in effect_report
    assert "mini_swe_agent_produced_schema_valid_verifier_artifacts" in effect_report
    assert "official harness performance is not claimed" in effect_report
    assert "## Next-Step Bridge" in effect_report


def test_public_heldout_required_artifacts_exist(tmp_path: Path) -> None:
    output = tmp_path / "public_heldout"
    reports = tmp_path / "reports"
    assert run_public_heldout(["--output", str(output), "--state-dir", str(tmp_path / "state"), "--reports-dir", str(reports)]) == 0

    required_outputs = [
        "aggregate_summary.json",
        "per_lane_summary.json",
        "backend_condition_lane_effect_matrix.json",
        "backend_condition_lane_effect_matrix.md",
        "repo_level_heldout_manifest.json",
        "swe_bench_micro_lane_manifest.json",
        "anti_leakage_audit.json",
        "claim_boundary.json",
        "public_excerpt_candidate_search_log.json",
        "public_excerpt_candidate_search_log.md",
    ]
    for rel_path in required_outputs:
        assert (output / rel_path).exists()

    for rel_path in [
        "PUBLIC_HELDOUT_EVALUATION_V0_STATUS.md",
        "PUBLIC_HELDOUT_EVALUATION_V0_ANTI_LEAKAGE_AUDIT.md",
        "PUBLIC_HELDOUT_EVALUATION_V0_EFFECT_INTERPRETATION.md",
    ]:
        assert (reports / rel_path).exists()
