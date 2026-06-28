from __future__ import annotations

import json
from pathlib import Path

from scripts import run_expert_knowledge_ablation_v0 as ablation
from scripts.run_expert_knowledge_ablation_v0 import main as run_ablation


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_claim_boundary_blocks_broad_claims(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test-secret-do-not-write")
    output = tmp_path / "out"
    assert run_ablation(
        ["--output", str(output), "--state-dir", str(tmp_path / "state"), "--reports-dir", str(tmp_path / "reports"), "--mock-api"]
    ) == 0
    claims = read_json(output / "claim_boundary.json")
    blocked = claims["blocked_claims"]
    assert blocked["official_benchmark_performance"] == "not_claimed"
    assert blocked["retrieval_algorithm_superiority"] == "not_claimed"
    assert blocked["compiler_superiority"] == "not_evaluated"
    assert read_json(output / "anti_leakage_audit.json")["anti_leakage_status"] == "pass"


def test_api_key_leakage_is_detected(tmp_path: Path) -> None:
    output = tmp_path / "out"
    output.mkdir()
    secret = "sk-test-secret-do-not-write"
    (output / "leak.json").write_text(json.dumps({"bad": secret}), encoding="utf-8")
    config = ablation.ApiConfig(
        api_key=secret,
        base_url="https://api.deepseek.com",
        model="deepseek-chat",
        provider_label="test",
        mock_api=True,
    )
    audit = ablation._anti_leakage_audit(output, config)
    assert audit["anti_leakage_status"] == "failed"
    assert audit["checks"]["no_raw_api_key_in_artifacts"] is False
