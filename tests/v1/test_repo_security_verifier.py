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
        "import_use_site",
        "advisory_affected_range",
        "decision_evidence",
    }
    assert "hidden_gold" not in json.dumps(prediction)
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
            _repo_evidence("dependency_declaration", "requirements.txt", 1, "requests==2.19.1"),
            _repo_evidence("resolved_version", "requirements.txt", 1, "requests==2.19.1"),
            _advisory_evidence(),
            _decision_evidence(),
        ],
        "reason_codes": ["VERSION_IN_AFFECTED_RANGE"],
    }
    result = verify_dependency_use_prediction(task, bad_prediction, task_dir=TASK_DIR)
    assert result["verifier_pass"] is False
    assert result["failure_category"] == "evidence_error"


def test_repo_security_boundary_tasks_run_successfully(tmp_path: Path) -> None:
    cases = {
        "dependency_use_triage_declared_not_used": "dependency_present_not_used",
        "dependency_use_triage_version_not_affected": "dependency_used_not_affected",
    }
    for case_id, decision in cases.items():
        task_dir = Path("data/repo_security_tasks") / case_id
        result = run_dependency_use_triage(task_dir, tmp_path / case_id)
        prediction = json.loads(Path(result["prediction_path"]).read_text(encoding="utf-8"))
        assert result["verifier_pass"] is True
        assert prediction["decision"] == decision


def test_repo_security_verifier_rejects_nonexistent_file_or_line() -> None:
    task = load_repo_security_task(TASK_DIR)
    prediction = _valid_prediction()
    prediction["evidence"][0]["path"] = "missing.py"
    result = verify_dependency_use_prediction(task, prediction, task_dir=TASK_DIR)
    assert result["verifier_pass"] is False
    assert result["failure_category"] == "evidence_error"


def test_repo_security_verifier_rejects_hidden_gold_leakage() -> None:
    task = load_repo_security_task(TASK_DIR)
    prediction = _valid_prediction()
    prediction["hidden_gold"] = {"decision": "dependency_used_and_affected"}
    result = verify_dependency_use_prediction(task, prediction, task_dir=TASK_DIR)
    assert result["verifier_pass"] is False
    assert result["failure_category"] == "oracle_leakage"


def test_repo_security_verifier_rejects_advisory_only_prediction() -> None:
    task = load_repo_security_task(TASK_DIR)
    prediction = _valid_prediction()
    prediction["evidence"] = [_advisory_evidence(), _decision_evidence()]
    result = verify_dependency_use_prediction(task, prediction, task_dir=TASK_DIR)
    assert result["verifier_pass"] is False
    assert result["failure_category"] == "evidence_error"


def test_repo_security_verifier_rejects_wrong_reason_code() -> None:
    task = load_repo_security_task(TASK_DIR)
    prediction = _valid_prediction()
    prediction["reason_codes"] = ["VERSION_OUT_OF_RANGE", "IMPORT_USE_SITE_FOUND"]
    result = verify_dependency_use_prediction(task, prediction, task_dir=TASK_DIR)
    assert result["verifier_pass"] is False
    assert result["failure_category"] == "reason_code_error"


def _valid_prediction() -> dict:
    result = run_dependency_use_triage(TASK_DIR, Path("outputs/test_tmp/repo_security_valid_prediction"))
    return json.loads(Path(result["prediction_path"]).read_text(encoding="utf-8"))


def _repo_evidence(evidence_type: str, path: str, line: int, excerpt: str) -> dict:
    file_path = TASK_DIR / "repo_snapshot" / path
    import hashlib

    digest = "sha256:" + hashlib.sha256(file_path.read_bytes()).hexdigest()
    return {
        "evidence_id": f"test:{evidence_type}:{path}:{line}",
        "evidence_type": evidence_type,
        "path": path,
        "line_start": line,
        "line_end": line,
        "excerpt": excerpt,
        "file_digest": digest,
    }


def _advisory_evidence() -> dict:
    return {
        "evidence_id": "test:advisory",
        "evidence_type": "advisory_affected_range",
        "path": "allowed_knowledge.json",
        "line_start": None,
        "line_end": None,
        "excerpt": "fixed 2.20.0",
        "file_digest": None,
        "source_id": "PYSEC-2018-28",
    }


def _decision_evidence() -> dict:
    return {
        "evidence_id": "test:decision",
        "evidence_type": "decision_evidence",
        "path": "derived",
        "line_start": None,
        "line_end": None,
        "excerpt": "decision",
        "file_digest": None,
    }
