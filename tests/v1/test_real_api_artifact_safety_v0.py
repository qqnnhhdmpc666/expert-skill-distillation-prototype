from __future__ import annotations

import json
from pathlib import Path

from scripts.run_real_api_benchmark_micro_v0 import main as run_real_api_micro


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_api_key_is_never_written_to_artifacts(tmp_path: Path, monkeypatch) -> None:
    secret = "sk-test-secret-do-not-write"
    monkeypatch.setenv("DEEPSEEK_API_KEY", secret)
    output = tmp_path / "out"
    assert run_real_api_micro(
        [
            "--output",
            str(output),
            "--state-dir",
            str(tmp_path / "state"),
            "--reports-dir",
            str(tmp_path / "reports"),
            "--mock-api",
        ]
    ) == 0
    artifact_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in output.rglob("*")
        if path.is_file() and path.suffix.lower() in {".json", ".jsonl", ".md", ".txt"}
    )
    assert secret not in artifact_text
    manifest = read_json(output / "api_execution_manifest.json")
    assert manifest["OPENAI_API_KEY_present"] is True
    assert manifest["raw_api_key_written"] is False
    audit = read_json(output / "anti_leakage_audit.json")
    assert audit["anti_leakage_status"] == "pass"
    assert audit["checks"]["no_raw_api_key_in_artifacts"] is True


def test_null_and_negative_effects_are_preserved(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test-secret-do-not-write")
    output = tmp_path / "out"
    reports = tmp_path / "reports"
    assert run_real_api_micro(
        ["--output", str(output), "--state-dir", str(tmp_path / "state"), "--reports-dir", str(reports), "--mock-api"]
    ) == 0
    effect_report = reports / "REAL_API_BENCHMARK_MICRO_V0_EFFECT_INTERPRETATION.md"
    assert effect_report.exists()
    matrix = read_json(output / "backend_condition_lane_matrix.json")["rows"]
    assert any(row["verifier_pass_rate"] is None for row in matrix)
    assert any(row["execution_status"] in {"blocked", "skipped"} for row in matrix)
