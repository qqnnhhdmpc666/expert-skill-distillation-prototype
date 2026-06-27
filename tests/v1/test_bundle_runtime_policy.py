from __future__ import annotations

import json
from pathlib import Path

from scripts.run_distillation_loop_v1 import main as run_distillation_loop_v1

CASE_ROOT = Path("data/distillation_cases/repo_dependency_use_triage_v1")


def test_v1_bundle_runtime_policies_are_pinned_and_different(tmp_path: Path) -> None:
    output_dir = tmp_path / "v1-output"
    run_distillation_loop_v1(
        [
            "--case-root",
            str(CASE_ROOT),
            "--state-dir",
            str(tmp_path / "v1-state"),
            "--output",
            str(output_dir),
        ]
    )

    d1_base = _policy(output_dir, "D1_skill_missing_rule", "baseline_bundle")
    d1_revised = _policy(output_dir, "D1_skill_missing_rule", "revised_bundle")
    assert "import_use_site" not in d1_base["required_evidence"]
    assert "import_use_site" in d1_revised["required_evidence"]

    d2_base = _policy(output_dir, "D2_skill_overgeneralized_rule", "baseline_bundle")
    d2_revised = _policy(output_dir, "D2_skill_overgeneralized_rule", "revised_bundle")
    assert d2_base["decision_policy"]["version_range_comparison_required"] is False
    assert d2_revised["decision_policy"]["version_range_comparison_required"] is True

    d3_base = _policy(output_dir, "D3_knowledge_gap", "baseline_bundle")
    d3_revised = _policy(output_dir, "D3_knowledge_gap", "revised_bundle")
    assert d3_base["knowledge_projection_policy"]["allowed_advisory_fields"] == []
    assert d3_revised["knowledge_projection_policy"]["allowed_advisory_fields"] == ["affected_ranges"]

    d4_base = _evidence_plan(output_dir, "D4_evidence_binding_gap", "baseline_bundle")
    d4_revised = _evidence_plan(output_dir, "D4_evidence_binding_gap", "revised_bundle")
    assert _candidate_paths(d4_base, "import_use_site") == []
    assert _candidate_paths(d4_revised, "import_use_site") == ["*.py"]


def _policy(output_dir: Path, defect_id: str, bundle_dir: str) -> dict:
    return _read_json(output_dir / "cases" / defect_id / bundle_dir / "runtime_bundle_policy.json")


def _evidence_plan(output_dir: Path, defect_id: str, bundle_dir: str) -> dict:
    return _read_json(output_dir / "cases" / defect_id / bundle_dir / "evidence_binding_plan.json")


def _candidate_paths(plan: dict, evidence_type: str) -> list[str] | None:
    for row in plan["binding_plan"]:
        if row["evidence_type"] == evidence_type:
            return row.get("candidate_paths")
    return None


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
