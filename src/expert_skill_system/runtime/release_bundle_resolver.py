from __future__ import annotations

from pathlib import Path
from typing import Any

from ..registry.workspace import Workspace
from .bundle import BundleBuilder


class BundleResolutionError(RuntimeError):
    pass


def resolve_release_bundle(
    *,
    state_dir: Path,
    bundle_digest: str | None = None,
    use_active_binding: bool = False,
    binding_key: str = "python-advisory",
    allow_local_manifest_only: bool = False,
    fail_on_partial_bundle: bool = False,
) -> dict[str, Any]:
    workspace = Workspace.open(state_dir)
    active_generation = None
    resolved_digest = bundle_digest
    resolution_source = "explicit_bundle_digest" if bundle_digest else None
    if resolved_digest is None and use_active_binding:
        active = workspace.metadata.get_active_binding(binding_key)
        if active is None:
            return _partial_or_failed(
                state_dir=state_dir,
                reason="bundle_not_available:no_active_binding",
                allow_local_manifest_only=allow_local_manifest_only,
                fail_on_partial_bundle=fail_on_partial_bundle,
            )
        resolved_digest = active.bundle_digest
        active_generation = active.generation
        resolution_source = "active_binding"
    if resolved_digest is None:
        return _partial_or_failed(
            state_dir=state_dir,
            reason="bundle_not_available:no_bundle_digest_or_active_binding_requested",
            allow_local_manifest_only=allow_local_manifest_only,
            fail_on_partial_bundle=fail_on_partial_bundle,
        )
    try:
        bundle = BundleBuilder(workspace).load(resolved_digest)
    except Exception as exc:
        return _partial_or_failed(
            state_dir=state_dir,
            reason=f"bundle_not_available:{type(exc).__name__}:{exc}",
            allow_local_manifest_only=allow_local_manifest_only,
            fail_on_partial_bundle=fail_on_partial_bundle,
        )
    manifest = bundle.manifest
    return {
        "schema_version": "release_bundle_resolution.v1",
        "bundle_attachment_mode": "real_release_bundle_pinned",
        "resolution_source": resolution_source,
        "bundle_digest": bundle.bundle_digest,
        "skill_digest": _first_digest(manifest.get("skill_ir_refs", [])),
        "skill_artifact_digest": _first_digest(manifest.get("agent_artifact_refs", [])),
        "knowledge_projection_digest": _first_digest(manifest.get("knowledge_projection_refs", [])),
        "knowledge_access_binding_digest": _first_digest(manifest.get("knowledge_access_binding_refs", [])),
        "provider_policy_digest": _digest_of_ref(manifest.get("provider_policy_ref")),
        "state_dir": str(state_dir),
        "active_binding_generation": active_generation,
        "limitation": "python-advisory bundle reused as initial system bundle for repo-level harness",
        "bundle_manifest": manifest,
    }


def _partial_or_failed(
    *, state_dir: Path, reason: str, allow_local_manifest_only: bool, fail_on_partial_bundle: bool
) -> dict[str, Any]:
    if not allow_local_manifest_only or fail_on_partial_bundle:
        raise BundleResolutionError(reason)
    return {
        "schema_version": "release_bundle_resolution.v1",
        "bundle_attachment_mode": "partial_local_manifest_only",
        "resolution_source": "allow_local_manifest_only",
        "bundle_digest": None,
        "skill_digest": None,
        "skill_artifact_digest": None,
        "knowledge_projection_digest": None,
        "knowledge_access_binding_digest": None,
        "provider_policy_digest": None,
        "state_dir": str(state_dir),
        "active_binding_generation": None,
        "limitation": reason,
        "bundle_manifest": {"mode": "partial_local_manifest_only", "reason": reason},
    }


def _first_digest(refs: list[dict[str, Any]]) -> str | None:
    if not refs:
        return None
    return _digest_of_ref(refs[0])


def _digest_of_ref(ref: dict[str, Any] | None) -> str | None:
    if not ref:
        return None
    return str(ref.get("digest")) if ref.get("digest") else None
