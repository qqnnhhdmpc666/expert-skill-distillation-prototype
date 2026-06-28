from __future__ import annotations

import json
from pathlib import Path

from scripts.run_document_to_agent_e2e_v0 import main as run_e2e

ROOT = Path(__file__).resolve().parents[2]


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_verifier_spec_and_quality_gate(tmp_path: Path) -> None:
    output = tmp_path / "e2e"
    assert run_e2e(["--output", str(output), "--state-dir", str(tmp_path / "state")]) == 0

    spec = read_json(ROOT / "data" / "e2e_cases" / "document_to_agent_v0" / "verifier_spec.json")
    trace = read_json(output / "verifier_trace.json")
    audit = read_json(output / "verifier_quality_audit.json")
    result = read_json(output / "verifier_result.json")
    taxonomy = read_json(output / "verifier_failure_taxonomy.json")
    summary = read_json(output / "e2e_summary.json")

    assert spec["verifier_type"] == "schema_plus_evidence_plus_domain"
    assert spec["claim_level"] == "development_domain_verifier"
    assert spec["runtime_visible_gold"] is False
    assert {"schema_check", "evidence_check", "domain_check", "gold_access_check"}.issubset(trace)
    assert audit["verifier_quality_status"] == "pass"
    assert summary["end_to_end_status"] == "pass"
    assert summary["verifier_quality_status"] == "pass"
    assert result["failure_type"] is None
    assert result["failure_taxonomy_version"] == "0.1"
    assert result["claim_level"] == "development_domain_verifier"
    assert result["can_drive_revision"] is True
    assert result["can_claim_public_benchmark_performance"] is False
    required_types = {
        "schema_invalid",
        "missing_required_evidence",
        "forbidden_evidence_access",
        "domain_rule_violation",
        "knowledge_missing",
        "skill_rule_missing",
        "agent_execution_failure",
        "environment_blocked",
        "verifier_inconclusive",
    }
    assert required_types.issubset(set(taxonomy["types"]))
