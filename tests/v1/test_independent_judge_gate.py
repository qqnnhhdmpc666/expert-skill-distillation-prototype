from __future__ import annotations

import json
import urllib.error
from pathlib import Path

import pytest

from expert_skill_system.compiler import KnowledgeCompiler
from expert_skill_system.compiler.judge import JudgeGateError, JudgeResult, OpenAICompatibleJudge
from expert_skill_system.compiler.models import KnowledgeIR, KnowledgeNode, KnowledgeProjection, SkillIR
from expert_skill_system.compiler.validation import SourceGroundedValidator
from expert_skill_system.core.models import ArtifactRef, EvidenceUnit, SourceRef
from expert_skill_system.registry.workspace import Workspace
from expert_skill_system.sources import SourceIngestionService


def _objects():
    digest = "sha256:" + "1" * 64
    evidence = EvidenceUnit(
        evidence_id="evidence-1",
        source_id="expert",
        source_snapshot_digest=digest,
        content="- MUST PROCEDURE: Query frozen advisory evidence.",
        content_type="expert_section",
    )
    node = KnowledgeNode(
        node_id="opaque-1",
        semantic_type="procedure",
        statement="MUST Query frozen advisory evidence.",
        modality="must",
        evidence_refs=({"evidence_id": evidence.evidence_id, "source_snapshot_digest": digest},),
        quoted_support_spans=("- MUST PROCEDURE: Query frozen advisory evidence.",),
        scope_claim={"task_family": "python-advisory"},
    )
    knowledge = KnowledgeIR(nodes=(node,), source_snapshot_digests=(digest,))
    skill = SkillIR(
        invocation={"task_family": "python-advisory"},
        workflow=({"node_id": node.node_id, "instruction": node.statement, "modality": "must"},),
        source_node_ids=(node.node_id,),
    )
    projection = KnowledgeProjection(expert_evidence_refs=tuple(node.evidence_refs))
    return evidence, knowledge, skill, projection


def test_formal_profile_does_not_treat_unconfigured_judge_as_pass() -> None:
    evidence, knowledge, skill, projection = _objects()
    attestation = SourceGroundedValidator(require_judge=True).validate(
        knowledge_ir=knowledge,
        skill_ir=skill,
        projection=projection,
        known_evidence={evidence.evidence_id: evidence},
        visibility_manifest={"heldout_in_build_closure": False, "visible_snapshot_digests": []},
        subject_digests={"knowledge_ir": "sha256:" + "2" * 64},
    )

    assert attestation.validation_profile == "formal-research"
    assert attestation.independent_judge_status == "not_configured"
    assert attestation.eligible_for_candidate is False


def test_openai_compatible_judge_is_blind_and_does_not_persist_key(monkeypatch) -> None:
    _, knowledge, skill, _ = _objects()
    response_payload = {
        "choices": [{"message": {"content": json.dumps({"status": "pass", "findings": []})}}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 4},
    }

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def read(self):
            return json.dumps(response_payload).encode("utf-8")

    monkeypatch.setattr("urllib.request.urlopen", lambda request, timeout: Response())
    judge = OpenAICompatibleJudge(base_url="https://api.deepseek.com", model="deepseek-chat", api_key="secret-test-key")
    result = judge.evaluate(knowledge, skill)

    assert result.status == "pass"
    assert judge.last_blind_payload is not None
    serialized_input = json.dumps(judge.last_blind_payload)
    serialized_provenance = json.dumps(result.provenance)
    assert "compiler_distilled_skill" not in serialized_input
    assert "direct_to_skill_ir" not in serialized_input
    assert "secret-test-key" not in serialized_input
    assert "secret-test-key" not in serialized_provenance
    assert result.provenance["base_url"] == "https://api.deepseek.com"
    assert result.provenance["api_key_present"] is True


def test_formal_profile_rejects_critical_judge_finding() -> None:
    evidence, knowledge, skill, projection = _objects()

    class FailingJudge:
        def evaluate(self, knowledge_ir, skill_ir):
            return JudgeResult(
                status="fail",
                findings=({"category": "scope_overreach", "severity": "critical", "opaque_node_id": "opaque-1"},),
                provenance={"model": "independent-test-double"},
            )

    attestation = SourceGroundedValidator(judge=FailingJudge(), require_judge=True).validate(
        knowledge_ir=knowledge,
        skill_ir=skill,
        projection=projection,
        known_evidence={evidence.evidence_id: evidence},
        visibility_manifest={"heldout_in_build_closure": False, "visible_snapshot_digests": []},
        subject_digests={"knowledge_ir": "sha256:" + "2" * 64},
    )

    assert attestation.independent_judge_status == "fail"
    assert attestation.eligible_for_candidate is False


def test_malformed_judge_response_is_a_hard_contract_failure(monkeypatch) -> None:
    _, knowledge, skill, _ = _objects()

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def read(self):
            return b'{"choices":[{"message":{"content":"not-json"}}]}'

    monkeypatch.setattr("urllib.request.urlopen", lambda request, timeout: Response())
    judge = OpenAICompatibleJudge(base_url="https://api.deepseek.com", model="deepseek-chat", api_key="test")
    with pytest.raises(JudgeGateError, match="contract JSON") as raised:
        judge.evaluate(knowledge, skill)
    assert raised.value.category == "malformed_response"


def test_authentication_failure_cannot_become_a_judge_pass(monkeypatch) -> None:
    _, knowledge, skill, _ = _objects()

    def fail_auth(request, timeout):
        raise urllib.error.HTTPError(request.full_url, 401, "Unauthorized", {}, None)

    monkeypatch.setattr("urllib.request.urlopen", fail_auth)
    judge = OpenAICompatibleJudge(base_url="https://api.deepseek.com", model="deepseek-chat", api_key="invalid")
    with pytest.raises(JudgeGateError) as raised:
        judge.evaluate(knowledge, skill)
    assert raised.value.category == "authentication"
    assert raised.value.http_status == 401


def test_judge_pass_is_persisted_in_build_attestation(tmp_path: Path) -> None:
    expert_path = tmp_path / "expert.md"
    expert_path.write_text(
        "- MUST PROCEDURE: Query frozen OSV advisory evidence.\n"
        "- MUST NOT CONSTRAINT: Claim exploitability from advisory applicability.\n",
        encoding="utf-8",
    )
    osv_path = tmp_path / "osv.json"
    osv_path.write_text(
        json.dumps(
            {
                "id": "PYSEC-JUDGE-1",
                "affected": [
                    {
                        "package": {"ecosystem": "PyPI", "name": "requests"},
                        "ranges": [{"type": "ECOSYSTEM", "events": [{"introduced": "0"}, {"fixed": "2.20.0"}]}],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    workspace = Workspace.open(tmp_path / ".eskill")
    ingestion = SourceIngestionService(workspace)
    expert = ingestion.add(SourceRef(source_id="expert", uri=str(expert_path), adapter_type="expert-document"))
    osv = ingestion.add(SourceRef(source_id="osv", uri=str(osv_path), adapter_type="osv-snapshot"))

    class PassingJudge:
        def evaluate(self, knowledge_ir, skill_ir):
            return JudgeResult(status="pass", findings=(), provenance={"model": "independent-test-double"})

    build = KnowledgeCompiler(workspace, judge=PassingJudge(), require_judge=True).build(
        expert_snapshot=expert, structured_snapshots=(osv,)
    )
    attestation = workspace.artifacts.get_json(ArtifactRef.from_dict(build.attestation_ref))
    assert attestation["independent_judge_status"] == "pass"
    assert attestation["eligible_for_candidate"] is True
    assert attestation["validation_profile"] == "formal-research"
