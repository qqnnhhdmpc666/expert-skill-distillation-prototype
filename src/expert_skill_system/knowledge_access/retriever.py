from __future__ import annotations

import re
from typing import Any

from .index import KnowledgeIndexRow


def retrieve(index_rows: list[KnowledgeIndexRow], query_plan: dict[str, Any]) -> dict[str, Any]:
    retrieved: list[dict[str, Any]] = []
    for query in query_plan.get("queries", []):
        candidates = [
            row
            for row in index_rows
            if row.visibility == "agent_visible"
            and row.allowed_to_agent
            and row.evidence_type == query["required_evidence_type"]
        ]
        scored = sorted(
            ((_score(row, query["query_text"]), row) for row in candidates),
            key=lambda item: (-item[0], item[1].knowledge_id),
        )
        for score, row in scored[: int(query.get("top_k", 3))]:
            if score <= 0:
                continue
            retrieved.append(
                {
                    "query_id": query["query_id"],
                    "score": score,
                    "knowledge_id": row.knowledge_id,
                    "source_id": row.source_id,
                    "source_type": row.source_type,
                    "evidence_type": row.evidence_type,
                    "content": row.content,
                    "digest": row.digest,
                    "metadata": row.metadata,
                }
            )
    return {"schema_version": "retrieved_knowledge_refs.v0", "retrieved_refs": retrieved}


def _score(row: KnowledgeIndexRow, query_text: str) -> int:
    query_terms = set(_terms(query_text))
    content_terms = set(_terms(" ".join([row.content, row.evidence_type, row.source_type, row.source_id])))
    lexical_score = len(query_terms & content_terms)
    field_bonus = 2 if row.evidence_type.replace("_", " ") in query_text.lower() else 0
    return lexical_score + field_bonus


def _terms(text: str) -> list[str]:
    return [term for term in re.split(r"[^a-zA-Z0-9_.-]+", text.lower()) if term]
