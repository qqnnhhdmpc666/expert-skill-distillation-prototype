from __future__ import annotations

import json
from pathlib import Path

from scripts.run_system_readiness_audit_v0 import main as run_audit


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_claim_gate_blocks_mature_and_production_claims(tmp_path: Path) -> None:
    output = tmp_path / "audit"
    reports = tmp_path / "reports"
    assert run_audit(["--output", str(output), "--reports-dir", str(reports)]) == 0
    claim_gate = read_json(output / "claim_gate.json")
    states = claim_gate["claim_states"]
    assert states["mature_system_complete"] is False
    assert states["production_ready"] is False
    assert states["swe_bench_official_harness_executed"] is False
    assert states["real_llm_agent_effectiveness_evaluated"] is False
    assert states["public_heldout_validation_complete"] is False
    notes = (reports / "CLAIM_DOWNGRADE_NOTES.md").read_text(encoding="utf-8")
    assert "development/domain verifier" in notes
    assert "does not replace public benchmark harnesses" in notes
