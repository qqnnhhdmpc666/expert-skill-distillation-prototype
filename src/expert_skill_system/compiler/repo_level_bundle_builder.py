from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..compiler.evidence_binding import bind_task_aware_evidence
from ..core.models import ArtifactRef, utc_now
from ..registry.workspace import Workspace
from ..runtime.bundle import BundleBuilder, ReleaseBundle

REPO_LEVEL_BINDING_KEY = "repo-dependency-use-triage"
REPO_LEVEL_SKILL_ID = "repo-dependency-use-triage"


@dataclass(frozen=True)
class RepoLevelBundleBuildResult:
    schema_version: str
    status: str
    skill_family: str
    bundle_digest: str
    skill_ir_digest: str
    agent_skill_artifact_digest: str
    knowledge_projection_digest: str
    knowledge_access_binding_digest: str
    evidence_binding_plan_digest: str
    provider_policy_digest: str
    dependency_manifest_digest: str
    variant: str
    active_binding_generation: int | None
    previous_python_advisory_bundle_digest: str | None
    bundle_digest_changed: bool | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "status": self.status,
            "skill_family": self.skill_family,
            "bundle_digest": self.bundle_digest,
            "skill_ir_digest": self.skill_ir_digest,
            "agent_skill_artifact_digest": self.agent_skill_artifact_digest,
            "knowledge_projection_digest": self.knowledge_projection_digest,
            "knowledge_access_binding_digest": self.knowledge_access_binding_digest,
            "evidence_binding_plan_digest": self.evidence_binding_plan_digest,
            "provider_policy_digest": self.provider_policy_digest,
            "dependency_manifest_digest": self.dependency_manifest_digest,
            "variant": self.variant,
            "active_binding_generation": self.active_binding_generation,
            "previous_python_advisory_bundle_digest": self.previous_python_advisory_bundle_digest,
            "bundle_digest_changed": self.bundle_digest_changed,
        }


