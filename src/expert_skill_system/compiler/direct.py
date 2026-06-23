from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
import uuid
from typing import Any

from ..core.canonical import sha256_json
from ..core.models import ArtifactRef, EvidenceUnit, SourceSnapshot, StageResult
from ..registry.workspace import Workspace
from ..sources.adapters import SourceIngestionService
from .models import CompilerBuild, KnowledgeIR, KnowledgeProjection, SkillIR
from .pipeline import KnowledgeCompiler
from .validation import SourceGroundedValidator


class DirectToSkillIRBuilder:
    """One-stage baseline producing the same Skill IR without reading compiler intermediates."""

    def __init__(self, workspace: Workspace) -> None:
        self.workspace = workspace
        self.validator = SourceGroundedValidator()

    def build(
        self,
        *,
        expert_snapshot: SourceSnapshot,
        material_snapshots: tuple[SourceSnapshot, ...] = (),
        build_id: str | None = None,
    ) -> CompilerBuild:
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


class OpenAICompatibleDirectToSkillIRBuilder:
    """One-call raw-material-to-Skill-IR baseline with no Knowledge IR access."""

    contract_version = "direct_to_skill_ir_generation.v1"

    def __init__(
        self,
        workspace: Workspace,
        *,
        base_url: str,
        model: str,
        api_key: str,
        timeout_seconds: float = 120.0,
    ) -> None:
        if not base_url or not model or not api_key:
            raise ValueError("base_url, model and api_key are required")
        self.workspace = workspace
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    def build(
        self,
        *,
        expert_snapshot: SourceSnapshot,
        material_snapshots: tuple[SourceSnapshot, ...] = (),
        build_id: str | None = None,
    ) -> CompilerBuild:
        build_id = build_id or f"direct-llm-{uuid.uuid4()}"
        snapshots = (expert_snapshot, *material_snapshots)
        materials = [
            {
                "source_id": snapshot.source_id,
                "adapter_type": snapshot.adapter_type,
                "raw_digest": snapshot.raw_artifact_ref["digest"],
                "content": self.workspace.artifacts.get_bytes(
                    ArtifactRef.from_dict(snapshot.raw_artifact_ref)
                ).decode("utf-8"),
            }
            for snapshot in snapshots
        ]
        prompt = _direct_prompt(materials)
        request_payload = {
            "model": self.model,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [{"role": "user", "content": prompt}],
        }
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(request_payload).encode("utf-8"),
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        started = time.perf_counter()
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:  # noqa: S310
                raw = response.read()
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"direct generator provider returned HTTP {exc.code}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError("direct generator provider could not be reached") from exc
        elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
        try:
            response_payload = json.loads(raw.decode("utf-8"))
            content = response_payload["choices"][0]["message"]["content"]
            generated = json.loads(content)
        except (KeyError, IndexError, TypeError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            failure_ref = self._record_failure(
                raw=raw,
                category="response_contract",
                detail=type(exc).__name__,
                generated=None,
            )
            raise RuntimeError(
                f"direct generator response is not JSON; failure_artifact={failure_ref.digest}"
            ) from exc
        normalized, normalization_events = _normalize_generated_skill_ir(generated)
        try:
            skill_ir = _parse_generated_skill_ir(normalized)
        except ValueError as exc:
            failure_ref = self._record_failure(
                raw=raw,
                category="skill_ir_validation",
                detail=str(exc),
                generated=generated,
            )
            raise RuntimeError(
                f"direct generator returned invalid skill_ir.v1: {exc}; "
                f"failure_artifact={failure_ref.digest}"
            ) from exc
        skill_ref = self.workspace.put_json(skill_ir.to_dict(), schema_version=skill_ir.schema_version)
        visibility = SourceIngestionService(self.workspace).build_visibility_manifest()
        visibility_ref = self.workspace.put_json(visibility, schema_version="source_visibility_manifest.v1")
        usage = response_payload.get("usage", {})
        provenance = {
            "contract_version": self.contract_version,
            "provider_kind": "openai_compatible_chat_completions",
            "base_url": self.base_url,
            "model": self.model,
            "material_digests": [item["raw_digest"] for item in materials],
            "prompt_digest": sha256_json(prompt),
            "raw_response_digest": sha256_json(response_payload),
            "elapsed_ms": elapsed_ms,
            "prompt_tokens": usage.get("prompt_tokens"),
            "completion_tokens": usage.get("completion_tokens"),
            "api_key_present": True,
            "knowledge_ir_visible": False,
            "heldout_gold_visible": False,
            "normalization_events": normalization_events,
        }
        stage = StageResult(
            build_id=build_id,
            stage_id="direct-to-skill-ir-one-call-llm",
            input_refs=tuple(snapshot.raw_artifact_ref for snapshot in snapshots),
            output_refs=(skill_ref.to_dict(),),
            metrics={"pipeline_stages": 1, "target_schema": skill_ir.schema_version, **provenance},
        )
        stage_ref = self.workspace.put_json(stage.to_dict(), schema_version=stage.SCHEMA_VERSION)
        attestation = {
            "schema_version": "direct_generation_attestation.v1",
            "subject_digests": {"skill_ir": skill_ref.digest},
            "deterministic_status": "pass",
            "deterministic_findings": [],
            "source_grounding_status": "not_evaluated_without_knowledge_ir",
            "independent_judge_status": "not_configured",
            "perturbation_status": "not_applicable_to_baseline_generation",
            "heldout_visibility_status": "pass",
            "eligible_for_candidate": False,
            "generation_provenance": provenance,
        }
        attestation_ref = self.workspace.put_json(
            attestation, schema_version="direct_generation_attestation.v1"
        )
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

    def _record_failure(
        self,
        *,
        raw: bytes,
        category: str,
        detail: str,
        generated: Any,
    ) -> ArtifactRef:
        top_level_keys = sorted(generated) if isinstance(generated, dict) else []
        declared_node_ids = []
        used_node_ids = []
        if isinstance(generated, dict):
            declared = generated.get("source_node_ids", [])
            if isinstance(declared, list):
                declared_node_ids = sorted(str(item) for item in declared)
            for field in ("workflow", "constraints", "knowledge_requirements", "exceptions"):
                items = generated.get(field, [])
                if isinstance(items, list):
                    used_node_ids.extend(
                        str(item.get("node_id")) for item in items if isinstance(item, dict) and item.get("node_id")
                    )
        payload = {
            "schema_version": "direct_generation_failure.v1",
            "category": category,
            "detail": detail,
            "base_url": self.base_url,
            "model": self.model,
            "raw_response_digest": sha256_json(raw.decode("utf-8", errors="replace")),
            "generated_top_level_keys": top_level_keys,
            "declared_node_ids": declared_node_ids,
            "used_node_ids": sorted(set(used_node_ids)),
            "api_key_present": True,
            "raw_content_persisted": False,
        }
        return self.workspace.put_json(payload, schema_version=payload["schema_version"])


def _direct_prompt(materials: list[dict[str, Any]]) -> str:
    contract = {
        "schema_version": "skill_ir.v1",
        "skill_id": "string",
        "version": "string",
        "invocation": {"task_family": "string", "contraindications": ["string"]},
        "workflow": [{"node_id": "direct-N", "instruction": "string", "modality": "must|should|may|must_not"}],
        "constraints": [{"node_id": "direct-N", "instruction": "string", "modality": "must|should|may|must_not"}],
        "knowledge_requirements": [
            {"node_id": "direct-N", "semantic_requirement": "string", "unavailable_behavior": "string"}
        ],
        "exceptions": [{"node_id": "direct-N", "instruction": "string", "modality": "must_not"}],
        "source_node_ids": ["direct-N"],
    }
    return (
        "Generate exactly one Skill IR JSON object from the raw materials in one stage. "
        "Do not mention specific advisory identifiers, do not claim exploitability, and do not use hidden knowledge. "
        "Use only node ids direct-1, direct-2, and so on. Before returning, compute source_node_ids as the exact "
        "deduplicated union of every node_id used by workflow, constraints, knowledge_requirements, and exceptions; "
        "do not omit any used id and do not include unused ids. "
        "Return JSON only. Target contract:\n"
        + json.dumps(contract, ensure_ascii=False, sort_keys=True)
        + "\nRaw materials:\n"
        + json.dumps(materials, ensure_ascii=False, sort_keys=True)
    )


def _parse_generated_skill_ir(payload: Any) -> SkillIR:
    if not isinstance(payload, dict) or payload.get("schema_version") != "skill_ir.v1":
        raise ValueError("schema_version must be skill_ir.v1")
    required = {
        "skill_id", "version", "invocation", "workflow", "constraints",
        "knowledge_requirements", "exceptions", "source_node_ids",
    }
    if not required.issubset(payload):
        raise ValueError("missing Skill IR fields")
    if not isinstance(payload["invocation"], dict):
        raise ValueError("invocation must be an object")
    list_fields = ("workflow", "constraints", "knowledge_requirements", "exceptions", "source_node_ids")
    if any(not isinstance(payload[field], list) for field in list_fields):
        raise ValueError("Skill IR collection fields must be arrays")
    node_ids = {str(item) for item in payload["source_node_ids"]}
    if not node_ids or any(not item.startswith("direct-") for item in node_ids):
        raise ValueError("direct source node ids must be non-empty and use the direct- prefix")
    for field in ("workflow", "constraints", "exceptions"):
        for item in payload[field]:
            if not isinstance(item, dict) or item.get("node_id") not in node_ids:
                raise ValueError(f"{field} contains an unknown node_id")
            if item.get("modality") not in {"must", "should", "may", "must_not"}:
                raise ValueError(f"{field} contains an invalid modality")
            if not isinstance(item.get("instruction"), str) or not item["instruction"].strip():
                raise ValueError(f"{field} contains an invalid instruction")
    for item in payload["knowledge_requirements"]:
        if not isinstance(item, dict) or item.get("node_id") not in node_ids:
            raise ValueError("knowledge_requirements contains an unknown node_id")
        if not all(isinstance(item.get(key), str) and item[key].strip() for key in ("semantic_requirement", "unavailable_behavior")):
            raise ValueError("knowledge_requirements contains an invalid contract")
    serialized = json.dumps(payload, ensure_ascii=False)
    if "PYSEC-" in serialized or "GHSA-" in serialized:
        raise ValueError("dynamic advisory identifiers must not be embedded in Skill IR")
    return SkillIR(
        skill_id=str(payload["skill_id"]),
        version=str(payload["version"]),
        invocation=payload["invocation"],
        workflow=tuple(payload["workflow"]),
        constraints=tuple(payload["constraints"]),
        knowledge_requirements=tuple(payload["knowledge_requirements"]),
        exceptions=tuple(payload["exceptions"]),
        source_node_ids=tuple(str(item) for item in payload["source_node_ids"]),
    )


def _normalize_generated_skill_ir(payload: Any) -> tuple[Any, list[str]]:
    """Apply representation-only normalization shared with the runtime compiler boundary."""
    if not isinstance(payload, dict):
        return payload, []
    used: list[str] = []
    for field in ("workflow", "constraints", "knowledge_requirements", "exceptions"):
        items = payload.get(field)
        if not isinstance(items, list):
            return payload, []
        for item in items:
            if not isinstance(item, dict) or not isinstance(item.get("node_id"), str):
                return payload, []
            used.append(item["node_id"])
    used_ids = list(dict.fromkeys(used))
    if not used_ids or any(not item.startswith("direct-") for item in used_ids):
        return payload, []
    declared = payload.get("source_node_ids")
    if isinstance(declared, list) and set(map(str, declared)) == set(used_ids):
        return payload, []
    return {**payload, "source_node_ids": used_ids}, ["source_node_ids_recomputed_from_used_node_ids"]
