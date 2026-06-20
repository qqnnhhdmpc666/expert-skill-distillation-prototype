from __future__ import annotations

import uuid

from ..core.models import ArtifactRef, EvidenceUnit, SourceSnapshot, StageResult
from ..registry.workspace import Workspace
from ..sources.adapters import SourceIngestionService
from .models import CompilerBuild, KnowledgeIR, KnowledgeProjection
from .pipeline import KnowledgeCompiler
from .validation import SourceGroundedValidator


class DirectToSkillIRBuilder:
    """One-stage baseline producing the same Skill IR without reading compiler intermediates."""

    def __init__(self, workspace: Workspace) -> None:
        self.workspace = workspace
        self.validator = SourceGroundedValidator()

    def build(self, *, expert_snapshot: SourceSnapshot, build_id: str | None = None) -> CompilerBuild:
        build_id = build_id or f"direct-{uuid.uuid4()}"
        evidence = [
            EvidenceUnit.from_dict(self.workspace.artifacts.get_json(ArtifactRef.from_dict(item)))
            for item in expert_snapshot.evidence_refs
        ]
        explicit, _ = KnowledgeCompiler._extract_explicit(evidence)
        bound, _ = KnowledgeCompiler._bind_evidence(explicit, evidence)
        dispositions = KnowledgeCompiler._project_modalities(bound)
        skill_ir = KnowledgeCompiler._compile_skill(bound, dispositions)
        skill_ref = self.workspace.put_json(skill_ir.to_dict(), schema_version=skill_ir.schema_version)
        visibility = SourceIngestionService(self.workspace).build_visibility_manifest()
        visibility_ref = self.workspace.put_json(visibility, schema_version="source_visibility_manifest.v1")
        stage = StageResult(
            build_id=build_id,
            stage_id="direct-to-skill-ir-one-stage",
            input_refs=(expert_snapshot.raw_artifact_ref,),
            output_refs=(skill_ref.to_dict(),),
            metrics={"pipeline_stages": 1, "target_schema": skill_ir.schema_version},
        )
        stage_ref = self.workspace.put_json(stage.to_dict(), schema_version=stage.SCHEMA_VERSION)
        evaluator_ir = KnowledgeIR(nodes=tuple(bound), source_snapshot_digests=(expert_snapshot.raw_artifact_ref["digest"],))
        evaluator_projection = KnowledgeProjection(expert_evidence_refs=expert_snapshot.evidence_refs)
        attestation = self.validator.validate(
            knowledge_ir=evaluator_ir,
            skill_ir=skill_ir,
            projection=evaluator_projection,
            known_evidence={unit.evidence_id: unit for unit in evidence},
            visibility_manifest=visibility,
            subject_digests={"skill_ir": skill_ref.digest},
        )
        attestation_ref = self.workspace.put_json(attestation.to_dict(), schema_version=attestation.schema_version)
        build = CompilerBuild(
            build_id=build_id,
            method="direct_to_skill_ir",
            stage_result_refs=(stage_ref.to_dict(),),
            knowledge_ir_ref=None,
            skill_ir_ref=skill_ref.to_dict(),
            knowledge_projection_ref=None,
            attestation_ref=attestation_ref.to_dict(),
            visibility_manifest_ref=visibility_ref.to_dict(),
        )
        self.workspace.metadata.add_build_record(build_id=build_id, status="baseline", payload=build.to_dict())
        return build
