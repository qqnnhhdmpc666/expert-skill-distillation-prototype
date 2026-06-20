from __future__ import annotations

import re
import uuid
from dataclasses import replace
from typing import Any

from ..core.canonical import sha256_json
from ..core.models import ArtifactRef, EvidenceUnit, SourceSnapshot, StageResult
from ..registry.workspace import Workspace
from ..sources.adapters import SourceIngestionService
from .judge import IndependentJudge
from .models import CompilerBuild, KnowledgeIR, KnowledgeNode, KnowledgeProjection, SkillIR
from .validation import SourceGroundedValidator

NORMATIVE_PATTERN = re.compile(
    r"^\s*(?:[-*]|\d+[.)])?\s*(MUST NOT|MUST|SHOULD|MAY)\s+(?:(PROCEDURE|CONSTRAINT|CASE|PROPOSITION)\s*:\s*)?(.+?)\s*$",
    re.IGNORECASE,
)
UNSUPPORTED_PATTERN = re.compile(r"\[UNSUPPORTED\]\s*(.+)", re.IGNORECASE)


class KnowledgeCompiler:
    def __init__(
        self, workspace: Workspace, *, judge: IndependentJudge | None = None, require_judge: bool = False
    ) -> None:
        self.workspace = workspace
        self.validator = SourceGroundedValidator(judge=judge, require_judge=require_judge)

    def build(
        self,
        *,
        expert_snapshot: SourceSnapshot,
        structured_snapshots: tuple[SourceSnapshot, ...] = (),
        build_id: str | None = None,
    ) -> CompilerBuild:
        build_id = build_id or f"build-{uuid.uuid4()}"
        stages: list[dict[str, Any]] = []
        stage0 = self._stage(
            build_id,
            "stage-0-capture",
            input_refs=(),
            output_refs=(expert_snapshot.raw_artifact_ref,),
            metrics={"source_count": 1 + len(structured_snapshots)},
        )
        stages.append(stage0)

        evidence = self._load_evidence(expert_snapshot)
        stage1 = self._stage(
            build_id,
            "stage-1-segment",
            input_refs=(expert_snapshot.raw_artifact_ref,),
            output_refs=expert_snapshot.evidence_refs,
            metrics={"evidence_unit_count": len(evidence)},
        )
        stages.append(stage1)

        explicit, quarantine = self._extract_explicit(evidence)
        extracted_ref = self.workspace.put_json(
            {"nodes": [node.to_dict() for node in explicit], "quarantined": [node.to_dict() for node in quarantine]},
            schema_version="explicit_extraction.v1",
        )
        stages.append(
            self._stage(
                build_id,
                "stage-2-explicit-extraction",
                input_refs=expert_snapshot.evidence_refs,
                output_refs=(extracted_ref.to_dict(),),
                quarantined_item_refs=tuple({"node_id": node.node_id} for node in quarantine),
                metrics={"explicit_count": len(explicit), "quarantined_count": len(quarantine)},
                status="partial" if quarantine else "complete",
            )
        )

        bound, binding_quarantine = self._bind_evidence(explicit, evidence)
        quarantine.extend(binding_quarantine)
        bound_ref = self.workspace.put_json(
            {"nodes": [node.to_dict() for node in bound]}, schema_version="bound_knowledge_nodes.v1"
        )
        stages.append(
            self._stage(
                build_id,
                "stage-3-evidence-binding",
                input_refs=(extracted_ref.to_dict(),),
                output_refs=(bound_ref.to_dict(),),
                quarantined_item_refs=tuple({"node_id": node.node_id} for node in binding_quarantine),
                status="partial" if binding_quarantine else "complete",
            )
        )

        synthesized = self._synthesize(bound)
        knowledge_ir = KnowledgeIR(
            nodes=tuple(synthesized),
            quarantined_nodes=tuple(quarantine),
            source_snapshot_digests=(expert_snapshot.raw_artifact_ref["digest"],),
        )
        knowledge_ref = self.workspace.put_json(knowledge_ir.to_dict(), schema_version=knowledge_ir.schema_version)
        stages.append(
            self._stage(
                build_id,
                "stage-4-synthesis",
                input_refs=(bound_ref.to_dict(),),
                output_refs=(knowledge_ref.to_dict(),),
                metrics={"eligible_count": len(synthesized), "conflict_count": sum(n.validation_status == "disputed" for n in synthesized)},
            )
        )

        stages.append(
            self._stage(
                build_id,
                "stage-5-limited-induction",
                input_refs=(knowledge_ref.to_dict(),),
                output_refs=(knowledge_ref.to_dict(),),
                metrics={"induced_count": 0, "reason": "no_two_independent_build_cases"},
            )
        )

        dispositions = self._project_modalities(synthesized)
        disposition_ref = self.workspace.put_json(dispositions, schema_version="projection_decisions.v1")
        stages.append(
            self._stage(
                build_id,
                "stage-6-modality-projection",
                input_refs=(knowledge_ref.to_dict(),),
                output_refs=(disposition_ref.to_dict(),),
                metrics={"decision_count": len(dispositions)},
            )
        )

        skill_ir = self._compile_skill(synthesized, dispositions)
        skill_ref = self.workspace.put_json(skill_ir.to_dict(), schema_version=skill_ir.schema_version)
        stages.append(
            self._stage(
                build_id,
                "stage-7-skill-ir",
                input_refs=(knowledge_ref.to_dict(), disposition_ref.to_dict()),
                output_refs=(skill_ref.to_dict(),),
            )
        )

        projection = self._build_projection(synthesized, dispositions, expert_snapshot, structured_snapshots)
        projection_ref = self.workspace.put_json(projection.to_dict(), schema_version=projection.schema_version)
        stages.append(
            self._stage(
                build_id,
                "stage-8-knowledge-projection",
                input_refs=(knowledge_ref.to_dict(), *tuple(item.raw_artifact_ref for item in structured_snapshots)),
                output_refs=(projection_ref.to_dict(),),
            )
        )

        visibility = SourceIngestionService(self.workspace).build_visibility_manifest()
        visibility_ref = self.workspace.put_json(visibility, schema_version="source_visibility_manifest.v1")
        known_evidence = {unit.evidence_id: unit for unit in evidence}
        attestation = self.validator.validate(
            knowledge_ir=knowledge_ir,
            skill_ir=skill_ir,
            projection=projection,
            known_evidence=known_evidence,
            visibility_manifest=visibility,
            subject_digests={
                "knowledge_ir": knowledge_ref.digest,
                "skill_ir": skill_ref.digest,
                "knowledge_projection": projection_ref.digest,
            },
        )
        attestation_ref = self.workspace.put_json(attestation.to_dict(), schema_version=attestation.schema_version)
        stages.append(
            self._stage(
                build_id,
                "stage-9-source-grounded-validation",
                input_refs=(knowledge_ref.to_dict(), skill_ref.to_dict(), projection_ref.to_dict()),
                output_refs=(attestation_ref.to_dict(),),
                status="complete" if attestation.eligible_for_candidate else "rejected",
                metrics={"eligible_for_candidate": attestation.eligible_for_candidate},
                next_action="continue" if attestation.eligible_for_candidate else "stop",
            )
        )
        build = CompilerBuild(
            build_id=build_id,
            method="compiler_distilled_skill",
            stage_result_refs=tuple(stages),
            knowledge_ir_ref=knowledge_ref.to_dict(),
            skill_ir_ref=skill_ref.to_dict(),
            knowledge_projection_ref=projection_ref.to_dict(),
            attestation_ref=attestation_ref.to_dict(),
            visibility_manifest_ref=visibility_ref.to_dict(),
        )
        self.workspace.metadata.add_build_record(
            build_id=build_id,
            status="candidate" if attestation.eligible_for_candidate else "rejected",
            payload=build.to_dict(),
        )
        return build

    def _load_evidence(self, snapshot: SourceSnapshot) -> list[EvidenceUnit]:
        units: list[EvidenceUnit] = []
        for item in snapshot.evidence_refs:
            ref = ArtifactRef.from_dict(item)
            units.append(EvidenceUnit.from_dict(self.workspace.artifacts.get_json(ref)))
        return units

    @staticmethod
    def _extract_explicit(evidence: list[EvidenceUnit]) -> tuple[list[KnowledgeNode], list[KnowledgeNode]]:
        nodes: list[KnowledgeNode] = []
        quarantine: list[KnowledgeNode] = []
        for unit in evidence:
            for line in unit.content.splitlines():
                unsupported = UNSUPPORTED_PATTERN.search(line)
                if unsupported:
                    quarantine.append(
                        KnowledgeNode(
                            node_id=f"node-{sha256_json({'evidence': unit.evidence_id, 'line': line})[-16:]}",
                            semantic_type="proposition",
                            statement=unsupported.group(1).strip(),
                            modality="may",
                            evidence_refs=(),
                            quoted_support_spans=(),
                            scope_claim={"task_family": "python-advisory"},
                            validation_status="quarantined",
                            uncertainty="source marks this claim unsupported",
                        )
                    )
                    continue
                match = NORMATIVE_PATTERN.match(line)
                if not match:
                    continue
                modality_text, semantic_text, body = match.groups()
                modality = modality_text.casefold().replace(" ", "_")
                semantic_type = (semantic_text or ("procedure" if body.casefold().startswith(("query", "parse", "compare")) else "constraint")).casefold()
                statement = f"{modality_text.upper()} {body.strip()}"
                nodes.append(
                    KnowledgeNode(
                        node_id=f"node-{sha256_json({'evidence': unit.evidence_id, 'statement': statement})[-16:]}",
                        semantic_type=semantic_type,  # type: ignore[arg-type]
                        statement=statement,
                        modality=modality,  # type: ignore[arg-type]
                        evidence_refs=(
                            {
                                "evidence_id": unit.evidence_id,
                                "source_snapshot_digest": unit.source_snapshot_digest,
                                "locator": unit.locator,
                            },
                        ),
                        quoted_support_spans=(line.strip(),),
                        scope_claim={"task_family": "python-advisory"},
                    )
                )
        return nodes, quarantine

    @staticmethod
    def _bind_evidence(
        nodes: list[KnowledgeNode], evidence: list[EvidenceUnit]
    ) -> tuple[list[KnowledgeNode], list[KnowledgeNode]]:
        by_id = {unit.evidence_id: unit for unit in evidence}
        bound: list[KnowledgeNode] = []
        quarantine: list[KnowledgeNode] = []
        for node in nodes:
            valid = bool(node.evidence_refs)
            for ref in node.evidence_refs:
                unit = by_id.get(str(ref.get("evidence_id")))
                valid = valid and unit is not None and all(span in unit.content for span in node.quoted_support_spans)
            if valid:
                bound.append(node)
            else:
                quarantine.append(replace(node, validation_status="quarantined", uncertainty="binding_failure"))
        return bound, quarantine

    @staticmethod
    def _synthesize(nodes: list[KnowledgeNode]) -> list[KnowledgeNode]:
        unique: dict[tuple[str, str, str], KnowledgeNode] = {}
        for node in nodes:
            key = (node.semantic_type, node.modality, " ".join(node.statement.casefold().split()))
            if key not in unique:
                unique[key] = replace(node, derivation_mode="synthesized")
        synthesized = list(unique.values())
        by_body: dict[str, list[KnowledgeNode]] = {}
        for node in synthesized:
            body = re.sub(r"^(must not|must|should|may)\s+", "", node.statement.casefold()).strip()
            by_body.setdefault(body, []).append(node)
        result: list[KnowledgeNode] = []
        for node in synthesized:
            body = re.sub(r"^(must not|must|should|may)\s+", "", node.statement.casefold()).strip()
            peers = by_body[body]
            modalities = {peer.modality for peer in peers}
            if "must" in modalities and "must_not" in modalities:
                peer_ids = tuple(peer.node_id for peer in peers if peer.node_id != node.node_id)
                result.append(
                    replace(
                        node,
                        validation_status="disputed",
                        relations=tuple({"type": "contradicts", "target_node_id": peer_id} for peer_id in peer_ids),
                    )
                )
            else:
                result.append(node)
        return result

    @staticmethod
    def _project_modalities(nodes: list[KnowledgeNode]) -> list[dict[str, str]]:
        decisions: list[dict[str, str]] = []
        for node in nodes:
            dynamic = any(term in node.statement.casefold() for term in ("osv", "advisory record", "affected range", "version"))
            if node.validation_status != "eligible":
                disposition = "none"
            elif node.semantic_type == "case":
                disposition = "knowledge"
            elif dynamic:
                disposition = "both"
            else:
                disposition = "skill"
            decisions.append({"node_id": node.node_id, "disposition": disposition, "reason": "transparent_v1_rule"})
        return decisions

    @staticmethod
    def _compile_skill(nodes: list[KnowledgeNode], dispositions: list[dict[str, str]]) -> SkillIR:
        allowed = {item["node_id"] for item in dispositions if item["disposition"] in {"skill", "both"}}
        selected = [node for node in nodes if node.node_id in allowed]
        workflow = tuple(
            {"node_id": node.node_id, "instruction": node.statement, "modality": node.modality}
            for node in selected
            if node.semantic_type == "procedure"
        )
        constraints = tuple(
            {"node_id": node.node_id, "instruction": node.statement, "modality": node.modality}
            for node in selected
            if node.semantic_type in {"constraint", "proposition"}
        )
        knowledge_requirements = tuple(
            {
                "node_id": node.node_id,
                "semantic_requirement": "frozen_osv_advisory_and_affected_ranges",
                "unavailable_behavior": "abstain_unresolved",
            }
            for node in selected
            if any(term in node.statement.casefold() for term in ("osv", "advisory record", "affected range", "version"))
        )
        exceptions = tuple(item for item in constraints if item["modality"] == "must_not")
        return SkillIR(
            invocation={"task_family": "python-advisory", "contraindications": ["exploitability claim"]},
            workflow=workflow,
            constraints=constraints,
            knowledge_requirements=knowledge_requirements,
            exceptions=exceptions,
            source_node_ids=tuple(node.node_id for node in selected),
        )

    @staticmethod
    def _build_projection(
        nodes: list[KnowledgeNode],
        dispositions: list[dict[str, str]],
        expert_snapshot: SourceSnapshot,
        structured_snapshots: tuple[SourceSnapshot, ...],
    ) -> KnowledgeProjection:
        knowledge_ids = {item["node_id"] for item in dispositions if item["disposition"] in {"knowledge", "both"}}
        expert_refs = tuple(
            ref
            for node in nodes
            if node.node_id in knowledge_ids
            for ref in node.evidence_refs
        )
        return KnowledgeProjection(
            expert_evidence_refs=expert_refs or expert_snapshot.evidence_refs,
            structured_snapshot_refs=tuple(item.raw_artifact_ref for item in structured_snapshots),
            query_contracts=(
                {
                    "provider_id": "osv-snapshot-provider",
                    "query_type": "advisory_package",
                    "required_parameters": ["advisory_id"],
                },
            ),
            source_node_ids=tuple(sorted(knowledge_ids)),
        )

    def _stage(
        self,
        build_id: str,
        stage_id: str,
        *,
        input_refs: tuple[dict[str, Any], ...],
        output_refs: tuple[dict[str, Any], ...],
        quarantined_item_refs: tuple[dict[str, Any], ...] = (),
        metrics: dict[str, Any] | None = None,
        status: str = "complete",
        next_action: str = "continue",
    ) -> dict[str, Any]:
        result = StageResult(
            build_id=build_id,
            stage_id=stage_id,
            status=status,  # type: ignore[arg-type]
            input_refs=input_refs,
            output_refs=output_refs,
            quarantined_item_refs=quarantined_item_refs,
            metrics=metrics or {},
            next_action=next_action,  # type: ignore[arg-type]
        )
        return self.workspace.put_json(result.to_dict(), schema_version=result.SCHEMA_VERSION).to_dict()
