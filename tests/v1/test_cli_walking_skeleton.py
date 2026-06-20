from __future__ import annotations

import json
from pathlib import Path

from expert_skill_system.cli import main

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = PROJECT_ROOT / "data" / "v1_walking_skeleton"


def _output(capsys):
    return json.loads(capsys.readouterr().out)


def test_demo_is_a_real_state_driven_cli_path(tmp_path: Path, capsys) -> None:
    state = tmp_path / ".eskill"
    exit_code = main(["--state-dir", str(state), "demo", "--data-dir", str(DATA_ROOT)])
    result = _output(capsys)

    assert exit_code == 0
    assert result["status"] == "pass"
    assert result["build_attestation"] == "pass"
    assert result["decision"]["verdict"] == "advisory_applicable"
    assert result["decision"]["reason_codes"] == ["VERSION_IN_RANGE"]
    assert (state / "metadata.sqlite").exists()
    assert (state / "artifacts" / "sha256").is_dir()

    assert main(["--state-dir", str(state), "inspect", "session", result["session_id"]]) == 0
    session = _output(capsys)
    assert session["bundle_digest"] == result["bundle_digest"]
    assert session["payload"]["trace_ref"]["digest"].startswith("sha256:")


def test_granular_cli_build_validate_promote_run_and_baselines(tmp_path: Path, capsys) -> None:
    state = tmp_path / ".eskill"
    assert main(["--state-dir", str(state), "init"]) == 0
    initialized = _output(capsys)
    assert initialized["schema_count"] >= 10
    assert (state / "schemas" / "release_bundle.v1.schema.json").exists()
    assert (
        main(
            [
                "--state-dir",
                str(state),
                "source",
                "add",
                str(DATA_ROOT / "expert_spec" / "python_advisory_review.md"),
                "--adapter",
                "expert-document",
                "--source-id",
                "expert",
            ]
        )
        == 0
    )
    _output(capsys)
    assert (
        main(
            [
                "--state-dir",
                str(state),
                "source",
                "add",
                str(DATA_ROOT / "osv" / "PYSEC-2018-28.json"),
                "--adapter",
                "osv-snapshot",
                "--source-id",
                "osv",
            ]
        )
        == 0
    )
    _output(capsys)
    assert main(["--state-dir", str(state), "build", "python-advisory"]) == 0
    build = _output(capsys)
    assert build["stage_count"] == 10
    bundle_digest = build["bundle_digest"]
    assert main(["--state-dir", str(state), "validate", "bundle", bundle_digest]) == 0
    assert _output(capsys)["status"] == "pass"
    assert (
        main(
            [
                "--state-dir",
                str(state),
                "promote",
                "python-advisory",
                bundle_digest,
                "--expected-generation",
                "0",
            ]
        )
        == 0
    )
    assert _output(capsys)["generation"] == 1
    assert (
        main(
            [
                "--state-dir",
                str(state),
                "run",
                "python-advisory",
                "--requirements",
                str(DATA_ROOT / "runtime_inputs" / "requirements.txt"),
                "--environment",
                str(DATA_ROOT / "runtime_inputs" / "environment.json"),
                "--advisory",
                "PYSEC-2018-28",
            ]
        )
        == 0
    )
    run = _output(capsys)
    assert run["domain_outcome"]["decision"]["verdict"] == "advisory_applicable"

    assert main(["--state-dir", str(state), "baselines"]) == 0
    baselines = _output(capsys)
    assert set(baselines["conditions"]) == {
        "no_skill",
        "full_material",
        "direct_to_skill_ir",
        "compiler_distilled_skill",
        "human_authored_reference_skill",
    }
    assert baselines["conditions"]["human_authored_reference_skill"]["status"] == "not_available"
    assert "not AgentHost effectiveness" in baselines["claim_boundary"]
