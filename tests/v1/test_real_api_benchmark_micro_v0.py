from __future__ import annotations

import json
from pathlib import Path

from scripts import run_real_api_benchmark_micro_v0 as real_api_micro
from scripts.run_real_api_benchmark_micro_v0 import ApiResult
from scripts.run_real_api_benchmark_micro_v0 import main as run_real_api_micro


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_missing_api_key_blocks_without_false_pass(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    output = tmp_path / "out"
    assert run_real_api_micro(
        ["--output", str(output), "--state-dir", str(tmp_path / "state"), "--reports-dir", str(tmp_path / "reports")]
    ) == 1
    aggregate = read_json(output / "aggregate_summary.json")
    matrix = read_json(output / "backend_condition_lane_matrix.json")["rows"]
    assert aggregate["real_api_status"] == "blocked_missing_api_key"
    assert aggregate["real_api_benchmark_micro_v0_status"] == "blocked_missing_api_key"
    assert all(not row["real_llm_agent_executed"] for row in matrix if row["lane"] == "document_to_agent_real_api")
    assert all(row["claim_counted"] is False for row in matrix)


def test_mock_real_api_matrix_and_reports(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test-secret-do-not-write")
    output = tmp_path / "out"
    reports = tmp_path / "reports"
    assert run_real_api_micro(
        [
            "--output",
            str(output),
            "--state-dir",
            str(tmp_path / "state"),
            "--reports-dir",
            str(reports),
            "--mock-api",
        ]
    ) == 0
    aggregate = read_json(output / "aggregate_summary.json")
    matrix = read_json(output / "backend_condition_lane_matrix.json")["rows"]
    keys = {(row["lane"], row["backend"], row["condition"]) for row in matrix}
    for lane in ["document_to_agent_real_api", "skillsbench_micro", "skillgen_mapping", "swebench_micro"]:
        assert (lane, "mini_swe_agent_real_llm", "no_skill") in keys
        assert (lane, "mini_swe_agent_real_llm", "document_to_agent_bundle") in keys
    assert aggregate["document_to_agent_lane_executed"] is True
    assert aggregate["benchmark_style_lane_attempted"] is True
    assert read_json(output / "cost_summary.json")["api_call_count"] == 2
    assert (reports / "REAL_API_BENCHMARK_MICRO_V0_STATUS.md").exists()
    assert (reports / "REAL_API_BENCHMARK_MICRO_V0_EFFECT_INTERPRETATION.md").exists()


def test_swebench_blocked_does_not_block_document_lane(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test-secret-do-not-write")
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
    per_lane = read_json(output / "per_lane_summary.json")["lanes"]
    assert per_lane["document_to_agent_real_api"]["status"] == "executed"
    assert per_lane["swebench_micro"]["status"] == "blocked_or_mapping_only"
    aggregate = read_json(output / "aggregate_summary.json")
    assert aggregate["real_api_status"] == "pass"


def test_non_mock_path_uses_mini_swe_agent_not_direct_chat(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test-secret-do-not-write")

    def fail_direct_chat(*args, **kwargs):  # noqa: ANN002, ANN003
        raise AssertionError("non-mock path must not use direct chat completion")

    def fake_mini_swe_agent(config, prompt, run_dir):  # noqa: ANN001
        return ApiResult(
            ok=True,
            content=json.dumps(real_api_micro._reference_prediction(), sort_keys=True),
            status_code=200,
            error_type=None,
            error_summary=None,
            token_usage={"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
            raw_response_redacted={"mini_swe_agent": True},
            runtime_seconds=0.01,
            agent_surface="mini_swe_agent_real_llm",
            mini_swe_agent_trajectory_ref=str(Path(run_dir) / "mini_swe_agent_real_llm_trajectory.json"),
            mini_swe_agent_result={"exit_status": "Submitted"},
        )

    monkeypatch.setattr(real_api_micro, "_call_chat_completion", fail_direct_chat)
    monkeypatch.setattr(real_api_micro, "_run_mini_swe_agent_real_llm", fake_mini_swe_agent)

    output = tmp_path / "out"
    assert run_real_api_micro(
        ["--output", str(output), "--state-dir", str(tmp_path / "state"), "--reports-dir", str(tmp_path / "reports")]
    ) == 0
    rows = read_json(output / "backend_condition_lane_matrix.json")["rows"]
    doc_rows = [row for row in rows if row["lane"] == "document_to_agent_real_api"]
    assert doc_rows
    assert all(row["agent_execution_surface"] == "mini_swe_agent_real_llm" for row in doc_rows)
