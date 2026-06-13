"""Minimal reusable helpers for the expert skill deployment prototype."""

from .artifacts import ManifestCheckResult, check_artifact_manifest
from .capability_registry import CAPABILITY_SPECS, CapabilitySpec
from .evidence import MarginalUtilityResult, build_marginal_utility_result, score_from_verifier, write_evidence_bundle
from .gate import ValidationGateResult, evaluate_validation_gate
from .harbor_adapter import HarborReplaySnapshot, execution_report_from_harbor_snapshot, load_harbor_replay_snapshot
from .install_state import install_skill_package, load_active_pointer, load_registry, resolve_installed_skill, rollback_installed_skill
from .live_contract import FAILURE_TAXONOMY, before_after_verifier, classify_verifier_failure, normalize_live_execution_report
from .provenance import SCHEMA_VERSION, VERIFIER_VERSION, build_verifier_hash, hash_file_sha256, hash_json_file_sha256, hash_json_payload_sha256, hash_text_sha256
from .repair import RepairContext, RepairOperator, build_patch_and_gate, select_repair_operator
from .runner import BackendRunner, HarborReplayRunner, LiveLLMSecurityRunner, NonOracleLocalSemanticRunner, OfflineDeterministicRunner, RunnerContext, RunnerResult, get_backend_runner, resolve_task_conditioned_activation, summarize_runner_context
from .schemas import ExecutionReport, GateDecision, PatchPlan, SkillPackage, TaskCase, TraceRecord, VerifierReport
from .task_cases import ControlledTaskCase, LegacyHoldoutTaskCase, controlled_task_case_from_directory, load_controlled_task_cases, load_legacy_holdout_task_cases, select_controlled_task_cases, validate_controlled_task_case_dir
from .token_budget import TokenBudgetResult, check_token_budget, estimate_tokens
from .trace import TraceCheckResult, check_rule_application_trace
from .validity import build_repair_loop_validity_card, build_skill_revision_validity_cards, render_single_validity_card_markdown, render_skill_revision_validity_markdown
from .verifier import summarize_verifier_report, verify_controlled_execution

__all__ = [
    "BackendRunner",
    "CAPABILITY_SPECS",
    "CapabilitySpec",
    "ControlledTaskCase",
    "ExecutionReport",
    "execution_report_from_harbor_snapshot",
    "FAILURE_TAXONOMY",
    "GateDecision",
    "get_backend_runner",
    "HarborReplayRunner",
    "HarborReplaySnapshot",
    "hash_file_sha256",
    "hash_json_file_sha256",
    "hash_json_payload_sha256",
    "hash_text_sha256",
    "LegacyHoldoutTaskCase",
    "LiveLLMSecurityRunner",
    "load_active_pointer",
    "ManifestCheckResult",
    "MarginalUtilityResult",
    "NonOracleLocalSemanticRunner",
    "OfflineDeterministicRunner",
    "PatchPlan",
    "RepairContext",
    "RepairOperator",
    "RunnerContext",
    "RunnerResult",
    "SkillPackage",
    "TaskCase",
    "TokenBudgetResult",
    "TraceRecord",
    "TraceCheckResult",
    "ValidationGateResult",
    "VerifierReport",
    "build_patch_and_gate",
    "build_marginal_utility_result",
    "build_repair_loop_validity_card",
    "build_skill_revision_validity_cards",
    "check_artifact_manifest",
    "check_rule_application_trace",
    "check_token_budget",
    "controlled_task_case_from_directory",
    "estimate_tokens",
    "evaluate_validation_gate",
    "load_controlled_task_cases",
    "load_harbor_replay_snapshot",
    "normalize_live_execution_report",
    "load_legacy_holdout_task_cases",
    "render_single_validity_card_markdown",
    "render_skill_revision_validity_markdown",
    "resolve_task_conditioned_activation",
    "resolve_installed_skill",
    "rollback_installed_skill",
    "score_from_verifier",
    "SCHEMA_VERSION",
    "select_controlled_task_cases",
    "select_repair_operator",
    "summarize_verifier_report",
    "summarize_runner_context",
    "validate_controlled_task_case_dir",
    "VERIFIER_VERSION",
    "verify_controlled_execution",
    "before_after_verifier",
    "build_verifier_hash",
    "classify_verifier_failure",
    "install_skill_package",
    "load_registry",
    "write_evidence_bundle",
]
