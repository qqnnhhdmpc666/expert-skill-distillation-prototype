from __future__ import annotations

import json
from pathlib import Path

from expert_skill_system.evaluation.repo_evidence_collector import collect_repo_evidence, validate_repo_file_digests

TASK_DIR = Path("data/repo_security_tasks/dependency_use_triage_requests_demo")


def test_repo_evidence_collector_emits_grounded_evidence_ids() -> None:
    manifest = json.loads((TASK_DIR / "repo_snapshot_manifest.json").read_text(encoding="utf-8"))
    evidence = collect_repo_evidence(task_dir=TASK_DIR, repo_manifest=manifest, package="requests")
    evidence_types = {item["evidence_type"] for item in evidence}
    assert evidence_types >= {"dependency_declaration", "resolved_version", "import_use_site", "repo_file_digest"}
    assert all(item["evidence_id"].startswith("sha256:") for item in evidence)
    assert all("line_start" in item and "line_end" in item for item in evidence)
    assert all(item["file_digest"].startswith("sha256:") for item in evidence)


def test_repo_snapshot_manifest_file_digests_and_line_counts_match() -> None:
    manifest = json.loads((TASK_DIR / "repo_snapshot_manifest.json").read_text(encoding="utf-8"))
    checks = validate_repo_file_digests(task_dir=TASK_DIR, repo_manifest=manifest)
    assert checks
    assert all(item["digest_match"] for item in checks)
    assert all(item["line_count_match"] for item in checks)
