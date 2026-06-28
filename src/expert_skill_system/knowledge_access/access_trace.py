from __future__ import annotations

from typing import Any

from .index import KnowledgeIndexRow


def build_access_trace(index_rows: list[KnowledgeIndexRow], query_plan: dict[str, Any], retrieved: dict[str, Any]) -> dict[str, Any]:
    index_by_id = {row.knowledge_id: row for row in index_rows}
    trace_rows = []
    for item in retrieved.get("retrieved_refs", []):
        row = index_by_id.get(item["knowledge_id"])
        trace_rows.append(
            {
                "query_id": item["query_id"],
                "knowledge_id": item["knowledge_id"],
                "exists_in_index": row is not None,
                "visibility": row.visibility if row else None,
                "allowed_to_agent": row.allowed_to_agent if row else False,
                "returned_to_agent": True,
            }
        )
    return {
        "schema_version": "knowledge_access_trace.v0",
        "query_plan_ref": query_plan.get("schema_version"),
        "trace_rows": trace_rows,
    }


def audit_retrieval(index_rows: list[KnowledgeIndexRow], retrieved: dict[str, Any]) -> dict[str, Any]:
    index_by_id = {row.knowledge_id: row for row in index_rows}
    returned_ids = [item["knowledge_id"] for item in retrieved.get("retrieved_refs", [])]
    missing_ids = [item for item in returned_ids if item not in index_by_id]
    forbidden_returned = [
        item
        for item in returned_ids
        if item in index_by_id
        and (index_by_id[item].visibility in {"verifier_only", "evaluator_only"} or not index_by_id[item].allowed_to_agent)
    ]
    checks = {
        "returned_refs_exist_in_index": not missing_ids,
        "verifier_only_rows_not_returned": not any(index_by_id[item].visibility == "verifier_only" for item in forbidden_returned),
        "evaluator_only_rows_not_returned": not any(index_by_id[item].visibility == "evaluator_only" for item in forbidden_returned),
        "all_returned_refs_recorded": len(returned_ids) == len(retrieved.get("retrieved_refs", [])),
    }
    return {
        "schema_version": "knowledge_access_audit.v0",
        "knowledge_access_status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "missing_ids": missing_ids,
        "forbidden_returned": forbidden_returned,
    }
