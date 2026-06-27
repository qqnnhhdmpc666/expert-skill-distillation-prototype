from __future__ import annotations

from typing import Any

REQUIRED_RULE_TEXT = """Before deciding dependency_used_and_affected, the runtime must require:
1. dependency declaration evidence
2. resolved version evidence
3. import/use-site evidence
4. advisory affected range evidence
5. decision evidence

If import/use evidence is missing, the decision must be dependency_present_not_used or unresolved, never dependency_used_and_affected."""


def build_revision_plan(
    *,
    expert_material_v0: str,
    expected_evidence_policy: dict[str, Any],
    failure_summary: dict[str, Any],
) -> tuple[dict[str, Any], str]:
    revision_targets = _revision_targets(expected_evidence_policy, failure_summary)
    repair_type = _repair_type(revision_targets)
    revised_material = _append_revision_section(expert_material_v0)
    plan = {
        "schema_version": "distillation_revision_plan.v1",
        "repair_type": repair_type,
        "revision_targets": revision_targets,
        "applies_to_task_family": "dependency_use_triage",
        "task_specific_patch": False,
        "patched_task_answers": [],
        "source_failure_types": sorted(failure_summary.get("failure_types", {})),
        "required_evidence_after_revision": list(expected_evidence_policy["required_evidence"]),
        "decision_policy_after_revision": dict(expected_evidence_policy.get("decision_policy", {})),
        "knowledge_projection_policy_after_revision": dict(expected_evidence_policy.get("knowledge_projection_policy", {})),
        "candidate_path_overrides_after_revision": dict(expected_evidence_policy.get("candidate_path_overrides", {})),
        "rule_added": REQUIRED_RULE_TEXT,
        "scope_guard": "The rule applies to every dependency_use_triage task and does not mention a concrete task id.",
        "modifies": {
            "skill_rule": "skill_rule" in revision_targets,
            "evidence_binding_plan": "evidence_binding_plan" in revision_targets,
            "knowledge_access_binding": "knowledge_projection" in revision_targets,
            "runtime_policy": "runtime_policy" in revision_targets,
        },
    }
    return plan, revised_material


def _append_revision_section(expert_material_v0: str) -> str:
    base = expert_material_v0.rstrip()
    return (
        base
        + "\n\n## Distilled Revision v1: use-site evidence gate\n\n"
        + REQUIRED_RULE_TEXT
        + "\n\nThis revision is a general dependency-use triage rule. It is not a patch for a specific task answer.\n"
    )


def _revision_targets(expected_policy: dict[str, Any], failure_summary: dict[str, Any]) -> list[str]:
    configured = expected_policy.get("revision_targets")
    if configured:
        return [str(item) for item in configured]
    repair_targets = set(failure_summary.get("repair_targets", {}))
    if "knowledge_projection" in repair_targets:
        return ["knowledge_projection", "knowledge_access_binding"]
    if repair_targets == {"evidence_binding_plan"}:
        return ["evidence_binding_plan"]
    return ["skill_rule", "evidence_binding_plan"]


def _repair_type(revision_targets: list[str]) -> str:
    if "knowledge_projection" in revision_targets:
        return "knowledge_projection_repair"
    if revision_targets == ["evidence_binding_plan"]:
        return "evidence_binding_repair"
    return "rule_generalization"
