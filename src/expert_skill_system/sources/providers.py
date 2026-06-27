from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path

from packaging.utils import canonicalize_name

from ..core.canonical import sha256_json
from ..core.models import EvidenceEnvelope, KnowledgeQuery
from ..registry.workspace import Workspace


class ExpertSectionProvider:
    provider_id = "expert-section-provider"
    provider_version = "v1"

    def __init__(self, workspace: Workspace, snapshot_digest: str) -> None:
        self.workspace = workspace
        self.snapshot_digest = snapshot_digest

    def query(self, request: KnowledgeQuery) -> EvidenceEnvelope:
        started = time.perf_counter()
        rows = self.workspace.metadata.evidence_for_snapshot(self.snapshot_digest)
        heading = str(request.parameters.get("heading", "")).casefold()
        selected = [row for row in rows if not heading or heading in str(row["locator"].get("heading", "")).casefold()]
        selected = selected[: request.limit]
        result = [{"evidence_id": row["evidence_id"], "artifact_digest": row["artifact_digest"], "locator": row["locator"]} for row in selected]
        return _envelope(self.provider_id, self.provider_version, self.snapshot_digest, request, result, started)


class OSVSnapshotProvider:
    provider_id = "osv-snapshot-provider"
    provider_version = "v1"

    def __init__(self, index_path: Path, snapshot_digest: str) -> None:
        self.index_path = index_path
        self.snapshot_digest = snapshot_digest

    def query(self, request: KnowledgeQuery) -> EvidenceEnvelope:
        started = time.perf_counter()
        advisory_id = request.parameters.get("advisory_id")
        package_name = request.parameters.get("package_name")
        clauses: list[str] = []
        values: list[str] = []
        if advisory_id:
            clauses.append("a.advisory_id = ?")
            values.append(str(advisory_id))
        if package_name:
            clauses.append("f.package_name = ?")
            values.append(canonicalize_name(str(package_name)))
        where = " AND ".join(clauses) if clauses else "1 = 1"
        with sqlite3.connect(self.index_path) as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                f"""SELECT a.advisory_id, a.record_json, f.ecosystem, f.package_name, f.ranges_json, f.versions_json
                    FROM advisory a JOIN affected f ON a.advisory_id = f.advisory_id
                    WHERE {where} ORDER BY a.advisory_id, f.package_name LIMIT ?""",  # noqa: S608 - clauses are fixed constants
                (*values, request.limit),
            ).fetchall()
        result = [
            {
                "advisory_id": row["advisory_id"],
                "record": json.loads(row["record_json"]),
                "ecosystem": row["ecosystem"],
                "package_name": row["package_name"],
                "ranges": json.loads(row["ranges_json"]),
                "versions": json.loads(row["versions_json"]),
            }
            for row in rows
        ]
        return _envelope(self.provider_id, self.provider_version, self.snapshot_digest, request, result, started)


class BuildCaseProvider:
    provider_id = "build-case-provider"
    provider_version = "v1"

    def __init__(self, path: Path) -> None:
        self.path = path
        self.snapshot_digest = sha256_json(path.read_text(encoding="utf-8").splitlines())

    def query(self, request: KnowledgeQuery) -> EvidenceEnvelope:
        started = time.perf_counter()
        cases = [json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines() if line.strip()]
        selected = [
            case
            for case in cases
            if all(case.get(key) == value for key, value in request.parameters.items())
        ][: request.limit]
        return _envelope(self.provider_id, self.provider_version, self.snapshot_digest, request, selected, started)


def _envelope(
    provider_id: str,
    provider_version: str,
    snapshot_digest: str,
    request: KnowledgeQuery,
    result: list[dict[str, object]],
    started: float,
) -> EvidenceEnvelope:
    query_contract_digest = sha256_json(
        {"provider_id": provider_id, "provider_version": provider_version, "query_type": request.query_type}
    )
    return EvidenceEnvelope(
        provider_id=provider_id,
        provider_version=provider_version,
        snapshot_digest=snapshot_digest,
        query_contract_digest=query_contract_digest,
        normalized_parameters=request.parameters,
        evidence_units=tuple(result),
        result_digest=sha256_json(result),
        elapsed_ms=round((time.perf_counter() - started) * 1000, 3),
    )
