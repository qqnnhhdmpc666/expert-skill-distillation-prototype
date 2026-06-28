from __future__ import annotations

import json
from pathlib import Path

from scripts.run_expert_knowledge_ablation_v0 import main as run_ablation


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_condition_manifests_encode_visibility_boundaries(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test-secret-do-not-write")
    output = tmp_path / "out"
    assert run_ablation(
        ["--output", str(output), "--state-dir", str(tmp_path / "state"), "--reports-dir", str(tmp_path / "reports"), "--mock-api"]
    ) == 0

    no_expert = read_json(output / "runs" / "no_expert_knowledge" / "knowledge_condition_manifest.json")
    assert no_expert["expert_material_visible"] is False
    assert no_expert["distilled_skill_visible"] is False
    assert no_expert["distilled_knowledge_visible"] is False

    raw_prompt = (output / "runs" / "raw_expert_material" / "agent_prompt_runtime_visible.md").read_text(
        encoding="utf-8"
    )
    assert "extracted_skill.md" not in raw_prompt
    assert "knowledge_projection.json" not in raw_prompt

    skill_only = read_json(output / "runs" / "distilled_skill_only" / "knowledge_condition_manifest.json")
    assert skill_only["distilled_skill_visible"] is True
    assert skill_only["distilled_knowledge_visible"] is False

    knowledge_only_prompt = (
        output / "runs" / "distilled_knowledge_only" / "agent_prompt_runtime_visible.md"
    ).read_text(encoding="utf-8")
    assert "Distilled procedural Skill" not in knowledge_only_prompt

    controlled = read_json(
        output / "runs" / "distilled_skill_plus_controlled_access" / "knowledge_condition_manifest.json"
    )
    assert controlled["controlled_access_enabled"] is True
    assert controlled["static_knowledge_injected"] is False
