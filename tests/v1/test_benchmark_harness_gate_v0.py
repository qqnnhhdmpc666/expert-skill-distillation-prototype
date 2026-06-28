from __future__ import annotations

import json
from pathlib import Path

from scripts.run_system_readiness_audit_v0 import main as run_audit


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_benchmark_harness_gate_blocks_official_claim_without_execution(tmp_path: Path) -> None:
    output = tmp_path / "audit"
    assert run_audit(["--output", str(output), "--reports-dir", str(tmp_path / "reports")]) == 0
    gate = read_json(output / "benchmark_harness_gate.json")
    assert gate["swe_bench_official_protocol_executed"] is False
    assert gate["swe_bench_official_score_available"] is False
    assert gate["benchmark_harness_gate_status"] in {
        "blocked_by_environment",
        "contract_ready",
        "harness_importable",
        "harness_command_available",
        "docker_ready",
    }
    if not gate["swe_bench_official_protocol_executed"]:
        assert gate["swe_bench_official_score_available"] is False
