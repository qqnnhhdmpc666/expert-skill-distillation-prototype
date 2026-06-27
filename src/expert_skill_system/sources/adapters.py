from __future__ import annotations

import json
import re
import sqlite3
from dataclasses import replace
from pathlib import Path
from typing import Protocol

from packaging.requirements import InvalidRequirement, Requirement
from packaging.utils import canonicalize_name

from ..core.canonical import sha256_bytes, sha256_json
from ..core.models import EvidenceUnit, SourceRef, SourceSnapshot, utc_now
from ..registry.workspace import Workspace


class SourceAdapter(Protocol):
    def ingest(self, source_ref: SourceRef, workspace: Workspace) -> SourceSnapshot: ...


def _read_utf8(path: Path) -> bytes:
    payload = path.read_bytes()
    payload.decode("utf-8")
    return payload


def _line_byte_offsets(payload: bytes) -> list[int]:
    offsets = [0]
    for match in re.finditer(b"\n", payload):
        offsets.append(match.end())
    return offsets


def _evidence_id(source_id: str, snapshot_digest: str, locator: dict[str, object]) -> str:
    return f"ev:{source_id}:{sha256_json({'snapshot': snapshot_digest, 'locator': locator})[-16:]}"


class ExpertDocumentAdapter:
    adapter_type = "expert-document"

    def ingest(self, source_ref: SourceRef, workspace: Workspace) -> SourceSnapshot:
        path = Path(source_ref.uri).resolve()
        payload = _read_utf8(path)
        text = payload.decode("utf-8")
        raw_ref = workspace.put_bytes(payload, media_type="text/markdown", schema_version="expert_document.raw.v1")
        lines = text.splitlines(keepends=True)
        offsets = _line_byte_offsets(payload)
        starts = [index for index, line in enumerate(lines) if line.lstrip().startswith("#")]
        if not starts:
            starts = [0]
        boundaries = [*starts, len(lines)]
        evidence_refs: list[dict[str, object]] = []
        for position, start in enumerate(starts):
            end = boundaries[position + 1]
            content = "".join(lines[start:end]).strip()
            if not content:
                continue
            byte_start = offsets[start]
            byte_end = offsets[end] if end < len(offsets) else len(payload)
            locator: dict[str, object] = {
                "kind": "line_byte_range",
                "line_start": start + 1,
                "line_end": end,
                "byte_start": byte_start,
                "byte_end": byte_end,
                "heading": lines[start].strip() if lines[start].lstrip().startswith("#") else None,
            }
            unit = EvidenceUnit(
                evidence_id=_evidence_id(source_ref.source_id, raw_ref.digest, locator),
                source_id=source_ref.source_id,
                source_snapshot_digest=raw_ref.digest,
                content=content,
                content_type="expert_section",
                locator=locator,
                attributes={"visibility": source_ref.visibility},
            )
            unit_ref = workspace.put_json(unit.to_dict(), schema_version=unit.SCHEMA_VERSION, artifact_id=unit.evidence_id)
            workspace.metadata.add_evidence(
                evidence_id=unit.evidence_id,
                artifact_ref=unit_ref,
                source_snapshot_digest=raw_ref.digest,
                locator=locator,
            )
            evidence_refs.append(unit_ref.to_dict())
        snapshot = SourceSnapshot(
            source_id=source_ref.source_id,
            adapter_type=self.adapter_type,
            source_uri=str(path),
            visibility=source_ref.visibility,
            captured_at=utc_now(),
            raw_artifact_ref=raw_ref.to_dict(),
            evidence_refs=tuple(evidence_refs),
            metadata={
                **source_ref.metadata,
                "visibility": source_ref.visibility,
                "encoding": "utf-8",
                "source_content_digest": raw_ref.digest,
            },
        )
        snapshot_ref = workspace.put_json(snapshot.to_dict(), schema_version=snapshot.SCHEMA_VERSION)
        workspace.metadata.add_source_snapshot(
            source_id=source_ref.source_id,
            snapshot_ref=snapshot_ref,
            adapter_type=self.adapter_type,
            source_uri=str(path),
            metadata=snapshot.metadata,
        )
        return replace(snapshot, metadata={**snapshot.metadata, "snapshot_ref": snapshot_ref.to_dict()})


