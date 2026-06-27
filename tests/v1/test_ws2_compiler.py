from __future__ import annotations

import json
from pathlib import Path

from expert_skill_system.compiler import (
    DirectToSkillIRBuilder,
    KnowledgeCompiler,
    OpenAICompatibleDirectToSkillIRBuilder,
)
from expert_skill_system.core.models import ArtifactRef, SourceRef
from expert_skill_system.registry.workspace import Workspace
from expert_skill_system.sources import SourceIngestionService


def _sources(tmp_path: Path):
    expert = tmp_path / "expert.md"
    expert.write_text(
        """# Python advisory procedure
- MUST PROCEDURE: Parse one exact pinned dependency version.
- MUST PROCEDURE: Query the frozen OSV advisory record and affected range.
- MUST CONSTRAINT: Return unresolved when required evidence is missing.
- MUST NOT CONSTRAINT: Claim exploitability from advisory applicability.
- MUST CONSTRAINT: Keep this contradictory sample.
- MUST NOT CONSTRAINT: Keep this contradictory sample.
- [UNSUPPORTED] Treat every dependency warning as exploitable.
""",
        encoding="utf-8",
    )
    osv = tmp_path / "osv.json"
    osv.write_text(
        json.dumps(
            {
                "vulns": [
                    {
                        "id": "PYSEC-DYNAMIC-99",
                        "affected": [
                            {
                                "package": {"ecosystem": "PyPI", "name": "requests"},
                                "ranges": [{"type": "ECOSYSTEM", "events": [{"introduced": "0"}, {"fixed": "2.32.0"}]}],
                            }
                        ],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    workspace = Workspace.open(tmp_path / ".eskill")
    service = SourceIngestionService(workspace)
    expert_snapshot = service.add(
        SourceRef(source_id="expert", uri=str(expert), adapter_type="expert-document", visibility="build")
    )
    osv_snapshot = service.add(SourceRef(source_id="osv", uri=str(osv), adapter_type="osv-snapshot", visibility="build"))
    return workspace, expert_snapshot, osv_snapshot


def _artifact_json(workspace: Workspace, payload: dict[str, object]):
    return workspace.artifacts.get_json(ArtifactRef.from_dict(payload))


def test_compiler_runs_all_stages_and_separates_skill_from_dynamic_knowledge(tmp_path: Path) -> None:
    workspace, expert, osv = _sources(tmp_path)
    build = KnowledgeCompiler(workspace).build(
        expert_snapshot=expert, structured_snapshots=(osv,), build_id="compiler-test"
    )

    assert len(build.stage_result_refs) == 10
    stages = [_artifact_json(workspace, item) for item in build.stage_result_refs]
    assert [item["stage_id"] for item in stages] == [
        "stage-0-capture",
        "stage-1-segment",
        "stage-2-explicit-extraction",
        "stage-3-evidence-binding",
        "stage-4-synthesis",
        "stage-5-limited-induction",
        "stage-6-modality-projection",
        "stage-7-skill-ir",
        "stage-8-knowledge-projection",
        "stage-9-source-grounded-validation",
    ]
    knowledge = _artifact_json(workspace, build.knowledge_ir_ref)
    skill = _artifact_json(workspace, build.skill_ir_ref)
    projection = _artifact_json(workspace, build.knowledge_projection_ref)
    assert knowledge["quarantined_nodes"][0]["uncertainty"] == "source marks this claim unsupported"
    assert sum(node["validation_status"] == "disputed" for node in knowledge["nodes"]) == 2
    assert "PYSEC-DYNAMIC-99" not in json.dumps(skill)
    assert projection["structured_snapshot_refs"][0]["digest"] == osv.raw_artifact_ref["digest"]
    assert build.skill_ir_ref["digest"] != build.knowledge_projection_ref["digest"]


def test_source_grounded_attestation_detects_registered_perturbations(tmp_path: Path) -> None:
    workspace, expert, osv = _sources(tmp_path)
    build = KnowledgeCompiler(workspace).build(expert_snapshot=expert, structured_snapshots=(osv,))
    attestation = _artifact_json(workspace, build.attestation_ref)

    assert attestation["deterministic_status"] == "pass"
    assert attestation["heldout_visibility_status"] == "pass"
    assert attestation["independent_judge_status"] == "not_configured"
    assert attestation["perturbation_status"] == "pass"
    assert {item["name"] for item in attestation["perturbation_results"]} == {
        "missing_evidence",
        "broken_reference",
        "digest_mismatch",
        "scope_overreach",
        "modality_mismatch",
        "stale_rule",
        "unresolved_conflict",
        "missing_exception",
    }
    assert all(item["detected"] for item in attestation["perturbation_results"])


def test_direct_baseline_outputs_same_skill_schema_without_compiler_intermediates(tmp_path: Path) -> None:
    workspace, expert, _ = _sources(tmp_path)
    compiler_build = KnowledgeCompiler(workspace).build(expert_snapshot=expert, build_id="compiler")
    direct_build = DirectToSkillIRBuilder(workspace).build(expert_snapshot=expert, build_id="direct")
    compiler_skill = _artifact_json(workspace, compiler_build.skill_ir_ref)
    direct_skill = _artifact_json(workspace, direct_build.skill_ir_ref)
    direct_stage = _artifact_json(workspace, direct_build.stage_result_refs[0])
    direct_attestation = _artifact_json(workspace, direct_build.attestation_ref)

    assert compiler_skill["schema_version"] == direct_skill["schema_version"] == "skill_ir.v1"
    assert direct_build.knowledge_ir_ref is None
    assert direct_build.knowledge_projection_ref is None
    assert len(direct_build.stage_result_refs) == 1
    assert direct_stage["stage_id"] == "direct-to-skill-ir-one-stage"
    assert direct_attestation["deterministic_status"] == "pass"


def test_live_direct_baseline_is_one_call_and_does_not_consume_knowledge_ir(tmp_path: Path, monkeypatch) -> None:
    workspace, expert, osv = _sources(tmp_path)
    generated = {
        "schema_version": "skill_ir.v1",
        "skill_id": "direct-python-advisory",
        "version": "1.0.0",
        "invocation": {"task_family": "python-advisory", "contraindications": ["exploitability"]},
        "workflow": [
            {"node_id": "direct-1", "instruction": "Parse one pinned dependency.", "modality": "must"}
        ],
        "constraints": [
            {"node_id": "direct-2", "instruction": "Do not claim exploitability.", "modality": "must_not"}
        ],
        "knowledge_requirements": [
            {
                "node_id": "direct-3",
                "semantic_requirement": "frozen advisory range",
                "unavailable_behavior": "return unresolved",
            }
        ],
        "exceptions": [
            {"node_id": "direct-2", "instruction": "Do not claim exploitability.", "modality": "must_not"}
        ],
        "source_node_ids": ["direct-1", "direct-2"],
    }
    response_payload = {
        "choices": [{"message": {"content": json.dumps(generated)}}],
        "usage": {"prompt_tokens": 100, "completion_tokens": 50},
    }

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return json.dumps(response_payload).encode("utf-8")

    requests = []

    def respond(request, timeout):
        requests.append((request, timeout))
        return Response()

    monkeypatch.setattr("urllib.request.urlopen", respond)
    build = OpenAICompatibleDirectToSkillIRBuilder(
        workspace,
        base_url="https://api.deepseek.example",
        model="deepseek-chat",
        api_key="synthetic-test-key",
    ).build(expert_snapshot=expert, material_snapshots=(osv,), build_id="direct-live")

    stage = _artifact_json(workspace, build.stage_result_refs[0])
    attestation = _artifact_json(workspace, build.attestation_ref)
    assert len(requests) == 1
    assert build.knowledge_ir_ref is None
    assert build.knowledge_projection_ref is None
    assert stage["stage_id"] == "direct-to-skill-ir-one-call-llm"
    assert stage["metrics"]["knowledge_ir_visible"] is False
    assert stage["metrics"]["heldout_gold_visible"] is False
    assert stage["metrics"]["normalization_events"] == [
        "source_node_ids_recomputed_from_used_node_ids"
    ]
    assert attestation["source_grounding_status"] == "not_evaluated_without_knowledge_ir"
    assert "synthetic-test-key" not in json.dumps(stage)