class RepoLevelBundleBuilder:
    """Build a repo-level-specific ReleaseBundle without reusing python-advisory IR."""

    def __init__(self, workspace: Workspace) -> None:
        self.workspace = workspace

    def build(
        self,
        *,
        data_dir: Path,
        skill_family: str = REPO_LEVEL_SKILL_ID,
        promote: bool = False,
        variant: str = "default",
        evidence_policy: dict[str, Any] | None = None,
    ) -> RepoLevelBundleBuildResult:
        if skill_family != REPO_LEVEL_SKILL_ID:
            raise ValueError(f"unsupported repo-level skill_family: {skill_family!r}")
        expert_material = (data_dir / "expert_material.md").read_text(encoding="utf-8")
        task_contract = _read_json(data_dir / "task_contract.json")
        knowledge_contract = _read_json(data_dir / "knowledge_contract.json")
        required_evidence = list((evidence_policy or {}).get("required_evidence", task_contract["required_evidence"]))
        decision_policy = {
            "version_range_comparison_required": True,
            **dict((evidence_policy or {}).get("decision_policy", {})),
        }
        candidate_path_overrides = dict((evidence_policy or {}).get("candidate_path_overrides", {}))
        knowledge_projection_policy = {
            "allowed_advisory_fields": ["affected_ranges"],
            **dict((evidence_policy or {}).get("knowledge_projection_policy", {})),
        }
        task_contract = {**task_contract, "required_evidence": required_evidence}
        self._validate_contracts(
            task_contract,
            knowledge_contract,
            allow_incomplete_policy=evidence_policy is not None,
        )

        expert_ref = self.workspace.put_bytes(
            expert_material.encode("utf-8"),
            media_type="text/markdown",
            schema_version="repo_level_expert_material.v1",
            artifact_id="repo-level-dependency-use-triage-expert-material",
        )
        task_contract_ref = self.workspace.put_json(
            task_contract,
            schema_version=task_contract["schema_version"],
            artifact_id="repo-level-dependency-use-triage-task-contract",
        )
        knowledge_contract_ref = self.workspace.put_json(
            knowledge_contract,
            schema_version=knowledge_contract["schema_version"],
            artifact_id="repo-level-dependency-use-triage-knowledge-contract",
        )
        evidence_binding = bind_task_aware_evidence(
            {
                "task_type": "dependency_use_triage",
                "skill_requirements": task_contract["required_evidence"],
                "required_evidence": task_contract["required_evidence"],
                "decision_policy": decision_policy,
                "candidate_path_overrides": candidate_path_overrides,
                "available_knowledge_sources": ["task_allowed_advisory_snapshot"],
                "repo_manifest": {
                    "files": [
                        {"path": "requirements.txt"},
                        {"path": "pyproject.toml"},
                        {"path": "src/app/client.py"},
                    ]
                },
            }
        )
        evidence_binding_ref = self.workspace.put_json(
            evidence_binding,
            schema_version=evidence_binding["schema_version"],
            artifact_id="repo-level-dependency-use-triage-evidence-binding-plan",
        )
        knowledge_ir = self._knowledge_ir(
            source_refs=(expert_ref, task_contract_ref, knowledge_contract_ref, evidence_binding_ref),
            task_contract=task_contract,
            knowledge_contract=knowledge_contract,
            variant=variant,
            decision_policy=decision_policy,
            knowledge_projection_policy=knowledge_projection_policy,
        )
        knowledge_ir_ref = self.workspace.put_json(
            knowledge_ir,
            schema_version=knowledge_ir["schema_version"],
            artifact_id="repo-level-dependency-use-triage-knowledge-ir",
        )
        skill_ir = self._skill_ir(task_contract, variant=variant, decision_policy=decision_policy)
        skill_ir_ref = self.workspace.put_json(
            skill_ir,
            schema_version=skill_ir["schema_version"],
            artifact_id="repo-level-dependency-use-triage-skill-ir",
        )
        projection = self._knowledge_projection(
            task_contract_ref=task_contract_ref,
            knowledge_contract_ref=knowledge_contract_ref,
            evidence_binding_ref=evidence_binding_ref,
            knowledge_ir_ref=knowledge_ir_ref,
            knowledge_contract=knowledge_contract,
            knowledge_projection_policy=knowledge_projection_policy,
        )
        projection_ref = self.workspace.put_json(
            projection,
            schema_version=projection["schema_version"],
            artifact_id="repo-level-dependency-use-triage-knowledge-projection",
        )
        agent_ref = self.workspace.put_bytes(
            self._agent_artifact(skill_ir, evidence_binding).encode("utf-8"),
            media_type="text/markdown",
            schema_version="agent_skill_artifact.v1",
            artifact_id="repo-level-dependency-use-triage-agent-skill",
        )
        access_binding = {
            "schema_version": "knowledge_access_binding.v1",
            "binding_id": "repo-level-dependency-use-triage-task-snapshots",
            "projection_ref": projection_ref.to_dict(),
            "provider_id": "repo-level-task-snapshot-provider",
            "provider_version": "v1",
            "query_type": "repo_dependency_use_triage",
            "freshness_mode": "immutable_task_and_repo_snapshots",
            "on_unavailable": "abstain_or_fail_safe",
            "evidence_binding_plan_ref": evidence_binding_ref.to_dict(),
            "knowledge_projection_policy": knowledge_projection_policy,
        }
        access_ref = self.workspace.put_json(
            access_binding,
            schema_version=access_binding["schema_version"],
            artifact_id="repo-level-dependency-use-triage-access-binding",
        )
        static_refs = self._static_refs()
        provenance_ref = self.workspace.put_json(
            {
                "schema_version": "bundle_provenance.v1",
                "build_mode": "repo_level_specific_static_compiler",
                "variant": variant,
                "expert_material_ref": expert_ref.to_dict(),
                "task_contract_ref": task_contract_ref.to_dict(),
                "knowledge_contract_ref": knowledge_contract_ref.to_dict(),
                "evidence_binding_plan_ref": evidence_binding_ref.to_dict(),
                "knowledge_ir_ref": knowledge_ir_ref.to_dict(),
                "skill_ir_ref": skill_ir_ref.to_dict(),
                "knowledge_projection_ref": projection_ref.to_dict(),
                "claim_boundary": task_contract["claim_boundary"],
            },
            schema_version="bundle_provenance.v1",
            artifact_id="repo-level-dependency-use-triage-provenance",
        )
        hard_refs = [
            expert_ref.to_dict(),
            task_contract_ref.to_dict(),
            knowledge_contract_ref.to_dict(),
            evidence_binding_ref.to_dict(),
            knowledge_ir_ref.to_dict(),
            skill_ir_ref.to_dict(),
            projection_ref.to_dict(),
            agent_ref.to_dict(),
            access_ref.to_dict(),
            provenance_ref.to_dict(),
            *(ref.to_dict() for ref in static_refs.values()),
        ]
        dependency_ref = self.workspace.put_json(
            {
                "schema_version": "dependency_manifest.v1",
                "hard_runtime_dependencies": hard_refs,
                "edge_direction": "dependent_ref_requires_dependency_ref",
            },
            schema_version="dependency_manifest.v1",
            artifact_id="repo-level-dependency-use-triage-dependency-manifest",
        )
        manifest = {
            "schema_version": "release_bundle.v1",
            "skill_family": skill_family,
            "variant": variant,
            "compatible_agent_profiles": ["repo-level-dependency-use-triage-v1"],
            "knowledge_ir_ref": knowledge_ir_ref.to_dict(),
            "skill_ir_refs": [skill_ir_ref.to_dict()],
            "agent_artifact_refs": [agent_ref.to_dict()],
            "knowledge_projection_refs": [projection_ref.to_dict()],
            "knowledge_access_binding_refs": [access_ref.to_dict()],
            "promotion_verifier_binding_refs": [static_refs["promotion_verifier_binding_ref"].to_dict()],
            "runtime_verifier_binding_refs": [static_refs["runtime_verifier_binding_ref"].to_dict()],
            "domain_adapter_ref": static_refs["domain_adapter_ref"].to_dict(),
            "runtime_compiler_ref": static_refs["runtime_compiler_ref"].to_dict(),
            "domain_primitive_refs": [evidence_binding_ref.to_dict()],
            "provider_adapter_refs": [],
            "schema_bundle_ref": static_refs["schema_bundle_ref"].to_dict(),
            "provider_policy_ref": static_refs["provider_policy_ref"].to_dict(),
            "permission_request_ref": static_refs["permission_request_ref"].to_dict(),
            "provenance_manifest_ref": provenance_ref.to_dict(),
            "dependency_manifest_ref": dependency_ref.to_dict(),
        }
        manifest_ref = self.workspace.put_json(
            manifest,
            schema_version="release_bundle.v1",
            artifact_id="repo-level-dependency-use-triage-release-bundle",
        )
        bundle = ReleaseBundle(bundle_digest=manifest_ref.digest, manifest_ref=manifest_ref, manifest=manifest)
        BundleBuilder(self.workspace)._verify_closure(manifest)
        self.workspace.metadata.add_build_record(
            build_id=f"repo-level-bundle-{manifest_ref.digest[-12:]}",
            status="candidate",
            payload={
                "schema_version": "repo_level_bundle_build.v1",
                "method": "repo_level_specific_static_compiler",
                "variant": variant,
                "skill_family": skill_family,
                "knowledge_ir_ref": knowledge_ir_ref.to_dict(),
                "skill_ir_ref": skill_ir_ref.to_dict(),
                "knowledge_projection_ref": projection_ref.to_dict(),
                "evidence_binding_plan_ref": evidence_binding_ref.to_dict(),
                "created_at": utc_now(),
            },
            candidate_bundle_digest=bundle.bundle_digest,
        )
        previous_python = self.workspace.metadata.get_active_binding("python-advisory")
        active_generation = None
        if promote:
            current = self.workspace.metadata.get_active_binding(skill_family)
            expected_generation = current.generation if current else 0
            active = self.workspace.metadata.change_binding(
                binding_key=skill_family,
                target_digest=bundle.bundle_digest,
                expected_generation=expected_generation,
                event_type="promote",
                reason_codes=("REPO_LEVEL_SPECIFIC_BUNDLE_BUILD_PASS",),
            )
            active_generation = active.generation
        return RepoLevelBundleBuildResult(
            schema_version="repo_level_bundle_build_result.v1",
            status="pass",
            skill_family=skill_family,
            bundle_digest=bundle.bundle_digest,
            skill_ir_digest=skill_ir_ref.digest,
            agent_skill_artifact_digest=agent_ref.digest,
            knowledge_projection_digest=projection_ref.digest,
            knowledge_access_binding_digest=access_ref.digest,
            evidence_binding_plan_digest=evidence_binding_ref.digest,
            provider_policy_digest=static_refs["provider_policy_ref"].digest,
            dependency_manifest_digest=dependency_ref.digest,
            variant=variant,
            active_binding_generation=active_generation,
            previous_python_advisory_bundle_digest=previous_python.bundle_digest if previous_python else None,
            bundle_digest_changed=(bundle.bundle_digest != previous_python.bundle_digest) if previous_python else None,
        )

    @staticmethod
    def _validate_contracts(
        task_contract: dict[str, Any],
        knowledge_contract: dict[str, Any],
        *,
        allow_incomplete_policy: bool = False,
    ) -> None:
        if task_contract.get("skill_family") != REPO_LEVEL_SKILL_ID:
            raise ValueError("task_contract skill_family must be repo-dependency-use-triage")
        if task_contract.get("task_type") != "dependency_use_triage":
            raise ValueError("task_contract task_type must be dependency_use_triage")
        if knowledge_contract.get("skill_family") != REPO_LEVEL_SKILL_ID:
            raise ValueError("knowledge_contract skill_family must match task_contract")
        required = {
            "dependency_declaration",
            "resolved_version",
            "import_use_site",
            "advisory_affected_range",
            "decision_evidence",
        }
        actual_required = set(task_contract.get("required_evidence", []))
        if allow_incomplete_policy:
            unknown = sorted(actual_required - required)
            if unknown:
                raise ValueError(f"task_contract required_evidence has unsupported values: {unknown}")
            if "decision_evidence" not in actual_required:
                raise ValueError("task_contract required_evidence must include decision_evidence")
        elif actual_required != required:
            raise ValueError("task_contract required_evidence must match dependency-use triage requirements")

    @staticmethod
    def _knowledge_ir(
        *,
        source_refs: tuple[ArtifactRef, ...],
        task_contract: dict[str, Any],
        knowledge_contract: dict[str, Any],
        variant: str,
        decision_policy: dict[str, Any],
        knowledge_projection_policy: dict[str, Any],
    ) -> dict[str, Any]:
        required_evidence_text = ", ".join(task_contract["required_evidence"])
        return {
            "schema_version": "knowledge_ir.v1",
            "domain_id": REPO_LEVEL_SKILL_ID,
            "variant": variant,
            "decision_policy": decision_policy,
            "knowledge_projection_policy": knowledge_projection_policy,
            "nodes": [
                {
                    "node_id": "repo-triage-skill-knowledge-boundary",
                    "semantic_type": "constraint",
                    "statement": "Stable workflow belongs to Skill; concrete advisory and repository evidence remain runtime knowledge.",
                    "modality": "must",
                    "evidence_refs": [ref.to_dict() for ref in source_refs],
                    "quoted_support_spans": ["Skill = stable workflow / constraints / abstention policy"],
                    "scope_claim": {"task_type": task_contract["task_type"]},
                    "derivation_mode": "explicit",
                    "validation_status": "eligible",
                    "relations": [],
                    "uncertainty": None,
                },
                {
                    "node_id": "repo-triage-required-evidence",
                    "semantic_type": "procedure",
                    "statement": f"A valid decision requires: {required_evidence_text}.",
                    "modality": "must",
                    "evidence_refs": [ref.to_dict() for ref in source_refs],
                    "quoted_support_spans": task_contract["required_evidence"],
                    "scope_claim": {"task_type": task_contract["task_type"]},
                    "derivation_mode": "explicit",
                    "validation_status": "eligible",
                    "relations": [],
                    "uncertainty": None,
                },
                {
                    "node_id": "repo-triage-knowledge-access",
                    "semantic_type": "constraint",
                    "statement": "Runtime knowledge access is limited to immutable task advisory and repository snapshots.",
                    "modality": "must",
                    "evidence_refs": [ref.to_dict() for ref in source_refs],
                    "quoted_support_spans": knowledge_contract["knowledge_owned_facts"],
                    "scope_claim": {"task_type": task_contract["task_type"]},
                    "derivation_mode": "explicit",
                    "validation_status": "eligible",
                    "relations": [],
                    "uncertainty": None,
                },
            ],
            "quarantined_nodes": [],
            "source_snapshot_digests": [ref.digest for ref in source_refs],
        }

    @staticmethod
    def _skill_ir(task_contract: dict[str, Any], *, variant: str, decision_policy: dict[str, Any]) -> dict[str, Any]:
        required = set(task_contract["required_evidence"])
        workflow = [
            {"step_id": "identify_declaration", "instruction": "Identify dependency declaration evidence."},
            {"step_id": "identify_version", "instruction": "Identify resolved version or lock/version evidence."},
        ]
        if "import_use_site" in required:
            workflow.append({"step_id": "identify_use", "instruction": "Identify import/use evidence in repo files."})
        workflow.extend(
            [
                {"step_id": "consult_advisory", "instruction": "Consult only the allowed advisory snapshot."},
                {"step_id": "compare_range", "instruction": "Compare resolved version against affected range."},
                {"step_id": "decide", "instruction": "Emit one bounded dependency-use triage decision with evidence."},
            ]
        )
        constraints = [
            {"constraint_id": "no_advisory_only_decision", "instruction": "Never decide affectedness from advisory evidence alone."},
            {"constraint_id": "fail_safe_missing_evidence", "instruction": "Abstain or fail safe when required repo evidence is insufficient."},
            {"constraint_id": "no_exploitability_claim", "instruction": "Do not claim exploitability, reachability, or general vulnerability discovery."},
        ]
        exceptions = []
        if "import_use_site" in required:
            exceptions.append(
                {
                    "exception_id": "missing_import_use_site",
                    "instruction": "Missing import/use evidence must not produce dependency_used_and_affected.",
                }
            )
        return {
            "schema_version": "skill_ir.v1",
            "skill_id": REPO_LEVEL_SKILL_ID,
            "version": "1.0.0",
            "variant": variant,
            "decision_policy": decision_policy,
            "invocation": {"task_family": REPO_LEVEL_SKILL_ID, "task_type": task_contract["task_type"]},
            "workflow": workflow,
            "constraints": constraints,
            "knowledge_requirements": [
                {
                    "semantic_requirement": evidence_type,
                    "unavailable_behavior": "abstain_or_fail_safe",
                }
                for evidence_type in task_contract["required_evidence"]
            ],
            "exceptions": exceptions,
            "source_node_ids": [
                "repo-triage-skill-knowledge-boundary",
                "repo-triage-required-evidence",
                "repo-triage-knowledge-access",
            ],
        }

    @staticmethod
    def _knowledge_projection(
        *,
        task_contract_ref: ArtifactRef,
        knowledge_contract_ref: ArtifactRef,
        evidence_binding_ref: ArtifactRef,
        knowledge_ir_ref: ArtifactRef,
        knowledge_contract: dict[str, Any],
        knowledge_projection_policy: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "schema_version": "knowledge_projection.v1",
            "projection_id": "repo-level-dependency-use-triage-knowledge",
            "knowledge_projection_policy": knowledge_projection_policy,
            "expert_evidence_refs": [task_contract_ref.to_dict(), knowledge_contract_ref.to_dict()],
            "structured_snapshot_refs": [task_contract_ref.to_dict(), knowledge_contract_ref.to_dict(), evidence_binding_ref.to_dict()],
            "query_contracts": knowledge_contract["query_contracts"],
            "source_node_ids": [
                "repo-triage-skill-knowledge-boundary",
                "repo-triage-required-evidence",
                "repo-triage-knowledge-access",
            ],
            "knowledge_ir_ref": knowledge_ir_ref.to_dict(),
        }

    def _static_refs(self) -> dict[str, ArtifactRef]:
        return {
            "domain_adapter_ref": self.workspace.put_json(
                {"schema_version": "domain_adapter.v1", "adapter": "repo-level-dependency-use-triage"},
                schema_version="domain_adapter.v1",
                artifact_id="repo-level-dependency-use-triage-domain-adapter",
            ),
            "runtime_compiler_ref": self.workspace.put_json(
                {"schema_version": "runtime_compiler.v1", "compiler": "deterministic-repo-level-dependency-use-triage"},
                schema_version="runtime_compiler.v1",
                artifact_id="repo-level-dependency-use-triage-runtime-compiler",
            ),
            "schema_bundle_ref": self.workspace.put_json(
                {
                    "schema_version": "schema_bundle.v1",
                    "schemas": ["release_bundle.v1", "repo_security_prediction.v1", "evidence_binding_plan.v1"],
                },
                schema_version="schema_bundle.v1",
                artifact_id="repo-level-dependency-use-triage-schema-bundle",
            ),
            "provider_policy_ref": self.workspace.put_json(
                {
                    "schema_version": "provider_policy.v1",
                    "live_query": False,
                    "memory_fallback": False,
                    "allowed_runtime_sources": ["task_allowed_knowledge", "task_repo_snapshot"],
                },
                schema_version="provider_policy.v1",
                artifact_id="repo-level-dependency-use-triage-provider-policy",
            ),
            "permission_request_ref": self.workspace.put_json(
                {"schema_version": "permission_request.v1", "filesystem": "read_declared_task_inputs", "network": "none"},
                schema_version="permission_request.v1",
                artifact_id="repo-level-dependency-use-triage-permission-request",
            ),
            "runtime_verifier_binding_ref": self.workspace.put_json(
                {"schema_version": "verifier_binding.v1", "verifier": "repo-dependency-use-triage-deterministic-v1"},
                schema_version="verifier_binding.v1",
                artifact_id="repo-level-dependency-use-triage-runtime-verifier",
            ),
            "promotion_verifier_binding_ref": self.workspace.put_json(
                {"schema_version": "verifier_binding.v1", "verifier": "repo-level-bundle-promotion-v1"},
                schema_version="verifier_binding.v1",
                artifact_id="repo-level-dependency-use-triage-promotion-verifier",
            ),
        }

    @staticmethod
    def _agent_artifact(skill_ir: dict[str, Any], evidence_binding: dict[str, Any]) -> str:
        lines = ["# Repo-Level Dependency-Use Triage", "", "## Workflow"]
        lines.extend(f"- {item['instruction']}" for item in skill_ir["workflow"])
        lines.extend(["", "## Constraints"])
        lines.extend(f"- {item['instruction']}" for item in skill_ir["constraints"])
        lines.extend(["", "## Required Evidence"])
        lines.extend(f"- {item}" for item in evidence_binding["required_evidence"])
        lines.extend(["", "## Missing Evidence Policy", "- abstain_or_fail_safe"])
        return "\n".join(lines).rstrip() + "\n"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
