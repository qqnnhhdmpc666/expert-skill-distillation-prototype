from pathlib import Path

from skill_deployment import OfflineDeterministicRunner, RunnerContext, SkillPackage, resolve_task_conditioned_activation, select_controlled_task_cases


ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = ROOT / "data" / "task_cases"


def build_task_conditioned_skill() -> SkillPackage:
    return SkillPackage(
        skill_id="secure_code_review",
        version="v2",
        task_family="secure_code_review",
        capabilities=(
            "UPLOAD_PATH_ISOLATION",
            "UPLOAD_TYPE_MAGIC",
            "UPLOAD_AUDIT_RETENTION",
            "CONFIG_AUDIT_EXPORT",
            "CONFIG_ENV_GUARD",
            "API_SCHEMA_CONTRACT",
            "API_OVERBROAD_RISK",
            "AUTH_SCOPE_MATRIX",
            "AUTH_OBJECT_OWNERSHIP",
            "AUTH_ERROR_ENVELOPE",
        ),
        output_contract=("capability_id", "evidence_span", "recommended_fix"),
        trace_contract=("trajectory.jsonl", "target_reads.json", "skill_reads.json"),
        metadata={
            "supported_task_families": ["upload_security", "config_security", "api_or_code_review", "auth_access_control"],
            "out_of_scope_group": "out_of_scope_guard",
            "capability_groups": [
                {
                    "name": "upload_security",
                    "task_families": ["upload_security"],
                    "capabilities": ["UPLOAD_PATH_ISOLATION", "UPLOAD_TYPE_MAGIC", "UPLOAD_AUDIT_RETENTION"],
                },
                {
                    "name": "config_security",
                    "task_families": ["config_security"],
                    "capabilities": ["CONFIG_AUDIT_EXPORT", "CONFIG_ENV_GUARD"],
                },
                {
                    "name": "api_or_code_review",
                    "task_families": ["api_or_code_review"],
                    "capabilities": ["API_SCHEMA_CONTRACT", "API_OVERBROAD_RISK"],
                },
                {
                    "name": "auth_access_control",
                    "task_families": ["auth_access_control"],
                    "capabilities": ["AUTH_SCOPE_MATRIX", "AUTH_OBJECT_OWNERSHIP", "AUTH_ERROR_ENVELOPE"],
                },
                {
                    "name": "out_of_scope_guard",
                    "task_families": [],
                    "capabilities": [],
                },
            ],
        },
    )


def load_case(name: str):
    return select_controlled_task_cases(DATA_ROOT, name)[0]


def test_resolve_task_conditioned_activation_selects_matching_group() -> None:
    skill = build_task_conditioned_skill()

    upload = resolve_task_conditioned_activation(skill, load_case("upload"))
    config = resolve_task_conditioned_activation(skill, load_case("config"))
    api = resolve_task_conditioned_activation(skill, load_case("api_review"))
    auth = resolve_task_conditioned_activation(skill, load_case("auth"))
    data_quality = resolve_task_conditioned_activation(skill, load_case("data_quality"))

    assert upload["activated_capability_group"] == "upload_security"
    assert tuple(upload["capabilities"]) == ("UPLOAD_PATH_ISOLATION", "UPLOAD_TYPE_MAGIC", "UPLOAD_AUDIT_RETENTION")
    assert config["activated_capability_group"] == "config_security"
    assert tuple(config["capabilities"]) == ("CONFIG_AUDIT_EXPORT", "CONFIG_ENV_GUARD")
    assert api["activated_capability_group"] == "api_or_code_review"
    assert tuple(api["capabilities"]) == ("API_SCHEMA_CONTRACT", "API_OVERBROAD_RISK")
    assert auth["activated_capability_group"] == "auth_access_control"
    assert tuple(auth["capabilities"]) == ("AUTH_SCOPE_MATRIX", "AUTH_OBJECT_OWNERSHIP", "AUTH_ERROR_ENVELOPE")
    assert data_quality["activated_capability_group"] == "out_of_scope_guard"
    assert data_quality["out_of_scope"] is True
    assert data_quality["capabilities"] == ()


def test_offline_runner_uses_only_config_capabilities_for_config_case(tmp_path: Path) -> None:
    runner = OfflineDeterministicRunner()
    case = load_case("config")
    context = RunnerContext(
        scenario_id=case.case_id,
        backend="offline_deterministic",
        target_dir=tmp_path / "target",
        output_dir=tmp_path / "agent",
        attempt_id="config_case",
        skill_package=build_task_conditioned_skill(),
        task_case=case,
        metadata={},
    )

    result = runner.run(context)
    capability_ids = {item["capability_id"] for item in result.report.findings}

    assert capability_ids == {"CONFIG_AUDIT_EXPORT", "CONFIG_ENV_GUARD"}
    assert "UPLOAD_TYPE_MAGIC" not in capability_ids
    assert "activated_capability_group:config_security" in result.report.notes


def test_offline_runner_marks_data_quality_as_out_of_scope(tmp_path: Path) -> None:
    runner = OfflineDeterministicRunner()
    case = load_case("data_quality")
    context = RunnerContext(
        scenario_id=case.case_id,
        backend="offline_deterministic",
        target_dir=tmp_path / "target",
        output_dir=tmp_path / "agent",
        attempt_id="data_quality_case",
        skill_package=build_task_conditioned_skill(),
        task_case=case,
        metadata={},
    )

    result = runner.run(context)

    assert result.report.findings == ()
    assert "out_of_scope" in result.report.notes
    assert "unsupported_task_family:data_quality_review" in result.report.notes
    assert "activated_capability_group:out_of_scope_guard" in result.report.notes