class RequirementsAdapter:
    adapter_type = "requirements"

    def ingest(self, source_ref: SourceRef, workspace: Workspace) -> SourceSnapshot:
        path = Path(source_ref.uri).resolve()
        payload = _read_utf8(path)
        raw_ref = workspace.put_bytes(payload, media_type="text/plain", schema_version="requirements.raw.v1")
        evidence_refs: list[dict[str, object]] = []
        diagnostics: list[dict[str, object]] = []
        seen_pins: dict[str, tuple[str, str | None, int]] = {}
        byte_cursor = 0
        for line_number, raw_line in enumerate(payload.splitlines(keepends=True), start=1):
            line = raw_line.decode("utf-8").strip()
            byte_start = byte_cursor
            byte_cursor += len(raw_line)
            if not line or line.startswith("#"):
                continue
            try:
                requirement = Requirement(line)
                exact_versions = [specifier.version for specifier in requirement.specifier if specifier.operator in {"==", "==="}]
                if len(exact_versions) != 1 or len(requirement.specifier) != 1 or requirement.url or requirement.extras:
                    raise InvalidRequirement("V1 accepts one exact pinned version without extras or URL")
                attributes = {
                    "name": requirement.name,
                    "normalized_name": canonicalize_name(requirement.name),
                    "version": exact_versions[0],
                    "marker": str(requirement.marker) if requirement.marker else None,
                }
                prior = seen_pins.get(attributes["normalized_name"])
                current = (attributes["version"], attributes["marker"])
                if prior is not None and current != prior[:2]:
                    diagnostics.append(
                        {
                            "line": line_number,
                            "text": line,
                            "reason": "CONFLICTING_DUPLICATE_PIN",
                            "conflicts_with_line": prior[2],
                        }
                    )
                    continue
                seen_pins[attributes["normalized_name"]] = (*current, line_number)
            except InvalidRequirement as exc:
                diagnostics.append({"line": line_number, "text": line, "reason": str(exc)})
                continue
            locator: dict[str, object] = {
                "kind": "line_byte_range",
                "line_start": line_number,
                "line_end": line_number,
                "byte_start": byte_start,
                "byte_end": byte_cursor,
            }
            unit = EvidenceUnit(
                evidence_id=_evidence_id(source_ref.source_id, raw_ref.digest, locator),
                source_id=source_ref.source_id,
                source_snapshot_digest=raw_ref.digest,
                content=line,
                content_type="pinned_requirement",
                locator=locator,
                attributes={**attributes, "visibility": source_ref.visibility},
            )
            unit_ref = workspace.put_json(unit.to_dict(), schema_version=unit.SCHEMA_VERSION, artifact_id=unit.evidence_id)
            workspace.metadata.add_evidence(
                evidence_id=unit.evidence_id,
                artifact_ref=unit_ref,
                source_snapshot_digest=raw_ref.digest,
                locator=locator,
            )
            evidence_refs.append(unit_ref.to_dict())
        snapshot = SourceSnapshot(
            source_id=source_ref.source_id,
            adapter_type=self.adapter_type,
            source_uri=str(path),
            visibility=source_ref.visibility,
            captured_at=utc_now(),
            raw_artifact_ref=raw_ref.to_dict(),
            evidence_refs=tuple(evidence_refs),
            metadata={
                **source_ref.metadata,
                "visibility": source_ref.visibility,
                "diagnostics": diagnostics,
                "source_content_digest": raw_ref.digest,
            },
        )
        snapshot_ref = workspace.put_json(snapshot.to_dict(), schema_version=snapshot.SCHEMA_VERSION)
        workspace.metadata.add_source_snapshot(
            source_id=source_ref.source_id,
            snapshot_ref=snapshot_ref,
            adapter_type=self.adapter_type,
            source_uri=str(path),
            metadata=snapshot.metadata,
        )
        return replace(snapshot, metadata={**snapshot.metadata, "snapshot_ref": snapshot_ref.to_dict()})


