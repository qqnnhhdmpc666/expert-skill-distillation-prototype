from pathlib import Path

from skill_deployment import CAPABILITY_SPECS
from skill_deployment.repair import RepairContext, build_patch_and_gate, select_repair_operator
from skill_deployment.runner import RunnerContext, get_backend_runner, summarize_runner_context
from skill_deployment.schemas import ExecutionReport, GateDecision, PatchPlan, SkillPackage, TraceRecord, VerifierReport
from skill_deployment.validity import build_repair_loop_validity_card


def test_skill_package_roundtrip_and_validation() -> None:
    package = SkillPackage(
        skill_id="upload_skill",
        version="v2",
        task_family="upload_security",
        capabilities=("UPLOAD_PATH_ISOLATION", "UPLOAD_AUDIT_RETENTION"),
        output_contract=("capability_id", "evidence_span", "recommended_fix"),
        trace_contract=("evidence_span",),
        metadata={"source": "expert_material"},
    )
    package.validate()
    restored = SkillPackage.from_dict(package.to_dict())

    assert restored == package


def test_execution_verifier_patch_gate_trace_roundtrip() -> None:
    report = ExecutionReport.from_dict(
        {
            "attempt": "A1_skill_v1",
            "backend": "offline_deterministic",
            "findings": [{"capability_id": "UPLOAD_PATH_ISOLATION", "evidence_span": "UPLOAD_ROOT / filename"}],
            "notes": ["structured output"],
        }
    )
    verifier = VerifierReport.from_dict(
        {
            "pass": False,
            "feedback_type": "missing_capability",
            "missing_capabilities": ["UPLOAD_AUDIT_RETENTION"],
            "scores": {"capability_coverage_score": 0.5},
        }
    )
    patch = PatchPlan.from_dict(
        {
            "feedback_type": "missing_capability",
            "repair_action": "patch_capability",
            "before_capabilities": ["UPLOAD_PATH_ISOLATION"],
            "after_capabilities": ["UPLOAD_PATH_ISOLATION", "UPLOAD_AUDIT_RETENTION"],
            "details_ref": "revision/repair_policy.json",
        }
    )
    gate = GateDecision.from_dict(
        {
            "decision": "accept",
            "intervention": "hard",
            "reason": "missing_capability -> patch_capability",
            "scores": {"capability_coverage_score": 0.5},
            "repair_policy_ref": "revision/repair_policy.json",
        }
    )
    trace = TraceRecord.from_dict(
        {
            "event": "finding",
            "capability_id": "UPLOAD_PATH_ISOLATION",
            "evidence_span": "UPLOAD_ROOT / filename",
            "attempt": "A1_skill_v1",
        }
    )

    assert report.to_dict()["attempt"] == "A1_skill_v1"
    assert verifier.to_dict()["feedback_type"] == "missing_capability"
    assert patch.to_dict()["repair_action"] == "patch_capability"
    assert gate.to_dict()["decision"] == "accept"
    assert trace.to_dict()["event"] == "finding"


def test_runner_context_summary_contains_skill_package() -> None:
    package = SkillPackage(
        skill_id="upload_skill",
        version="v1",
        task_family="upload_security",
        capabilities=("UPLOAD_PATH_ISOLATION",),
    )
    context = RunnerContext(
        scenario_id="upload_security_001",
        backend="offline_deterministic",
        target_dir=Path("target"),
        output_dir=Path("out"),
        skill_package=package,
        metadata={"attempt": "A1"},
    )
    payload = summarize_runner_context(context)

    assert payload["scenario_id"] == "upload_security_001"
    assert payload["skill_package"]["skill_id"] == "upload_skill"
    assert payload["metadata"]["attempt"] == "A1"


