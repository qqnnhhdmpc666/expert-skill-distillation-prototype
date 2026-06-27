from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path

from expert_skill_system.lifecycle import load_skill_family_registry, run_skill_family_lifecycle

REGISTRY = Path("data/skill_families/registry.json")


def test_skill_family_registry_parses_family_specs() -> None:
    registry = load_skill_family_registry(REGISTRY)

    families = {spec.skill_family: spec for spec in registry.families}
    assert set(families) == {"python-advisory", "repo-dependency-use-triage"}
    assert families["python-advisory"].binding_key == "python-advisory"
    assert families["repo-dependency-use-triage"].binding_key == "repo-dependency-use-triage"
    assert "compiler_superiority" in registry.global_blocked_claims


def test_multi_skill_family_lifecycle_builds_separate_bundles_and_boundaries(tmp_path: Path) -> None:
    short_root = Path(".tmp") / f"sfl-{uuid.uuid4().hex[:8]}"
    if short_root.exists():
        shutil.rmtree(short_root)
    registry_path = _registry_with_temp_state(short_root)
    output_dir = short_root / "l"

    result = run_skill_family_lifecycle(
        family_registry=registry_path,
        families=["python-advisory", "repo-dependency-use-triage"],
        output_dir=output_dir,
    )

    assert result["multi_skill_family_lifecycle"] == "pass"
    assert result["repo_level_eval"] == "pass"
    family_builds = _read_json(output_dir / "family_builds.json")["families"]
    by_family = {row["skill_family"]: row for row in family_builds}
    assert by_family["python-advisory"]["build_status"] == "pass"
    assert by_family["repo-dependency-use-triage"]["build_status"] == "pass"
    assert by_family["python-advisory"]["bundle_digest"] != by_family["repo-dependency-use-triage"]["bundle_digest"]
    assert by_family["python-advisory"]["binding_key"] == "python-advisory"
    assert by_family["repo-dependency-use-triage"]["binding_key"] == "repo-dependency-use-triage"
    assert by_family["python-advisory"]["bundle_manifest_skill_family"] != "repo-dependency-use-triage"
    assert {
        "dependency_declaration",
        "resolved_version",
        "import_use_site",
        "advisory_affected_range",
        "decision_evidence",
    }.issubset(set(by_family["repo-dependency-use-triage"]["evidence_requirements"]))

    eval_rows = [json.loads(line) for line in (output_dir / "eval_runs.jsonl").read_text(encoding="utf-8").splitlines()]
    eval_by_family = {row["skill_family"]: row for row in eval_rows}
    assert eval_by_family["python-advisory"]["evaluation_status"] == "partial_no_family_eval_harness"
    assert eval_by_family["python-advisory"]["runtime_smoke_status"] == "pass"
    assert eval_by_family["repo-dependency-use-triage"]["evaluation_status"] == "pass"
    assert eval_by_family["repo-dependency-use-triage"]["task_count"] == 4
    assert eval_by_family["repo-dependency-use-triage"]["pass_count"] == 4
    assert eval_by_family["repo-dependency-use-triage"]["bundle_attachment_mode"] == "real_release_bundle_pinned"

    bundle_matrix = _read_json(output_dir / "bundle_matrix.json")
    assert all(item["status"] == "pass" for item in bundle_matrix["boundary_notes"])

    claim_matrix = _read_json(output_dir / "claim_boundary_matrix.json")
    blocked = set(claim_matrix["global_blocked_claims"])
    assert {
        "compiler_superiority",
        "mature_agenthost_effectiveness",
        "general_vulnerability_discovery",
        "production_scanner_readiness",
        "official_public_benchmark_performance",
        "exploitability_or_reachability",
    }.issubset(blocked)
    for family in claim_matrix["families"]:
        assert "compiler_superiority" in family["blocked_claims"]
        assert "official_public_benchmark_performance" in family["blocked_claims"]


def _registry_with_temp_state(tmp_path: Path) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    payload = _read_json(REGISTRY)
    for family in payload["families"]:
        family["default_state_dir"] = str(tmp_path / "state" / family["skill_family"])
    registry_path = tmp_path / "registry.json"
    registry_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return registry_path


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
