from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass(frozen=True)
class KnowledgeNode:
    node_id: str
    semantic_type: Literal["proposition", "procedure", "constraint", "case"]
    statement: str
    modality: Literal["must", "should", "may", "must_not"]
    evidence_refs: tuple[dict[str, Any], ...]
    quoted_support_spans: tuple[str, ...]
    scope_claim: dict[str, Any]
    derivation_mode: Literal["explicit", "synthesized", "induced", "hypothesized"] = "explicit"
    validation_status: Literal["eligible", "disputed", "quarantined"] = "eligible"
    relations: tuple[dict[str, str], ...] = ()
    uncertainty: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "semantic_type": self.semantic_type,
            "statement": self.statement,
            "modality": self.modality,
            "evidence_refs": list(self.evidence_refs),
            "quoted_support_spans": list(self.quoted_support_spans),
            "scope_claim": self.scope_claim,
            "derivation_mode": self.derivation_mode,
            "validation_status": self.validation_status,
            "relations": list(self.relations),
            "uncertainty": self.uncertainty,
        }


@dataclass(frozen=True)
class KnowledgeIR:
    schema_version: str = "knowledge_ir.v1"
    domain_id: str = "python-advisory"
    nodes: tuple[KnowledgeNode, ...] = ()
    quarantined_nodes: tuple[KnowledgeNode, ...] = ()
    source_snapshot_digests: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "domain_id": self.domain_id,
            "nodes": [node.to_dict() for node in self.nodes],
            "quarantined_nodes": [node.to_dict() for node in self.quarantined_nodes],
            "source_snapshot_digests": list(self.source_snapshot_digests),
        }


@dataclass(frozen=True)
class SkillIR:
    schema_version: str = "skill_ir.v1"
    skill_id: str = "python-advisory-review"
    version: str = "1.0.0"
    invocation: dict[str, Any] = field(default_factory=dict)
    workflow: tuple[dict[str, Any], ...] = ()
    constraints: tuple[dict[str, Any], ...] = ()
    knowledge_requirements: tuple[dict[str, Any], ...] = ()
    exceptions: tuple[dict[str, Any], ...] = ()
    source_node_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "skill_id": self.skill_id,
            "version": self.version,
            "invocation": self.invocation,
            "workflow": list(self.workflow),
            "constraints": list(self.constraints),
            "knowledge_requirements": list(self.knowledge_requirements),
            "exceptions": list(self.exceptions),
            "source_node_ids": list(self.source_node_ids),
        }


@dataclass(frozen=True)
class KnowledgeProjection:
    schema_version: str = "knowledge_projection.v1"
    projection_id: str = "python-advisory-knowledge"
    expert_evidence_refs: tuple[dict[str, Any], ...] = ()
    structured_snapshot_refs: tuple[dict[str, Any], ...] = ()
    query_contracts: tuple[dict[str, Any], ...] = ()
    source_node_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "projection_id": self.projection_id,
            "expert_evidence_refs": list(self.expert_evidence_refs),
            "structured_snapshot_refs": list(self.structured_snapshot_refs),
            "query_contracts": list(self.query_contracts),
            "source_node_ids": list(self.source_node_ids),
        }


@dataclass(frozen=True)
class BuildAttestation:
    schema_version: str = "build_attestation.v1"
    subject_digests: dict[str, str] = field(default_factory=dict)
    deterministic_status: Literal["pass", "fail"] = "fail"
    deterministic_findings: tuple[dict[str, Any], ...] = ()
    independent_judge_status: Literal["pass", "fail", "not_configured"] = "not_configured"
    independent_judge_findings: tuple[dict[str, Any], ...] = ()
    perturbation_status: Literal["pass", "fail"] = "fail"
    perturbation_results: tuple[dict[str, Any], ...] = ()
    heldout_visibility_status: Literal["pass", "fail"] = "fail"
    validation_profile: Literal["core-local", "formal-research"] = "core-local"
    judge_required: bool = False

    @property
    def eligible_for_candidate(self) -> bool:
        return (
            self.deterministic_status == "pass"
            and self.perturbation_status == "pass"
            and self.heldout_visibility_status == "pass"
            and (self.independent_judge_status == "pass" if self.judge_required else self.independent_judge_status != "fail")
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "subject_digests": self.subject_digests,
            "deterministic_status": self.deterministic_status,
            "deterministic_findings": list(self.deterministic_findings),
            "independent_judge_status": self.independent_judge_status,
            "independent_judge_findings": list(self.independent_judge_findings),
            "perturbation_status": self.perturbation_status,
            "perturbation_results": list(self.perturbation_results),
            "heldout_visibility_status": self.heldout_visibility_status,
            "validation_profile": self.validation_profile,
            "judge_required": self.judge_required,
            "eligible_for_candidate": self.eligible_for_candidate,
        }


@dataclass(frozen=True)
class CompilerBuild:
    build_id: str
    method: Literal["compiler_distilled_skill", "direct_to_skill_ir"]
    stage_result_refs: tuple[dict[str, Any], ...]
    knowledge_ir_ref: dict[str, Any] | None
    skill_ir_ref: dict[str, Any]
    knowledge_projection_ref: dict[str, Any] | None
    attestation_ref: dict[str, Any]
    visibility_manifest_ref: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "compiler_build.v1",
            "build_id": self.build_id,
            "method": self.method,
            "stage_result_refs": list(self.stage_result_refs),
            "knowledge_ir_ref": self.knowledge_ir_ref,
            "skill_ir_ref": self.skill_ir_ref,
            "knowledge_projection_ref": self.knowledge_projection_ref,
            "attestation_ref": self.attestation_ref,
            "visibility_manifest_ref": self.visibility_manifest_ref,
        }
