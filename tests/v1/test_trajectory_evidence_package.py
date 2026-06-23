from __future__ import annotations

import json
from pathlib import Path

from expert_skill_system.runtime.skill_knowledge_injection import build_injection_manifests
from expert_skill_system.runtime.trajectory_evidence import write_trajectory_evidence_package

TASK_DIR = Path("data/repo_security_tasks/dependency_use_triage_requests_demo")


def test_trajectory_evidence_package_writes_required_files(tmp_path: Path) -> None:
    injection = build_injection_manifests(task_dir=TASK_DIR, condition_id="C5_active_runtime", output_dir=tmp_path / "injection")
    prediction = {
        "schema_version": "repo_security_prediction.v1",
        "task_id": "dependency_use_triage_requests_demo",
        "evidence": [{"evidence_type": "decision_evidence", "path": "derived", "excerpt": "ok"}],
    }
    verifier_result = {"schema_version": "repo_security_verifier_result.v1", "verifier_pass": True, "failure_category": None}
    result = write_trajectory_evidence_package(
        output_dir=tmp_path,
        task_manifest={"task_id": "dependency_use_triage_requests_demo"},
        injection_manifests=injection,
        prediction=prediction,
        verifier_result=verifier_result,
        action_trace=[{"action": "emit_prediction"}],
        observation_trace=[{"path": "requirements.txt"}],
        knowledge_query_trace=[{"query_type": "advisory_by_package"}],
    )
    package_dir = Path(result["package_dir"])
    for name in [
        "task_manifest.json",
        "condition_manifest.json",
        "skill_manifest.json",
        "knowledge_manifest.json",
        "bundle_manifest.json",
        "environment_manifest.json",
        "action_trace.jsonl",
        "observation_trace.jsonl",
        "knowledge_query_trace.jsonl",
        "verifier_result.json",
        "outcome.json",
        "cost.json",
        "provenance.json",
    ]:
        assert (package_dir / name).exists()
    outcome = json.loads((package_dir / "outcome.json").read_text(encoding="utf-8"))
    assert outcome["skill_used"] is True
    assert outcome["knowledge_used"] is True
    assert outcome["verifier_pass"] is True
