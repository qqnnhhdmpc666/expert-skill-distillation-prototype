from __future__ import annotations

import json

from expert_skill_system.compiler.judge import JudgeResult, OpenAICompatibleJudge
from expert_skill_system.compiler.models import KnowledgeIR, KnowledgeNode, KnowledgeProjection, SkillIR
from expert_skill_system.compiler.validation import SourceGroundedValidator
from expert_skill_system.core.models import EvidenceUnit


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
