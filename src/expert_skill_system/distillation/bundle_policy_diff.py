from __future__ import annotations

from typing import Any


def diff_runtime_policies(baseline_policy: dict[str, Any], revised_policy: dict[str, Any]) -> dict[str, Any]:
    baseline_required = list(baseline_policy.get("required_evidence", []))
    revised_required = list(revised_policy.get("required_evidence", []))
    baseline_decision = dict(baseline_policy.get("decision_policy", {}))
    revised_decision = dict(revised_policy.get("decision_policy", {}))
    baseline_knowledge = dict(baseline_policy.get("knowledge_projection_policy", {}))
    revised_knowledge = dict(revised_policy.get("knowledge_projection_policy", {}))
    baseline_candidates = dict(baseline_policy.get("candidate_path_overrides", {}))
    revised_candidates = dict(revised_policy.get("candidate_path_overrides", {}))
    return {
        "schema_version": "bundle_policy_diff.v1",
        "required_evidence_added": sorted(set(revised_required) - set(baseline_required)),
        "required_evidence_removed": sorted(set(baseline_required) - set(revised_required)),
        "decision_policy_changed": baseline_decision != revised_decision,
        "knowledge_projection_policy_changed": baseline_knowledge != revised_knowledge,
        "candidate_path_overrides_changed": baseline_candidates != revised_candidates,
        "baseline": {
            "required_evidence": baseline_required,
            "decision_policy": baseline_decision,
            "knowledge_projection_policy": baseline_knowledge,
            "candidate_path_overrides": baseline_candidates,
        },
        "revised": {
            "required_evidence": revised_required,
            "decision_policy": revised_decision,
            "knowledge_projection_policy": revised_knowledge,
            "candidate_path_overrides": revised_candidates,
        },
    }
