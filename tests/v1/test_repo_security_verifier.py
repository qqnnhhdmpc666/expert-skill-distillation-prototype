from __future__ import annotations

import json
from pathlib import Path

from expert_skill_system.evaluation.repo_security_task import load_repo_security_task, run_dependency_use_triage
from expert_skill_system.evaluation.repo_security_verifier import verify_dependency_use_prediction

TASK_DIR = Path("data/repo_security_tasks/dependency_use_triage_requests_demo")


def test_repo_security_vertical_slice_generates_prediction_and_passes_verifier(tmp_path: Path) -> None:
    result = run_dependency_use_triage(TASK_DIR, tmp_path / "run")
    assert result["verifier_pass"] is True
    prediction_path = Path(result["prediction_path"])
    prediction = json.loads(prediction_path.read_text(encoding="utf-8"))
    assert prediction["decision"] == "dependency_used_and_affected"
    assert {item["evidence_type"] for item in prediction["evidence"]} >= {
        "dependency_declaration",
        "resolved_version",
        "import_or_use_site",
        "advisory_affected_range",
        "decision_evidence",
    }
    assert (tmp_path / "run" / "trajectory_evidence" / "outcome.json").exists()


def test_repo_security_verifier_rejects_missing_use_site_evidence() -> None:
    task = load_repo_security_task(TASK_DIR)
    bad_prediction = {
        "schema_version": "repo_security_prediction.v1",
        "task_id": task["task_id"],
        "task_type": "dependency_use_triage",
        "decision": "dependency_used_and_affected",
        "package": "requests",
        "declared_version": "2.19.1",
        "advisory_id": "PYSEC-2018-28",
        "evidence": [
            {"evidence_type": "dependency_declaration", "path": "requirements.txt", "line": 1, "excerpt": "requests==2.19.1"},
            {"evidence_type": "resolved_version", "path": "requirements.txt", "line": 1, "excerpt": "requests==2.19.1"},
            {"evidence_type": "advisory_affected_range", "path": "allowed_knowledge.json", "line": None, "excerpt": "fixed 2.20.0"},
            {"evidence_type": "decision_evidence", "path": "derived", "line": None, "excerpt": "decision"},
        ],
        "reason_codes": ["VERSION_IN_AFFECTED_RANGE"],
    }
    result = verify_dependency_use_prediction(task, bad_prediction)
    assert result["verifier_pass"] is False
    assert result["failure_category"] == "evidence_error"
