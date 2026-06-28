from __future__ import annotations

import json
from pathlib import Path

from scripts.run_system_readiness_audit_v0 import main as run_audit


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_system_readiness_audit_writes_split_gates(tmp_path: Path) -> None:
    output = tmp_path / "audit"
    reports = tmp_path / "reports"
    assert run_audit(["--output", str(output), "--reports-dir", str(reports)]) == 0

    summary = read_json(output / "system_readiness_summary.json")
    environment = read_json(output / "environment_gate.json")
    public_data = read_json(output / "public_data_gate.json")

    for key in [
        "environment_gate_status",
        "agent_backend_gate_status",
        "benchmark_harness_gate_status",
        "public_data_gate_status",
        "end_to_end_demo_gate_status",
        "claim_gate_status",
    ]:
        assert key in summary

    assert "docker_cli_found_in_path" in environment
    assert "docker_cli_found_outside_path" in environment
    assert "docker_daemon_available" in environment
    assert "docker_desktop_installed" in environment
    assert "wsl_available" in environment
    assert "mini_swe_agent_importable" in environment
    assert public_data["distinct_public_repo_count"] == 1
    assert public_data["clean_public_excerpt_count"] == 1
    assert public_data["repo_level_heldout_set_status"] == "partial"
    assert (reports / "SYSTEM_READINESS_AUDIT_V0.md").exists()
