from __future__ import annotations

from pathlib import Path
from typing import Any

from ..core.models import ArtifactRef
from ..registry.workspace import Workspace


def load_bundle_runtime_policy_from_resolution(bundle_resolution: dict[str, Any] | None) -> dict[str, Any] | None:
    """Load the runtime policies pinned by a resolved ReleaseBundle."""

    if not bundle_resolution or bundle_resolution.get("bundle_attachment_mode") != "real_release_bundle_pinned":
        return None
    manifest = bundle_resolution.get("bundle_manifest") or {}
    state_dir = bundle_resolution.get("state_dir")
    if not state_dir:
        return None
    workspace = Workspace.open(Path(state_dir))
    evidence_binding_plan = _load_evidence_binding_plan(workspace, manifest)
    knowledge_projection = _load_first_ref(workspace, manifest.get("knowledge_projection_refs") or [])
    return {
        "schema_version": "bundle_runtime_policy.v1",
        "bundle_digest": bundle_resolution.get("bundle_digest"),
        "variant": manifest.get("variant"),
        "skill_family": manifest.get("skill_family"),
        "evidence_binding_plan": evidence_binding_plan,
        "required_evidence": required_evidence_from_plan(evidence_binding_plan),
        "decision_policy": dict(evidence_binding_plan.get("decision_policy", {})) if evidence_binding_plan else {},
        "knowledge_projection_policy": dict(knowledge_projection.get("knowledge_projection_policy", {}))
        if knowledge_projection
        else {},
        "knowledge_projection": knowledge_projection,
    }


def load_evidence_binding_plan_from_resolution(bundle_resolution: dict[str, Any] | None) -> dict[str, Any] | None:
    """Load the evidence policy pinned by a resolved ReleaseBundle.

    Partial/local-manifest-only executions keep the legacy default runtime policy.
    """

    policy = load_bundle_runtime_policy_from_resolution(bundle_resolution)
    if not policy:
        return None
    return policy["evidence_binding_plan"]


def _load_evidence_binding_plan(workspace: Workspace, manifest: dict[str, Any]) -> dict[str, Any] | None:
    access_binding = _load_first_ref(workspace, manifest.get("knowledge_access_binding_refs") or [])
    if not access_binding:
        return None
    evidence_ref_payload = access_binding.get("evidence_binding_plan_ref")
    if not evidence_ref_payload:
        return None
    return workspace.artifacts.get_json(ArtifactRef.from_dict(evidence_ref_payload))


def _load_first_ref(workspace: Workspace, refs: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not refs:
        return None
    return workspace.artifacts.get_json(ArtifactRef.from_dict(refs[0]))


def required_evidence_from_plan(plan: dict[str, Any] | None) -> list[str]:
    if not plan:
        return []
    return [str(item) for item in plan.get("required_evidence", [])]