def test_backend_runner_registry_resolves_minimal_backends() -> None:
    offline = get_backend_runner("offline_deterministic", project_root=Path("."))
    local = get_backend_runner("non_oracle_local_semantic", project_root=Path("."))
    live_llm = get_backend_runner("live_llm_text", project_root=Path("."))
    harbor_upload = get_backend_runner("harbor_llm_repair_upload_replay", project_root=Path("."))

    assert offline.name == "offline_deterministic"
    assert local.name == "non_oracle_local_semantic"
    assert live_llm.name == "live_llm_text"
    assert harbor_upload.name == "harbor_llm_repair_upload_replay"


def test_repair_operator_registry_selects_policy_aligned_operator() -> None:
    verifier = VerifierReport(
        passed=False,
        feedback_type="target_context_missing",
        weak_evidence_capabilities=("DATA_TEMPORAL_SPLIT_GUARD",),
        scores={"evidence_binding_score": 0.0},
    )
    context = RepairContext(
        scenario_id="data_quality_review_001",
        task_family="data_quality_review",
        current_capabilities=(
            "DATA_REQUIRED_FIELD_COVERAGE",
            "DATA_TEMPORAL_SPLIT_GUARD",
            "DATA_LABEL_ENUM_ALIGNMENT",
        ),
        expected_capabilities=(
            "DATA_REQUIRED_FIELD_COVERAGE",
            "DATA_TEMPORAL_SPLIT_GUARD",
            "DATA_LABEL_ENUM_ALIGNMENT",
        ),
        verifier_report=verifier,
        repair_policy={"target_context_missing": "add_observation_step"},
    )

    operator, _ = select_repair_operator(context)

    assert operator.operator_id == "op_add_observation_step_generic"
    assert operator.repair_action == "add_observation_step"


def test_build_patch_and_gate_preserves_capabilities_for_observation_only_repair() -> None:
    verifier = VerifierReport(
        passed=False,
        feedback_type="target_context_missing",
        weak_evidence_capabilities=("DATA_TEMPORAL_SPLIT_GUARD",),
        scores={"evidence_binding_score": 0.0},
    )
    current = (
        "DATA_REQUIRED_FIELD_COVERAGE",
        "DATA_TEMPORAL_SPLIT_GUARD",
        "DATA_LABEL_ENUM_ALIGNMENT",
    )
    context = RepairContext(
        scenario_id="data_quality_review_001",
        task_family="data_quality_review",
        current_capabilities=current,
        expected_capabilities=current,
        verifier_report=verifier,
        repair_policy={"target_context_missing": "add_observation_step"},
    )

    after_capabilities, patch, gate = build_patch_and_gate(context)

    assert after_capabilities == current
    assert patch.to_dict()["repair_action"] == "add_observation_step"
    assert gate.to_dict()["decision"] == "accept"


def test_capability_registry_includes_non_security_transfer_family() -> None:
    spec = CAPABILITY_SPECS["DATA_TEMPORAL_SPLIT_GUARD"]

    assert spec.title == "Temporal split guard"
    assert "validation_cutoff=2025-04-30" in spec.detector_needles


def test_build_repair_loop_validity_card_marks_positive_delta() -> None:
    card = build_repair_loop_validity_card(
        card_id="demo_card",
        artifact="outputs/demo_loop",
        scenario="upload_security_001",
        backend="live_llm_text",
        a1_report={
            "pass": False,
            "feedback_type": "missing_capability",
            "missing_capabilities": ["UPLOAD_AUDIT_RETENTION"],
            "schema_errors": [],
            "weak_evidence_capabilities": [],
        },
        a2_report={
            "pass": True,
            "feedback_type": "pass",
            "missing_capabilities": [],
            "schema_errors": [],
            "weak_evidence_capabilities": [],
        },
        patch_plan={"repair_action": "patch_capability"},
        gate_decision={"decision": "accept"},
        sources=["outputs/demo_loop/A1/verifier_report.json", "outputs/demo_loop/A2/verifier_report.json"],
        claim_boundary="controlled only",
        grounded_agent_artifacts=True,
    )

    assert card["summary"]["reward_delta"] == 1.0
    assert card["metrics"]["outcome_delta"]["status"] == "supported"
    assert card["metrics"]["repair_attribution"]["note"].startswith("A1 feedback")