class OSVSnapshotAdapter:
    adapter_type = "osv-snapshot"

    def ingest(self, source_ref: SourceRef, workspace: Workspace) -> SourceSnapshot:
        path = Path(source_ref.uri).resolve()
        payload = _read_utf8(path)
        parsed = json.loads(payload)
        records = parsed.get("vulns") if isinstance(parsed, dict) and "vulns" in parsed else parsed
        if isinstance(records, dict) and records.get("id"):
            records = [records]
        if not isinstance(records, list) or not records:
            raise ValueError("OSV snapshot must be a non-empty list or {'vulns': [...]} object")
        for record in records:
            if not isinstance(record, dict) or not record.get("id") or not isinstance(record.get("affected", []), list):
                raise ValueError("invalid OSV record")
        raw_ref = workspace.put_bytes(payload, media_type="application/json", schema_version="osv_snapshot.raw.v1")
        index_dir = workspace.root / "indexes" / "osv"
        index_dir.mkdir(parents=True, exist_ok=True)
        index_path = index_dir / f"{raw_ref.digest.removeprefix('sha256:')}.sqlite"
        if not index_path.exists():
            self._materialize_index(index_path, records, raw_ref.digest)
        index_ref = workspace.put_bytes(
            index_path.read_bytes(), media_type="application/vnd.sqlite3", schema_version="osv_projection.sqlite.v1"
        )
        evidence_refs: list[dict[str, object]] = []
        for ordinal, record in enumerate(records):
            locator: dict[str, object] = {"kind": "json_record", "record_id": record["id"], "ordinal": ordinal}
            unit = EvidenceUnit(
                evidence_id=_evidence_id(source_ref.source_id, raw_ref.digest, locator),
                source_id=source_ref.source_id,
                source_snapshot_digest=raw_ref.digest,
                content=json.dumps(record, ensure_ascii=False, sort_keys=True),
                content_type="osv_advisory",
                locator=locator,
                attributes={"advisory_id": record["id"], "visibility": source_ref.visibility},
            )
            unit_ref = workspace.put_json(unit.to_dict(), schema_version=unit.SCHEMA_VERSION, artifact_id=unit.evidence_id)
            workspace.metadata.add_evidence(
                evidence_id=unit.evidence_id,
                artifact_ref=unit_ref,
                source_snapshot_digest=raw_ref.digest,
                locator=locator,
            )
            evidence_refs.append(unit_ref.to_dict())
        metadata = {
            **source_ref.metadata,
            "visibility": source_ref.visibility,
            "record_count": len(records),
            "index_path": str(index_path),
            "source_content_digest": sha256_bytes(payload),
        }
        snapshot = SourceSnapshot(
            source_id=source_ref.source_id,
            adapter_type=self.adapter_type,
            source_uri=str(path),
            visibility=source_ref.visibility,
            captured_at=utc_now(),
            raw_artifact_ref=raw_ref.to_dict(),
            evidence_refs=tuple(evidence_refs),
            native_index_refs=(index_ref.to_dict(),),
            metadata=metadata,
        )
        snapshot_ref = workspace.put_json(snapshot.to_dict(), schema_version=snapshot.SCHEMA_VERSION)
        workspace.metadata.add_source_snapshot(
            source_id=source_ref.source_id,
            snapshot_ref=snapshot_ref,
            adapter_type=self.adapter_type,
            source_uri=str(path),
            metadata=metadata,
        )
        return replace(snapshot, metadata={**metadata, "snapshot_ref": snapshot_ref.to_dict()})

    @staticmethod
    def _materialize_index(path: Path, records: list[dict[str, object]], snapshot_digest: str) -> None:
        with sqlite3.connect(path) as connection:
            connection.executescript(
                """
                CREATE TABLE metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL);
                CREATE TABLE advisory(advisory_id TEXT PRIMARY KEY, record_json TEXT NOT NULL);
                CREATE TABLE affected(advisory_id TEXT NOT NULL, ecosystem TEXT, package_name TEXT NOT NULL, ranges_json TEXT NOT NULL, versions_json TEXT NOT NULL);
                CREATE INDEX affected_package_idx ON affected(package_name, advisory_id);
                """
            )
            connection.execute("INSERT INTO metadata VALUES ('snapshot_digest', ?)", (snapshot_digest,))
            for record in sorted(records, key=lambda item: str(item["id"])):
                advisory_id = str(record["id"])
                connection.execute(
                    "INSERT INTO advisory VALUES (?, ?)",
                    (advisory_id, json.dumps(record, ensure_ascii=False, sort_keys=True)),
                )
                for affected in record.get("affected", []):  # type: ignore[union-attr]
                    package = affected.get("package", {})
                    connection.execute(
                        "INSERT INTO affected VALUES (?, ?, ?, ?, ?)",
                        (
                            advisory_id,
                            package.get("ecosystem"),
                            canonicalize_name(str(package.get("name", ""))),
                            json.dumps(affected.get("ranges", []), sort_keys=True),
                            json.dumps(affected.get("versions", []), sort_keys=True),
                        ),
                    )


class SourceIngestionService:
    def __init__(self, workspace: Workspace) -> None:
        self.workspace = workspace
        self.adapters: dict[str, SourceAdapter] = {
            "expert-document": ExpertDocumentAdapter(),
            "requirements": RequirementsAdapter(),
            "osv-snapshot": OSVSnapshotAdapter(),
        }

    def add(self, source_ref: SourceRef) -> SourceSnapshot:
        adapter = self.adapters.get(source_ref.adapter_type)
        if adapter is None:
            raise ValueError(f"unsupported source adapter: {source_ref.adapter_type}")
        content_digest = sha256_bytes(_read_utf8(Path(source_ref.uri).resolve()))
        for existing in self.workspace.metadata.source_snapshots():
            if (
                existing["source_id"] == source_ref.source_id
                and existing["adapter_type"] == source_ref.adapter_type
                and existing["metadata"].get("source_content_digest") == content_digest
            ):
                snapshot_ref = self.workspace.metadata.artifact_ref(existing["snapshot_digest"])
                snapshot = SourceSnapshot.from_dict(self.workspace.artifacts.get_json(snapshot_ref))
                return replace(snapshot, metadata={**snapshot.metadata, "snapshot_ref": snapshot_ref.to_dict()})
        return adapter.ingest(source_ref, self.workspace)

    def build_visibility_manifest(self) -> dict[str, object]:
        snapshots = self.workspace.metadata.source_snapshots()
        visible = [item for item in snapshots if item["metadata"].get("visibility") in {"build", "dev"}]
        heldout_count = sum(item["metadata"].get("visibility") == "heldout" for item in snapshots)
        return {
            "schema_version": "source_visibility_manifest.v1",
            "visible_snapshot_digests": sorted(item["snapshot_digest"] for item in visible),
            "excluded_visibility_counts": {"heldout": heldout_count},
            "heldout_in_build_closure": False,
        }
