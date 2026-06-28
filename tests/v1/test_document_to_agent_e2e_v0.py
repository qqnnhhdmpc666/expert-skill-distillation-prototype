from __future__ import annotations

import json
import shutil
from pathlib import Path

from scripts.run_document_to_agent_e2e_v0 import main as run_e2e

ROOT = Path(__file__).resolve().parents[2]


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_document_to_agent_e2e_real_chain(tmp_path: Path) -> None:
    output = tmp_path / "e2e"
    reports = tmp_path / "reports"
    status = run_e2e(
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

    summary = read_json(output / "e2e_summary.json")
    request = read_json(output / "agent_backend_request.json")["request"] if "request" in read_json(output / "agent_backend_request.json") else read_json(output / "agent_backend_request.json")
    release_bundle = read_json(output / "release_bundle_manifest.json")
    separation = read_json(output / "skill_knowledge_separation_audit.json")

    assert summary["end_to_end_status"] == "pass"
    assert summary["document_ingestion_status"] == "pass"
    assert summary["bundle_build_status"] == "pass"
    assert summary["active_binding_status"] == "pass"
    assert summary["agent_execution_status"] == "pass"
    assert summary["trajectory_status"] == "pass"
    assert summary["verifier_status"] == "pass"
    assert summary["verifier_quality_status"] == "pass"
    assert summary["real_llm_agent_executed"] is False

    assert (output / "material_digest.json").exists()
    assert read_json(output / "material_windows.json")["window_count"] >= 3
    assert "Inspect dependency declarations" in (output / "extracted_skill.md").read_text(encoding="utf-8")
    assert read_json(output / "knowledge_manifest.json")["evidence_refs"]
    assert release_bundle["skill_ir_refs"]
    assert release_bundle["knowledge_projection_refs"]
    assert request["bundle_digest"].startswith("sha256:")
    assert request["bundle_path"]
    assert separation["status"] == "pass"

    assert (output / "normalized_trajectory.jsonl").exists()
    assert (output / "verifier_result.json").exists()
    assert (reports / "DOCUMENT_TO_AGENT_E2E_V0_STATUS.md").exists()


def test_document_to_agent_e2e_missing_material_fails(tmp_path: Path) -> None:
    case_copy = tmp_path / "case"
    shutil.copytree(ROOT / "data" / "e2e_cases" / "document_to_agent_v0", case_copy)
    (case_copy / "input_material.md").unlink()
    status = run_e2e(
        [
            "--case-dir",
            str(case_copy),
            "--output",
            str(tmp_path / "out"),
            "--state-dir",
            str(tmp_path / "state"),
        ]
    )
    assert status == 2
