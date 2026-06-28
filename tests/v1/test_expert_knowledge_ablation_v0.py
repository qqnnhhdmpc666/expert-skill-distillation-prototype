from __future__ import annotations

import json
from pathlib import Path

from scripts.run_expert_knowledge_ablation_v0 import CONDITIONS
from scripts.run_expert_knowledge_ablation_v0 import main as run_ablation


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_mock_ablation_outputs_all_six_conditions(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test-secret-do-not-write")
    output = tmp_path / "out"
    reports = tmp_path / "reports"
    assert run_ablation(
        [
            "--output",
            str(output),
            "--state-dir",
            str(tmp_path / "state"),
            "--reports-dir",
            str(reports),
            "--mock-api",
        ]
    ) == 0

    matrix = read_json(output / "ablation_matrix.json")["rows"]
    assert {row["condition"] for row in matrix} == set(CONDITIONS)
    assert len(matrix) == 6
    assert read_json(output / "knowledge_access" / "knowledge_access_audit.json")["knowledge_access_status"] == "pass"
    assert (output / "ablation_matrix.md").exists()
    assert (reports / "EXPERT_KNOWLEDGE_ABLATION_V0_STATUS.md").exists()
    assert read_json(output / "aggregate_summary.json")["direct_chat_fallback_counted"] is False


def test_failed_conditions_have_failure_attribution(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test-secret-do-not-write")
    output = tmp_path / "out"
    assert run_ablation(
        ["--output", str(output), "--state-dir", str(tmp_path / "state"), "--reports-dir", str(tmp_path / "reports"), "--mock-api"]
    ) == 0
    rows = read_json(output / "ablation_matrix.json")["rows"]
    failed = [row for row in rows if not row["verifier_pass"]]
    assert failed
    for row in failed:
        attribution = read_json(output / "runs" / row["condition"] / "failure_attribution.json")
        assert attribution["failure_type"] in {
            "schema_invalid",
            "missing_skill_rule",
            "missing_knowledge",
            "missing_evidence",
            "unsupported_claim",
            "output_schema_error",
            "agent_execution_failure",
            "verifier_inconclusive",
            "environment_blocked",
        }
        assert "suggested_revision_target" in attribution
