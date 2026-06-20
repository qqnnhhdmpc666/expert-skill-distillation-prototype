from __future__ import annotations

import json
from pathlib import Path

from expert_skill_system.core.models import KnowledgeQuery, SourceRef
from expert_skill_system.registry.workspace import Workspace
from expert_skill_system.sources import OSVSnapshotProvider, SourceIngestionService


def test_expert_document_has_line_and_byte_provenance_and_deduplicates(tmp_path: Path) -> None:
    document = tmp_path / "expert.md"
    document.write_text("# Scope\nUse pinned inputs.\n\n# Procedure\n1. Query evidence.\n2. Abstain if missing.\n", encoding="utf-8")
    workspace = Workspace.open(tmp_path / ".eskill")
    service = SourceIngestionService(workspace)
    source = SourceRef(source_id="expert-spec", uri=str(document), adapter_type="expert-document", visibility="build")

    first = service.add(source)
    second = service.add(source)

    assert first.metadata["snapshot_ref"]["digest"] == second.metadata["snapshot_ref"]["digest"]
    assert first.raw_artifact_ref["digest"] == second.raw_artifact_ref["digest"]
    rows = workspace.metadata.evidence_for_snapshot(first.raw_artifact_ref["digest"])
    assert len(rows) == 2
    assert rows[0]["locator"]["line_start"] == 1
    assert rows[0]["locator"]["byte_start"] == 0
    assert rows[1]["locator"]["heading"] == "# Procedure"


def test_requirements_adapter_accepts_pins_and_reports_unsupported_syntax(tmp_path: Path) -> None:
    requirements = tmp_path / "requirements.txt"
    requirements.write_text("Requests==2.31.0\nflask>=2\n", encoding="utf-8")
    workspace = Workspace.open(tmp_path / ".eskill")
    snapshot = SourceIngestionService(workspace).add(
        SourceRef(source_id="runtime-requirements", uri=str(requirements), adapter_type="requirements", visibility="runtime")
    )

    assert len(snapshot.evidence_refs) == 1
    assert snapshot.metadata["diagnostics"][0]["line"] == 2
    evidence_ref = workspace.metadata.artifact_ref(snapshot.evidence_refs[0]["digest"])
    evidence = workspace.artifacts.get_json(evidence_ref)
    assert evidence["attributes"]["normalized_name"] == "requests"
    assert evidence["attributes"]["version"] == "2.31.0"


def test_osv_snapshot_materializes_typed_query_with_provenance(tmp_path: Path) -> None:
    osv = tmp_path / "snapshot.json"
    osv.write_text(
        json.dumps(
            {
                "vulns": [
                    {
                        "id": "PYSEC-TEST-1",
                        "affected": [
                            {
                                "package": {"ecosystem": "PyPI", "name": "Requests"},
                                "ranges": [{"type": "ECOSYSTEM", "events": [{"introduced": "0"}, {"fixed": "2.32.0"}]}],
                                "versions": ["2.31.0"],
                            }
                        ],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    workspace = Workspace.open(tmp_path / ".eskill")
    snapshot = SourceIngestionService(workspace).add(
        SourceRef(source_id="osv-2026-06", uri=str(osv), adapter_type="osv-snapshot", visibility="build")
    )
    provider = OSVSnapshotProvider(Path(snapshot.metadata["index_path"]), snapshot.raw_artifact_ref["digest"])
    result = provider.query(
        KnowledgeQuery(
            provider_id=provider.provider_id,
            query_type="advisory_package",
            parameters={"advisory_id": "PYSEC-TEST-1", "package_name": "requests"},
        )
    )

    assert result.snapshot_digest == snapshot.raw_artifact_ref["digest"]
    assert result.evidence_units[0]["package_name"] == "requests"
    assert result.evidence_units[0]["advisory_id"] == "PYSEC-TEST-1"
    assert result.query_contract_digest.startswith("sha256:")
    assert result.result_digest.startswith("sha256:")


def test_visibility_manifest_excludes_heldout_from_build_closure(tmp_path: Path) -> None:
    build = tmp_path / "build.md"
    heldout = tmp_path / "heldout.md"
    build.write_text("# Build\nVisible material.\n", encoding="utf-8")
    heldout.write_text("# Heldout\nHidden gold.\n", encoding="utf-8")
    service = SourceIngestionService(Workspace.open(tmp_path / ".eskill"))
    build_snapshot = service.add(
        SourceRef(source_id="build", uri=str(build), adapter_type="expert-document", visibility="build")
    )
    heldout_snapshot = service.add(
        SourceRef(source_id="heldout", uri=str(heldout), adapter_type="expert-document", visibility="heldout")
    )

    manifest = service.build_visibility_manifest()
    assert build_snapshot.metadata["snapshot_ref"]["digest"] in manifest["visible_snapshot_digests"]
    assert heldout_snapshot.metadata["snapshot_ref"]["digest"] not in manifest["visible_snapshot_digests"]
    assert heldout_snapshot.metadata["snapshot_ref"]["digest"] not in json.dumps(manifest)
    assert manifest["excluded_visibility_counts"] == {"heldout": 1}
    assert manifest["heldout_in_build_closure"] is False
