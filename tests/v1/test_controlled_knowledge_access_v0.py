from __future__ import annotations

from expert_skill_system.knowledge_access import (
    KnowledgeIndexRow,
    audit_retrieval,
    build_access_trace,
    build_dependency_use_query_plan,
    retrieve,
)


def test_controlled_access_filters_verifier_and_evaluator_only_rows() -> None:
    rows = [
        KnowledgeIndexRow.create(
            knowledge_id="decl",
            source_id="repo",
            source_type="repo_snapshot",
            content="requests==2.19.1",
            evidence_type="dependency_declaration",
        ),
        KnowledgeIndexRow.create(
            knowledge_id="hidden",
            source_id="gold",
            source_type="input_material",
            content="redacted evaluator item",
            evidence_type="dependency_declaration",
            visibility="evaluator_only",
            allowed_to_agent=False,
        ),
        KnowledgeIndexRow.create(
            knowledge_id="verifier",
            source_id="verifier",
            source_type="allowed_knowledge",
            content="redacted verifier item",
            evidence_type="dependency_declaration",
            visibility="verifier_only",
            allowed_to_agent=False,
        ),
    ]
    plan = build_dependency_use_query_plan("requests", "PYSEC-2018-28")
    retrieved = retrieve(rows, plan)
    ids = {item["knowledge_id"] for item in retrieved["retrieved_refs"]}
    assert "decl" in ids
    assert "hidden" not in ids
    assert "verifier" not in ids
    audit = audit_retrieval(rows, retrieved)
    assert audit["knowledge_access_status"] == "pass"
    trace = build_access_trace(rows, plan, retrieved)
    assert all(item["allowed_to_agent"] is True for item in trace["trace_rows"])
