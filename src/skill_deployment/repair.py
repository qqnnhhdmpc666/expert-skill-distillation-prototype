from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .schemas import GateDecision, PatchPlan, VerifierReport


@dataclass(frozen=True)
class RepairContext:
    scenario_id: str
    task_family: str
    current_capabilities: tuple[str, ...]
    expected_capabilities: tuple[str, ...]
    verifier_report: VerifierReport
    repair_policy: dict[str, str]


@dataclass(frozen=True)
class RepairOperator:
    operator_id: str
    repair_action: str
    feedback_types: tuple[str, ...]
    strategy: str
    description: str
    family_allowlist: tuple[str, ...] = ()
    hard_intervention: bool = False
    base_priority: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def applies_to(self, context: RepairContext) -> bool:
        if context.verifier_report.feedback_type not in self.feedback_types:
            return False
        if self.family_allowlist and context.task_family not in self.family_allowlist:
            return False
        return True


REPAIR_OPERATORS: tuple[RepairOperator, ...] = (
    RepairOperator(
        operator_id="op_patch_capability_generic",
        repair_action="patch_capability",
        feedback_types=("missing_capability",),
        strategy="add_missing_expected",
        description="Append missing expected capabilities while keeping the current package compact.",
        hard_intervention=True,
        base_priority=50,
    ),
    RepairOperator(
        operator_id="op_patch_boundary_auth",
        repair_action="patch_boundary",
        feedback_types=("ownership_boundary_missing",),
        strategy="replace_with_expected",
        description="Rewrite the package to reassert ownership and boundary checks.",
        family_allowlist=("auth_access_control",),
        hard_intervention=True,
        base_priority=60,
    ),
    RepairOperator(
        operator_id="op_strengthen_evidence_generic",
        repair_action="strengthen_evidence_requirement",
        feedback_types=("weak_evidence",),
        strategy="replace_with_expected",
        description="Keep the same task intent but strengthen evidence requirements and output specificity.",
        hard_intervention=False,
        base_priority=45,
    ),
    RepairOperator(
        operator_id="op_add_observation_step_generic",
        repair_action="add_observation_step",
        feedback_types=("target_context_missing", "config_path_missing", "unsupported_evidence"),
        strategy="observation_only",
        description="Preserve capabilities and add explicit observation steps so evidence binds to the target.",
        hard_intervention=False,
        base_priority=55,
    ),
    RepairOperator(
        operator_id="op_rewrite_output_contract_generic",
        repair_action="rewrite_output_contract",
        feedback_types=("output_contract_error",),
        strategy="replace_with_expected",
        description="Restore the structured report contract so outputs remain machine-verifiable.",
        hard_intervention=True,
        base_priority=55,
    ),
    RepairOperator(
        operator_id="op_reduce_false_positive_generic",
        repair_action="reduce_false_positive_risk",
        feedback_types=("false_positive_risk", "overbroad_finding"),
        strategy="remove_unsupported",
        description="Remove unsupported findings and shrink the package back to grounded capabilities.",
        hard_intervention=False,
        base_priority=50,
    ),
    RepairOperator(
        operator_id="op_add_safety_boundary_generic",
        repair_action="add_safety_boundary",
        feedback_types=("unsafe_action_risk",),
        strategy="replace_with_expected",
        description="Tighten execution boundaries when a repair would otherwise authorize unsafe actions.",
        hard_intervention=True,
        base_priority=65,
    ),
    RepairOperator(
        operator_id="op_reduce_select_trace_generic",
        repair_action="reduce_or_select_trace",
        feedback_types=("high_cost_low_gain", "trace_missing"),
        strategy="observation_only",
        description="Preserve core capabilities while reducing or reallocating trace budget to the most informative observations.",
        hard_intervention=False,
        base_priority=40,
    ),
    RepairOperator(
        operator_id="op_reject_and_rollback_generic",
        repair_action="reject_and_rollback",
        feedback_types=("regression_observed",),
        strategy="rollback_to_expected",
        description="Rollback to the last supported package after a regression.",
        hard_intervention=True,
        base_priority=70,
    ),
    RepairOperator(
        operator_id="op_noop_pass",
        repair_action="no_op",
        feedback_types=("pass",),
        strategy="noop",
        description="No repair required.",
        hard_intervention=False,
        base_priority=100,
    ),
)


