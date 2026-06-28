from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class KnowledgeQuery:
    query_id: str
    query_text: str
    required_evidence_type: str
    top_k: int = 3

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


def build_dependency_use_query_plan(package: str, advisory_id: str) -> dict[str, Any]:
    queries = [
        KnowledgeQuery(
            query_id="dependency_declaration",
            query_text=f"{package} dependency declaration resolved version requirements.txt",
            required_evidence_type="dependency_declaration",
        ),
        KnowledgeQuery(
            query_id="import_use",
            query_text=f"{package} import use site Python code requests.get requests.post",
            required_evidence_type="import_use",
        ),
        KnowledgeQuery(
            query_id="advisory_range",
            query_text=f"{advisory_id} {package} affected range introduced fixed version",
            required_evidence_type="advisory_range",
        ),
        KnowledgeQuery(
            query_id="output_constraint",
            query_text="decision evidence required evidence schema reason codes",
            required_evidence_type="output_constraint",
        ),
    ]
    return {
        "schema_version": "knowledge_query_plan.v0",
        "retrieval_method": "lexical_field_match",
        "package": package,
        "advisory_id": advisory_id,
        "queries": [query.to_json() for query in queries],
    }
