from __future__ import annotations

import json
from pathlib import Path

from scripts.run_open_world_integration_v0 import main as run_open_world


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_open_world_integration_v0_hard_gates(tmp_path: Path) -> None:
    output = tmp_path / "open_world"
    reports = tmp_path / "reports"
    status = run_open_world(["--output", str(output), "--state-dir", str(tmp_path / "state"), "--reports-dir", str(reports)])
    assert status == 0

    aggregate = read_json(output / "aggregate_summary.json")
    per_lane = read_json(output / "per_lane_summary.json")
    matrix = read_json(output / "backend_condition_lane_matrix.json")
    audit = read_json(output / "anti_leakage_audit.json")

    for key in [
        "survey_status",
        "agent_adapter_contract_status",
        "real_agent_execution_status",
        "bundle_injection_status",
        "public_eval_lane_status",
        "repo_level_lane_status",
        "swe_bench_lane_status",
        "trace_normalization_status",
        "anti_leakage_status",
        "claim_boundary_status",
        "open_world_integration_v0_status",
    ]:
        assert key in aggregate

    assert aggregate["real_agent_executed_count"] >= 1
    assert aggregate["real_agent_dry_run_count"] == 0
    assert aggregate["trace_normalization_status"] == "pass"
    assert aggregate["bundle_injection_status"] == "pass"
    assert aggregate["anti_leakage_status"] == "pass"
    assert aggregate["claim_boundary_status"] == "pass"

    assert per_lane["repo_level_dependency_use"]["repo_level_public_excerpt_count"] == 1
    assert per_lane["repo_level_dependency_use"]["repo_level_micro_lane_status"] == "partial"
    assert per_lane["repo_level_dependency_use"]["full_public_repo_level_evaluation"] == "not_claimed"
    assert per_lane["swe_bench_compatibility"]["official_harness_executed"] is False
    assert per_lane["swe_bench_compatibility"]["swe_bench_micro_lane_status"] == "harness_contract_ready"
    assert per_lane["swe_bench_compatibility"]["official_swe_bench_performance"] == "not_claimed"

    rows = matrix["rows"]
    assert len(rows) == 8
    for row in rows:
        assert row["backend"] in {"deterministic_reference", "real_agent"}
        assert row["condition"] in {"no_skill", "distillation_loop_v1_bundle"}
        assert row["lane"] in {"repo_level_dependency_use", "swe_bench_compatibility"}
        assert row["trajectory_available"] is True
        assert row["verifier_available"] is True
        if row["execution_status"] in {"dry_run", "unavailable"}:
            assert row["claim_counted"] is False
            assert row["not_counted_count"] == 1

    assert audit["anti_leakage_status"] == "pass"
    assert audit["swe_bench_gold_patch_visible_to_agent"] is False
    assert audit["dry_run_rows_counted_as_pass"] is False
    assert (reports / "OPEN_WORLD_INTEGRATION_V0_GAP_TO_MATURITY.md").exists()
    assert (reports / "PUBLIC_REPO_LEVEL_HELDOUT_SET_V0_READINESS.md").exists()