def _operator_score(operator: RepairOperator, context: RepairContext, preferred_action: str) -> int:
    score = operator.base_priority
    if operator.repair_action == preferred_action:
        score += 100
    if operator.family_allowlist and context.task_family in operator.family_allowlist:
        score += 10
    if operator.strategy == "add_missing_expected" and context.verifier_report.missing_capabilities:
        score += len(context.verifier_report.missing_capabilities)
    if operator.strategy == "remove_unsupported" and context.verifier_report.false_positive_capabilities:
        score += len(context.verifier_report.false_positive_capabilities)
    if operator.strategy == "observation_only" and context.verifier_report.weak_evidence_capabilities:
        score += len(context.verifier_report.weak_evidence_capabilities)
    return score


def select_repair_operator(context: RepairContext) -> tuple[RepairOperator, int]:
    preferred_action = context.repair_policy.get(context.verifier_report.feedback_type, "manual_review_required")
    candidates = [operator for operator in REPAIR_OPERATORS if operator.applies_to(context)]
    if not candidates:
        fallback = RepairOperator(
            operator_id="op_manual_review_fallback",
            repair_action=preferred_action,
            feedback_types=(context.verifier_report.feedback_type,),
            strategy="replace_with_expected",
            description="Fallback operator because no typed registry entry matched.",
            hard_intervention=True,
            base_priority=1,
        )
        return fallback, 1
    ranked = sorted(
        ((_operator_score(operator, context, preferred_action), operator) for operator in candidates),
        key=lambda item: (item[0], item[1].operator_id),
        reverse=True,
    )
    score, operator = ranked[0]
    return operator, score


def _apply_strategy(context: RepairContext, operator: RepairOperator) -> tuple[str, ...]:
    current = list(context.current_capabilities)
    expected = list(context.expected_capabilities)
    expected_set = set(expected)

    if operator.strategy == "noop":
        return tuple(current)
    if operator.strategy == "add_missing_expected":
        for capability_id in context.verifier_report.missing_capabilities:
            if capability_id not in current:
                current.append(capability_id)
        return tuple(current)
    if operator.strategy == "remove_unsupported":
        return tuple(item for item in current if item in expected_set)
    if operator.strategy == "observation_only":
        return tuple(current)
    if operator.strategy in {"replace_with_expected", "rollback_to_expected"}:
        return tuple(expected)
    return tuple(expected)


def build_patch_and_gate(context: RepairContext) -> tuple[tuple[str, ...], PatchPlan, GateDecision]:
    operator, selection_score = select_repair_operator(context)
    after_capabilities = _apply_strategy(context, operator)
    verifier = context.verifier_report
    scores = dict(verifier.scores)
    scores.update({"cost_budget_score": 1.0, "safety_boundary_score": 1.0})
    after_set = set(after_capabilities)
    expected_set = set(context.expected_capabilities)
    gate_accept = (
        verifier.feedback_type == "pass"
        or (expected_set.issubset(after_set) and not (after_set - expected_set))
        or operator.strategy == "observation_only"
    )
    gate = GateDecision(
        decision="accept_no_change" if verifier.feedback_type == "pass" else "accept" if gate_accept else "reject",
        intervention="hard" if operator.hard_intervention else "soft",
        reason=f"{verifier.feedback_type} -> {operator.repair_action}",
        scores=scores,
        refs={
            "taxonomy_ref": "revision/feedback_taxonomy.json",
            "repair_policy_ref": "revision/repair_policy.json",
            "intervention_scores_ref": "revision/intervention_scores.json",
            "operator_id": operator.operator_id,
        },
    )
    patch = PatchPlan(
        feedback_type=verifier.feedback_type,
        repair_action=operator.repair_action,
        before_capabilities=context.current_capabilities,
        after_capabilities=after_capabilities,
        details={
            "operator_id": operator.operator_id,
            "operator_strategy": operator.strategy,
            "operator_description": operator.description,
            "selection_score": selection_score,
            "preferred_action": context.repair_policy.get(verifier.feedback_type, "manual_review_required"),
        },
    )
    return after_capabilities, patch, gate
