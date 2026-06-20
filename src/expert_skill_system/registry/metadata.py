from __future__ import annotations

import json
import sqlite3
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from ..core.models import ActiveBinding, ArtifactRef, DeploymentEvent, utc_now


class ConcurrentBindingUpdate(RuntimeError):
    pass


MIGRATION_V1 = """
CREATE TABLE IF NOT EXISTS schema_migration (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS artifact (
    digest TEXT PRIMARY KEY,
    artifact_id TEXT NOT NULL,
    media_type TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS source_snapshot (
    source_id TEXT NOT NULL,
    snapshot_digest TEXT NOT NULL REFERENCES artifact(digest),
    adapter_type TEXT NOT NULL,
    source_uri TEXT NOT NULL,
    metadata_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (source_id, snapshot_digest)
);
CREATE TABLE IF NOT EXISTS evidence_index (
    evidence_id TEXT PRIMARY KEY,
    artifact_digest TEXT NOT NULL REFERENCES artifact(digest),
    source_snapshot_digest TEXT NOT NULL,
    locator_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS dependency_edge (
    dependent_digest TEXT NOT NULL,
    dependency_digest TEXT NOT NULL,
    role TEXT NOT NULL,
    criticality TEXT NOT NULL,
    PRIMARY KEY (dependent_digest, dependency_digest, role)
);
CREATE TABLE IF NOT EXISTS build_record (
    build_id TEXT PRIMARY KEY,
    candidate_bundle_digest TEXT,
    status TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS evaluation_attestation (
    attestation_id TEXT PRIMARY KEY,
    subject_digest TEXT NOT NULL,
    status TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS active_binding (
    binding_key TEXT PRIMARY KEY,
    bundle_digest TEXT NOT NULL,
    generation INTEGER NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS deployment_event (
    event_id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    binding_key TEXT NOT NULL,
    from_digest TEXT,
    to_digest TEXT,
    generation_before INTEGER NOT NULL,
    generation_after INTEGER NOT NULL,
    reason_codes_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS session (
    session_id TEXT PRIMARY KEY,
    binding_key TEXT NOT NULL,
    bundle_digest TEXT NOT NULL,
    status TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    completed_at TEXT
);
CREATE TABLE IF NOT EXISTS cost_event (
    event_id TEXT PRIMARY KEY,
    owner_id TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS decision_record (
    record_id TEXT PRIMARY KEY,
    decision_type TEXT NOT NULL,
    subject_digest TEXT,
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


class MetadataStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._migrate()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        return connection

    def _migrate(self) -> None:
        with self.connect() as connection:
            connection.executescript(MIGRATION_V1)
            connection.execute("INSERT OR IGNORE INTO schema_migration(version, applied_at) VALUES (?, ?)", (1, utc_now()))

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        connection = self.connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def register_artifact(self, ref: ArtifactRef) -> None:
        with self.connect() as connection:
            connection.execute(
                "INSERT OR IGNORE INTO artifact(digest, artifact_id, media_type, schema_version, size_bytes, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (ref.digest, ref.artifact_id, ref.media_type, ref.artifact_schema_version, ref.size_bytes, utc_now()),
            )

    def artifact_ref(self, digest: str) -> ArtifactRef:
        with self.connect() as connection:
            row = connection.execute("SELECT * FROM artifact WHERE digest = ?", (digest,)).fetchone()
        if row is None:
            raise KeyError(digest)
        return ArtifactRef(
            artifact_id=row["artifact_id"],
            digest=row["digest"],
            media_type=row["media_type"],
            artifact_schema_version=row["schema_version"],
            size_bytes=row["size_bytes"],
        )

    def add_source_snapshot(self, *, source_id: str, snapshot_ref: ArtifactRef, adapter_type: str, source_uri: str, metadata: dict[str, Any]) -> None:
        self.register_artifact(snapshot_ref)
        with self.connect() as connection:
            connection.execute(
                "INSERT OR IGNORE INTO source_snapshot(source_id, snapshot_digest, adapter_type, source_uri, metadata_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (source_id, snapshot_ref.digest, adapter_type, source_uri, json.dumps(metadata, sort_keys=True), utc_now()),
            )

    def add_evidence(self, *, evidence_id: str, artifact_ref: ArtifactRef, source_snapshot_digest: str, locator: dict[str, Any]) -> None:
        self.register_artifact(artifact_ref)
        with self.connect() as connection:
            connection.execute(
                "INSERT OR IGNORE INTO evidence_index(evidence_id, artifact_digest, source_snapshot_digest, locator_json, created_at) VALUES (?, ?, ?, ?, ?)",
                (evidence_id, artifact_ref.digest, source_snapshot_digest, json.dumps(locator, sort_keys=True), utc_now()),
            )

    def source_snapshots(self, *, visibility: str | None = None) -> list[dict[str, Any]]:
        query = "SELECT * FROM source_snapshot"
        parameters: tuple[Any, ...] = ()
        if visibility is not None:
            query += " WHERE json_extract(metadata_json, '$.visibility') = ?"
            parameters = (visibility,)
        query += " ORDER BY source_id, snapshot_digest"
        with self.connect() as connection:
            rows = connection.execute(query, parameters).fetchall()
        return [{**dict(row), "metadata": json.loads(row["metadata_json"])} for row in rows]

    def evidence_for_snapshot(self, snapshot_digest: str) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM evidence_index WHERE source_snapshot_digest = ? ORDER BY evidence_id", (snapshot_digest,)
            ).fetchall()
        return [{**dict(row), "locator": json.loads(row["locator_json"])} for row in rows]

    def add_build_record(self, *, build_id: str, status: str, payload: dict[str, Any], candidate_bundle_digest: str | None = None) -> None:
        with self.connect() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO build_record(build_id, candidate_bundle_digest, status, payload_json, created_at) VALUES (?, ?, ?, ?, ?)",
                (build_id, candidate_bundle_digest, status, json.dumps(payload, sort_keys=True), utc_now()),
            )

    def get_build_record(self, build_id: str) -> dict[str, Any]:
        with self.connect() as connection:
            row = connection.execute("SELECT * FROM build_record WHERE build_id = ?", (build_id,)).fetchone()
        if row is None:
            raise KeyError(build_id)
        return {**dict(row), "payload": json.loads(row["payload_json"])}

    def start_session(self, *, session_id: str, binding_key: str, bundle_digest: str, payload: dict[str, Any]) -> None:
        with self.connect() as connection:
            connection.execute(
                "INSERT INTO session(session_id, binding_key, bundle_digest, status, payload_json, created_at) VALUES (?, ?, ?, 'running', ?, ?)",
                (session_id, binding_key, bundle_digest, json.dumps(payload, sort_keys=True), utc_now()),
            )

    def complete_session(self, *, session_id: str, status: str, payload: dict[str, Any]) -> None:
        with self.connect() as connection:
            connection.execute(
                "UPDATE session SET status = ?, payload_json = ?, completed_at = ? WHERE session_id = ?",
                (status, json.dumps(payload, sort_keys=True), utc_now(), session_id),
            )
            if connection.total_changes != 1:
                raise KeyError(session_id)

    def get_session(self, session_id: str) -> dict[str, Any]:
        with self.connect() as connection:
            row = connection.execute("SELECT * FROM session WHERE session_id = ?", (session_id,)).fetchone()
        if row is None:
            raise KeyError(session_id)
        return {**dict(row), "payload": json.loads(row["payload_json"])}

    def get_active_binding(self, binding_key: str) -> ActiveBinding | None:
        with self.connect() as connection:
            row = connection.execute("SELECT * FROM active_binding WHERE binding_key = ?", (binding_key,)).fetchone()
        if row is None:
            return None
        return ActiveBinding(
            binding_key=row["binding_key"],
            bundle_digest=row["bundle_digest"],
            generation=row["generation"],
            updated_at=row["updated_at"],
        )

    def change_binding(
        self,
        *,
        binding_key: str,
        target_digest: str,
        expected_generation: int,
        event_type: str,
        reason_codes: tuple[str, ...] = (),
    ) -> ActiveBinding:
        if event_type not in {"promote", "rollback"}:
            raise ValueError("change_binding event_type must be promote or rollback")
        now = utc_now()
        with self.transaction() as connection:
            row = connection.execute("SELECT * FROM active_binding WHERE binding_key = ?", (binding_key,)).fetchone()
            current_generation = int(row["generation"]) if row else 0
            from_digest = str(row["bundle_digest"]) if row else None
            if current_generation != expected_generation:
                raise ConcurrentBindingUpdate(
                    f"binding {binding_key!r} generation is {current_generation}, expected {expected_generation}"
                )
            next_generation = current_generation + 1
            if row:
                connection.execute(
                    "UPDATE active_binding SET bundle_digest = ?, generation = ?, updated_at = ? WHERE binding_key = ? AND generation = ?",
                    (target_digest, next_generation, now, binding_key, expected_generation),
                )
                if connection.total_changes != 1:
                    raise ConcurrentBindingUpdate(binding_key)
            else:
                connection.execute(
                    "INSERT INTO active_binding(binding_key, bundle_digest, generation, updated_at) VALUES (?, ?, ?, ?)",
                    (binding_key, target_digest, next_generation, now),
                )
            event = DeploymentEvent(
                event_id=str(uuid.uuid4()),
                event_type=event_type,  # type: ignore[arg-type]
                binding_key=binding_key,
                from_digest=from_digest,
                to_digest=target_digest,
                generation_before=current_generation,
                generation_after=next_generation,
                reason_codes=reason_codes,
                created_at=now,
            )
            connection.execute(
                "INSERT INTO deployment_event VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    event.event_id,
                    event.event_type,
                    event.binding_key,
                    event.from_digest,
                    event.to_digest,
                    event.generation_before,
                    event.generation_after,
                    json.dumps(event.reason_codes),
                    event.created_at,
                ),
            )
        return ActiveBinding(binding_key=binding_key, bundle_digest=target_digest, generation=next_generation, updated_at=now)

    def record_rejection(self, *, binding_key: str, candidate_digest: str, reason_codes: tuple[str, ...]) -> DeploymentEvent:
        active = self.get_active_binding(binding_key)
        generation = active.generation if active else 0
        event = DeploymentEvent(
            event_id=str(uuid.uuid4()),
            event_type="reject",
            binding_key=binding_key,
            from_digest=active.bundle_digest if active else None,
            to_digest=candidate_digest,
            generation_before=generation,
            generation_after=generation,
            reason_codes=reason_codes,
            created_at=utc_now(),
        )
        with self.connect() as connection:
            connection.execute(
                "INSERT INTO deployment_event VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    event.event_id,
                    event.event_type,
                    event.binding_key,
                    event.from_digest,
                    event.to_digest,
                    event.generation_before,
                    event.generation_after,
                    json.dumps(event.reason_codes),
                    event.created_at,
                ),
            )
        return event

    def deployment_history(self, binding_key: str) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute("SELECT * FROM deployment_event WHERE binding_key = ? ORDER BY created_at, event_id", (binding_key,)).fetchall()
        return [
            {
                **dict(row),
                "reason_codes": json.loads(row["reason_codes_json"]),
            }
            for row in rows
        ]
