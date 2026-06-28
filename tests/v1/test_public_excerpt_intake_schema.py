from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_public_excerpt_registry_matches_intake_schema() -> None:
    schema = read_json(ROOT / "data" / "repo_security_tasks" / "public_excerpt_intake_schema.json")
    registry = read_json(ROOT / "data" / "repo_security_tasks" / "public_heldout_v0" / "registry.json")
    required = set(schema["required_fields"])
    assert {
        "repo_url",
        "commit_hash",
        "license",
        "snapshot_digest",
        "runtime_visible_files",
        "evaluator_only_gold",
        "dependency_declaration_evidence",
        "import_use_evidence",
        "advisory_record",
        "verifier",
        "source_manifest",
    }.issubset(required)

    accepted = [item for item in registry["excerpts"] if item["accepted"]]
    assert len(accepted) == 1
    for excerpt in accepted:
        task_dir = ROOT / "data" / "repo_security_tasks" / "public_heldout_v0" / excerpt["task_dir"]
        manifest = read_json(task_dir / "source_manifest.json")
        manifest_with_ref = {**manifest, "source_manifest": str(task_dir / "source_manifest.json")}
        assert required.issubset(set(manifest_with_ref))
        assert manifest["quality_tier"] == "A"
        assert manifest["repo_url"] == excerpt["repo_url"]
        assert manifest["commit_hash"] == excerpt["commit_hash"]
        assert manifest["license"]
        assert manifest["snapshot_digest"].startswith("sha256:")
        runtime_visible = set(manifest["runtime_visible_files"])
        evaluator_only = set(manifest["evaluator_only_gold"])
        assert runtime_visible.isdisjoint(evaluator_only)


def test_same_repo_multiple_tasks_do_not_inflate_count() -> None:
    registry = read_json(ROOT / "data" / "repo_security_tasks" / "public_heldout_v0" / "registry.json")
    accepted_a = [item for item in registry["excerpts"] if item["accepted"] and item["quality_tier"] == "A"]
    distinct_repos = {item["repo_url"] for item in accepted_a}
    assert len(distinct_repos) == 1
    assert registry["counting_policy"]["same_repo_multiple_tasks_count_once"] is True
    assert registry["counting_policy"]["synthetic_or_local_public_like_fixtures_count"] is False
