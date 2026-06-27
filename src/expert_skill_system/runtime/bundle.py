from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..compiler.models import CompilerBuild
from ..core.models import ArtifactRef
from ..registry.workspace import Workspace


@dataclass(frozen=True)
class ReleaseBundle:
    bundle_digest: str
    manifest_ref: ArtifactRef
    manifest: dict[str, Any]


class BundleBuilder:
    def __init__(self, workspace: Workspace) -> None:
        self.workspace = workspace

    def build(self, compiler_build: CompilerBuild) -> ReleaseBundle:
        if compiler_build.knowledge_ir_ref is None or compiler_build.knowledge_projection_ref is None:
            raise ValueError("a ReleaseBundle requires the compiler-distilled Knowledge IR and projection")
        skill_ir = self.workspace.artifacts.get_json(ArtifactRef.from_dict(compiler_build.skill_ir_ref))
        projection = self.workspace.artifacts.get_json(ArtifactRef.from_dict(compiler_build.knowledge_projection_ref))
        agent_text = self._compile_agent_artifact(skill_ir)
        agent_ref = self.workspace.put_bytes(
            agent_text.encode("utf-8"), media_type="text/markdown", schema_version="agent_skill_artifact.v1"
        )
        snapshot_refs = projection.get("structured_snapshot_refs", [])
        if not snapshot_refs:
            raise ValueError("knowledge projection has no frozen structured snapshot")
        snapshot_ref = ArtifactRef.from_dict(snapshot_refs[0])
        index_ref = self._find_osv_index_ref(snapshot_ref.digest)
        access_binding = {
            "schema_version": "knowledge_access_binding.v1",
            "binding_id": "python-advisory-osv-snapshot",
            "projection_ref": compiler_build.knowledge_projection_ref,
            "provider_id": "osv-snapshot-provider",
            "provider_version": "v1",
            "snapshot_ref": snapshot_ref.to_dict(),
            "native_index_ref": index_ref.to_dict(),
            "query_type": "advisory_package",
            "freshness_mode": "immutable_snapshot",
            "on_unavailable": "block",
        }
        access_ref = self.workspace.put_json(access_binding, schema_version="knowledge_access_binding.v1")
        static_artifacts = {
            "domain_adapter_ref": self.workspace.put_json(
                {"schema_version": "domain_adapter.v1", "adapter": "python-advisory"}, schema_version="domain_adapter.v1"
            ),
            "runtime_compiler_ref": self.workspace.put_json(
                {"schema_version": "runtime_compiler.v1", "compiler": "deterministic-python-advisory"},
                schema_version="runtime_compiler.v1",
            ),
            "schema_bundle_ref": self.workspace.put_json(
                {"schema_version": "schema_bundle.v1", "schemas": ["release_bundle.v1", "python_advisory_outcome.v1"]},
                schema_version="schema_bundle.v1",
            ),
            "provider_policy_ref": self.workspace.put_json(
                {"schema_version": "provider_policy.v1", "live_query": False, "memory_fallback": False},
                schema_version="provider_policy.v1",
            ),
            "permission_request_ref": self.workspace.put_json(
                {"schema_version": "permission_request.v1", "filesystem": "read_declared_inputs", "network": "none"},
                schema_version="permission_request.v1",
            ),
            "runtime_verifier_binding_ref": self.workspace.put_json(
                {"schema_version": "verifier_binding.v1", "verifier": "python-advisory-deterministic-v1"},
                schema_version="verifier_binding.v1",
            ),
            "promotion_verifier_binding_ref": self.workspace.put_json(
                {"schema_version": "verifier_binding.v1", "verifier": "bundle-promotion-v1"},
                schema_version="verifier_binding.v1",
            ),
        }
        provenance_ref = self.workspace.put_json(
            {
                "schema_version": "bundle_provenance.v1",
                "knowledge_ir_ref": compiler_build.knowledge_ir_ref,
                "skill_ir_ref": compiler_build.skill_ir_ref,
                "knowledge_projection_ref": compiler_build.knowledge_projection_ref,
            },
            schema_version="bundle_provenance.v1",
        )
        hard_refs = [
            compiler_build.knowledge_ir_ref,
            compiler_build.skill_ir_ref,
            compiler_build.knowledge_projection_ref,
            agent_ref.to_dict(),
            access_ref.to_dict(),
            snapshot_ref.to_dict(),
            index_ref.to_dict(),
            provenance_ref.to_dict(),
            *(ref.to_dict() for ref in static_artifacts.values()),
        ]
        dependency_ref = self.workspace.put_json(
            {
                "schema_version": "dependency_manifest.v1",
                "hard_runtime_dependencies": hard_refs,
                "edge_direction": "dependent_ref_requires_dependency_ref",
            },
            schema_version="dependency_manifest.v1",
        )
        manifest = {
            "schema_version": "release_bundle.v1",
            "skill_family": "python_advisory_applicability",
            "compatible_agent_profiles": ["reference-decision-v1"],
            "knowledge_ir_ref": compiler_build.knowledge_ir_ref,
            "skill_ir_refs": [compiler_build.skill_ir_ref],
            "agent_artifact_refs": [agent_ref.to_dict()],
            "knowledge_projection_refs": [compiler_build.knowledge_projection_ref],
            "knowledge_access_binding_refs": [access_ref.to_dict()],
            "promotion_verifier_binding_refs": [static_artifacts["promotion_verifier_binding_ref"].to_dict()],
            "runtime_verifier_binding_refs": [static_artifacts["runtime_verifier_binding_ref"].to_dict()],
            "domain_adapter_ref": static_artifacts["domain_adapter_ref"].to_dict(),
            "runtime_compiler_ref": static_artifacts["runtime_compiler_ref"].to_dict(),
            "domain_primitive_refs": [],
            "provider_adapter_refs": [index_ref.to_dict()],
            "schema_bundle_ref": static_artifacts["schema_bundle_ref"].to_dict(),
            "provider_policy_ref": static_artifacts["provider_policy_ref"].to_dict(),
            "permission_request_ref": static_artifacts["permission_request_ref"].to_dict(),
            "provenance_manifest_ref": provenance_ref.to_dict(),
            "dependency_manifest_ref": dependency_ref.to_dict(),
        }
        manifest_ref = self.workspace.put_json(manifest, schema_version="release_bundle.v1")
        self._verify_closure(manifest)
        build_record = self.workspace.metadata.get_build_record(compiler_build.build_id)
        self.workspace.metadata.add_build_record(
            build_id=compiler_build.build_id,
            status=build_record["status"],
            payload=build_record["payload"],
            candidate_bundle_digest=manifest_ref.digest,
        )
        return ReleaseBundle(bundle_digest=manifest_ref.digest, manifest_ref=manifest_ref, manifest=manifest)

    def load(self, bundle_digest: str) -> ReleaseBundle:
        ref = self.workspace.metadata.artifact_ref(bundle_digest)
        if ref.artifact_schema_version != "release_bundle.v1":
            raise ValueError("binding target is not a ReleaseBundle manifest")
        manifest = self.workspace.artifacts.get_json(ref)
        self._verify_closure(manifest)
        return ReleaseBundle(bundle_digest=bundle_digest, manifest_ref=ref, manifest=manifest)

    def _verify_closure(self, manifest: dict[str, Any]) -> None:
        dependency_ref = ArtifactRef.from_dict(manifest["dependency_manifest_ref"])
        dependencies = self.workspace.artifacts.get_json(dependency_ref)
        for payload in dependencies["hard_runtime_dependencies"]:
            ref = ArtifactRef.from_dict(payload)
            if not self.workspace.artifacts.contains(ref):
                raise FileNotFoundError(f"bundle hard dependency unavailable: {ref.digest}")

    def _find_osv_index_ref(self, snapshot_digest: str) -> ArtifactRef:
        for item in self.workspace.metadata.source_snapshots():
            if item["metadata"].get("source_content_digest") != snapshot_digest:
                continue
            snapshot_ref = self.workspace.metadata.artifact_ref(item["snapshot_digest"])
            snapshot = self.workspace.artifacts.get_json(snapshot_ref)
            native_refs = snapshot.get("native_index_refs", [])
            if native_refs:
                return ArtifactRef.from_dict(native_refs[0])
        raise KeyError(f"OSV native index not found for {snapshot_digest}")

    @staticmethod
    def _compile_agent_artifact(skill_ir: dict[str, Any]) -> str:
        lines = ["# Python Advisory Applicability", "", "## Workflow"]
        lines.extend(f"- {item['instruction']}" for item in skill_ir.get("workflow", []))
        lines.extend(["", "## Constraints"])
        lines.extend(f"- {item['instruction']}" for item in skill_ir.get("constraints", []))
        lines.extend(["", "## Knowledge Requirements"])
        lines.extend(
            f"- {item['semantic_requirement']}; unavailable: {item['unavailable_behavior']}"
            for item in skill_ir.get("knowledge_requirements", [])
        )
        return "\n".join(lines).rstrip() + "\n"
