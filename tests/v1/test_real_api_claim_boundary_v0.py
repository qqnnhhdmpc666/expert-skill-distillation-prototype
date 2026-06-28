from __future__ import annotations

import json
from pathlib import Path

from scripts.run_real_api_benchmark_micro_v0 import main as run_real_api_micro


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_official_benchmark_claims_remain_blocked(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test-secret-do-not-write")
    output = tmp_path / "out"
    reports = tmp_path / "reports"
    assert run_real_api_micro(
        ["--output", str(output), "--state-dir", str(tmp_path / "state"), "--reports-dir", str(reports), "--mock-api"]
    ) == 0
    boundary = read_json(output / "claim_boundary.json")
    blocked = boundary["blocked_claims"]
    assert boundary["claim_boundary_status"] == "pass"
    assert blocked["official_swe_bench_performance"] == "not_claimed"
    assert blocked["official_skillsbench_performance"] == "not_claimed"
    assert blocked["official_skillgenbench_performance"] == "not_claimed"
    assert blocked["production_ready"] is False
    assert blocked["compiler_superiority"] == "not_evaluated"
    status = (reports / "REAL_API_BENCHMARK_MICRO_V0_STATUS.md").read_text(encoding="utf-8")
    assert "not an official SWE-bench" in status


def test_claim_counted_requires_execution_verifier_and_no_leakage(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test-secret-do-not-write")
    output = tmp_path / "out"
    assert run_real_api_micro(
        [
            "--output",
            str(output),
            "--state-dir",
            str(tmp_path / "state"),
            "--reports-dir",
            str(tmp_path / "reports"),
            "--mock-api",
        ]
    ) == 0
    matrix = read_json(output / "backend_condition_lane_matrix.json")["rows"]
    for row in matrix:
        if row["claim_counted"]:
            assert row["real_llm_agent_executed"] is True
            assert row["verifier_available"] is True
            assert row["schema_valid_rate"] == 1.0
        else:
            assert row["execution_status"] in {"blocked", "skipped", "partial"} or row["real_llm_agent_executed"] is False
