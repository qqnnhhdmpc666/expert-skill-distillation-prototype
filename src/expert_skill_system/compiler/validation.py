from __future__ import annotations

from dataclasses import replace
from typing import Any

from ..core.canonical import sha256_json
from ..core.models import EvidenceUnit
from .judge import IndependentJudge
from .models import BuildAttestation, KnowledgeIR, KnowledgeNode, KnowledgeProjection, SkillIR


class SourceGroundedValidator:
    def __init__(self, *, judge: IndependentJudge | None = None, require_judge: bool = False) -> None:
        self.judge = judge
        self.require_judge = require_judge

    def validate(
        self,
        *,
        knowledge_ir: KnowledgeIR,
        skill_ir: SkillIR,
        projection: KnowledgeProjection,
        known_evidence: dict[str, EvidenceUnit],
        visibility_manifest: dict[str, Any],
        subject_digests: dict[str, str],
    ) -> BuildAttestation:
        findings = self._deterministic_findings(knowledge_ir, skill_ir, known_evidence)
        perturbations = self._run_perturbations(knowledge_ir, skill_ir, known_evidence)
        heldout_ok = (
            visibility_manifest.get("heldout_in_build_closure") is False
            and not any("heldout" in digest for digest in visibility_manifest.get("visible_snapshot_digests", []))
        )
        if self.judge is None:
            judge_status = "not_configured"
            judge_findings = (
                {
                    "code": "independent_llm_judge_not_configured",
                    "note": "This is automated deterministic evidence, not a human expert evaluation.",
                },
            )
        else:
            judge_result = self.judge.evaluate(knowledge_ir, skill_ir)
            judge_status = judge_result.status
            judge_findings = (*judge_result.findings, {"provenance": judge_result.provenance})
        return BuildAttestation(
            subject_digests=subject_digests,
            deterministic_status="pass" if not findings else "fail",
            deterministic_findings=tuple(findings),
            independent_judge_status=judge_status,  # type: ignore[arg-type]
            independent_judge_findings=judge_findings,
            perturbation_status="pass" if all(item["detected"] for item in perturbations) else "fail",
            perturbation_results=tuple(perturbations),
            heldout_visibility_status="pass" if heldout_ok else "fail",
            validation_profile="formal-research" if self.require_judge else "core-local",
            judge_required=self.require_judge,
        )

    def _deterministic_findings(
        self, knowledge_ir: KnowledgeIR, skill_ir: SkillIR, known_evidence: dict[str, EvidenceUnit]
    ) -> list[dict[str, Any]]:
        findings: list[dict[str, Any]] = []
        eligible_ids = {node.node_id for node in knowledge_ir.nodes if node.validation_status == "eligible"}
        for node in knowledge_ir.nodes:
            if not node.evidence_refs:
                findings.append({"code": "missing_evidence", "node_id": node.node_id})
            for ref in node.evidence_refs:
                evidence_id = str(ref.get("evidence_id"))
                if evidence_id not in known_evidence:
                    findings.append({"code": "broken_evidence_ref", "node_id": node.node_id})
                    continue
                unit = known_evidence[evidence_id]
                source = unit.content
                if ref.get("source_snapshot_digest") != unit.source_snapshot_digest:
                    findings.append({"code": "evidence_digest_mismatch", "node_id": node.node_id})
                if not all(span in source for span in node.quoted_support_spans):
                    findings.append({"code": "invalid_support_span", "node_id": node.node_id})
                source_modality = _source_modality("\n".join(node.quoted_support_spans))
                if source_modality is not None and source_modality != node.modality:
                    findings.append({"code": "modality_mismatch", "node_id": node.node_id})
            if not node.quoted_support_spans:
                findings.append({"code": "invalid_support_span", "node_id": node.node_id})
            if node.scope_claim.get("task_family") not in {None, "python-advisory"}:
                findings.append({"code": "scope_overreach", "node_id": node.node_id})
            if node.scope_claim.get("freshness") == "stale":
                findings.append({"code": "stale_rule", "node_id": node.node_id})
        unknown_source_nodes = set(skill_ir.source_node_ids) - eligible_ids
        if unknown_source_nodes:
            findings.append({"code": "skill_uses_ineligible_node", "node_ids": sorted(unknown_source_nodes)})
        must_not_ids = {
            item["node_id"] for item in skill_ir.constraints if item.get("modality") == "must_not"
        }
        exception_ids = {item["node_id"] for item in skill_ir.exceptions}
        if not must_not_ids.issubset(exception_ids):
            findings.append({"code": "missing_exception", "node_ids": sorted(must_not_ids - exception_ids)})
        serialized_skill = str(skill_ir.to_dict())
        if "PYSEC-" in serialized_skill or "GHSA-" in serialized_skill:
            findings.append({"code": "dynamic_advisory_embedded_in_skill"})
        return findings

    def _run_perturbations(
        self, knowledge_ir: KnowledgeIR, skill_ir: SkillIR, known_evidence: dict[str, EvidenceUnit]
    ) -> list[dict[str, Any]]:
        if not knowledge_ir.nodes:
            return [{"name": "fixture_available", "detected": False}]
        node = knowledge_ir.nodes[0]
        cases: list[tuple[str, KnowledgeNode]] = [
            ("missing_evidence", replace(node, evidence_refs=())),
            ("broken_reference", replace(node, evidence_refs=({"evidence_id": "missing"},))),
            (
                "digest_mismatch",
                replace(
                    node,
                    evidence_refs=tuple(
                        {**ref, "source_snapshot_digest": "sha256:" + "f" * 64} for ref in node.evidence_refs
                    ),
                ),
            ),
            ("scope_overreach", replace(node, scope_claim={"task_family": "all-security"})),
            ("modality_mismatch", replace(node, modality="may" if node.modality == "must" else "must")),
            ("stale_rule", replace(node, scope_claim={**node.scope_claim, "freshness": "stale"})),
            ("unresolved_conflict", replace(node, validation_status="disputed")),
        ]
        results: list[dict[str, Any]] = []
        for name, mutated in cases:
            mutated_ir = replace(knowledge_ir, nodes=(mutated, *knowledge_ir.nodes[1:]))
            findings = self._deterministic_findings(mutated_ir, skill_ir, known_evidence)
            expected_codes = {
                "missing_evidence": "missing_evidence",
                "broken_reference": "broken_evidence_ref",
                "digest_mismatch": "evidence_digest_mismatch",
                "scope_overreach": "scope_overreach",
                "modality_mismatch": "modality_mismatch",
                "stale_rule": "stale_rule",
                "unresolved_conflict": "skill_uses_ineligible_node",
            }
            detected = any(item["code"] == expected_codes[name] for item in findings)
            results.append({"name": name, "detected": detected, "finding_digest": sha256_json(findings)})
        missing_exception_skill = replace(skill_ir, exceptions=())
        exception_findings = self._deterministic_findings(knowledge_ir, missing_exception_skill, known_evidence)
        results.append(
            {
                "name": "missing_exception",
                "detected": any(item["code"] == "missing_exception" for item in exception_findings),
                "finding_digest": sha256_json(exception_findings),
            }
        )
        return results


def _source_modality(text: str) -> str | None:
    normalized = text.casefold()
    if "must not" in normalized:
        return "must_not"
    for modality in ("must", "should", "may"):
        if modality in normalized:
            return modality
    return None
