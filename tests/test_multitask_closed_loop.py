import json
from pathlib import Path

from scripts.run_multitask_closed_loop import main


def test_multitask_closed_loop_proves_core_claims(tmp_path, monkeypatch) -> None:
    out_dir = tmp_path / "multitask_run"
    monkeypatch.setattr("sys.argv", ["run_multitask_closed_loop.py", "--output-dir", str(out_dir)])

    assert main() == 0

    summary = json.loads((out_dir / "summary.json").read_text(encoding="utf-8"))
    assert summary["case_count"] == 3
    assert summary["task_family_count"] == 3
    assert summary["a2_pass_count"] == 3
    assert set(summary["feedback_types"]) == {"evidence_gap", "false_positive", "missing_capability"}
    assert set(summary["patch_operators"]) == {
        "add_environment_negative_guard",
        "add_missing_capability_modules",
        "strengthen_evidence_protocol",
    }
    assert all(summary["claim_support"].values())

    for case in summary["case_summaries"]:
        case_dir = out_dir / case["artifact_dir"]
        for rel_path in (
            "inputs/expert_material.md",
            "inputs/target_asset.md",
            "attempts/A0_no_skill.json",
            "attempts/A1_skill_v1.json",
            "attempts/A2_skill_v2.json",
            "verifier/A1_feedback.json",
            "verifier/A2_feedback.json",
            "revision/patch_plan.json",
            "skills/skill_v1.md",
            "skills/skill_v2.md",
            "trajectory.jsonl",
        ):
            assert (case_dir / rel_path).exists(), f"missing {case_dir / rel_path}"

        patch_plan = json.loads((case_dir / "revision" / "patch_plan.json").read_text(encoding="utf-8"))
        assert patch_plan["feedback_type"] == case["feedback_type"]
        assert patch_plan["patch_operator"] == case["patch_operator"]


def test_multitask_manifest_points_to_existing_top_level_artifacts(tmp_path, monkeypatch) -> None:
    out_dir = tmp_path / "multitask_run"
    monkeypatch.setattr("sys.argv", ["run_multitask_closed_loop.py", "--output-dir", str(out_dir)])

    assert main() == 0

    manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
    literal_artifacts = [item for item in manifest["artifacts"] if "*" not in item and not item.endswith("/")]
    assert literal_artifacts
    for rel_path in literal_artifacts:
        assert (out_dir / Path(rel_path)).exists()
