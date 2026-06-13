from pathlib import Path

from skill_deployment import RunnerContext, get_backend_runner


def test_harbor_upload_replay_adapter_reads_existing_a1() -> None:
    root = Path(__file__).resolve().parents[1]
    runner = get_backend_runner("harbor_llm_repair_upload_replay", project_root=root)
    result = runner.run(
        RunnerContext(
            scenario_id="harbor_llm_repair_upload_replay",
            backend="harbor_llm_repair_upload_replay",
            target_dir=root,
            output_dir=root,
            attempt_id="A1",
            skill_package=None,
            task_case=None,
            metadata={},
        )
    )

    assert result.report.backend == "harbor_llm_repair_upload_replay"
    assert result.report.attempt == "A1"
    assert result.output_path is not None and result.output_path.name == "security_report.json"
    assert "verifier_report" in result.artifact_paths
    assert "reward" in result.artifact_paths


def test_harbor_config_replay_adapter_reads_existing_a2() -> None:
    root = Path(__file__).resolve().parents[1]
    runner = get_backend_runner("harbor_llm_repair_config_replay", project_root=root)
    result = runner.run(
        RunnerContext(
            scenario_id="harbor_llm_repair_config_replay",
            backend="harbor_llm_repair_config_replay",
            target_dir=root,
            output_dir=root,
            attempt_id="A2",
            skill_package=None,
            task_case=None,
            metadata={},
        )
    )

    assert result.report.backend == "harbor_llm_repair_config_replay"
    assert result.report.attempt == "A2"
    assert len(result.report.findings) >= 1
    assert "skill_manifest" in result.artifact_paths
    assert "target_reads" in result.artifact_paths
