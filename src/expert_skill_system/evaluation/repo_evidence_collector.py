from __future__ import annotations

import re
from fnmatch import fnmatch
from pathlib import Path
from typing import Any

from ..core.canonical import sha256_bytes, sha256_json


def collect_repo_evidence(
    *,
    task_dir: Path,
    repo_manifest: dict[str, Any],
    package: str,
    evidence_binding_plan: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    repo_root = task_dir / "repo_snapshot"
    candidate_paths = _candidate_paths_by_type(evidence_binding_plan)
    evidence: list[dict[str, Any]] = []
    for file_item in repo_manifest.get("files", []):
        relative_path = str(file_item["path"])
        full_path = repo_root / relative_path
        if not full_path.exists() or full_path.is_dir():
            continue
        text = full_path.read_text(encoding="utf-8")
        file_digest = sha256_bytes(full_path.read_bytes())
        evidence.append(
            _evidence_item(
                evidence_type="repo_file_digest",
                path=relative_path,
                line_start=None,
                line_end=None,
                excerpt=file_digest,
                file_digest=file_digest,
            )
        )
        if relative_path.endswith("requirements.txt") and _path_allowed(candidate_paths, "dependency_declaration", relative_path):
            evidence.extend(_dependency_evidence(text, relative_path, package, file_digest))
        if relative_path.endswith(".py") and _path_allowed(candidate_paths, "import_use_site", relative_path):
            evidence.extend(_import_use_evidence(text, relative_path, package, file_digest))
    return evidence


def validate_repo_file_digests(*, task_dir: Path, repo_manifest: dict[str, Any]) -> list[dict[str, Any]]:
    repo_root = task_dir / "repo_snapshot"
    checks: list[dict[str, Any]] = []
    for file_item in repo_manifest.get("files", []):
        relative_path = str(file_item["path"])
        full_path = repo_root / relative_path
        exists = full_path.exists() and full_path.is_file()
        actual_digest = sha256_bytes(full_path.read_bytes()) if exists else None
        expected_digest = file_item.get("sha256")
        actual_line_count = len(full_path.read_text(encoding="utf-8").splitlines()) if exists else None
        checks.append(
            {
                "path": relative_path,
                "exists": exists,
                "expected_digest": expected_digest,
                "actual_digest": actual_digest,
                "digest_match": exists and actual_digest == expected_digest,
                "expected_line_count": file_item.get("line_count"),
                "actual_line_count": actual_line_count,
                "line_count_match": exists and actual_line_count == file_item.get("line_count"),
            }
        )
    return checks


def _dependency_evidence(text: str, path: str, package: str, file_digest: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        match = re.fullmatch(rf"\s*{re.escape(package)}==([^\s;]+)\s*", line)
        if not match:
            continue
        rows.append(
            _evidence_item(
                evidence_type="dependency_declaration",
                path=path,
                line_start=line_no,
                line_end=line_no,
                excerpt=line,
                file_digest=file_digest,
                attributes={"package": package, "version": match.group(1)},
            )
        )
        rows.append(
            _evidence_item(
                evidence_type="resolved_version",
                path=path,
                line_start=line_no,
                line_end=line_no,
                excerpt=line,
                file_digest=file_digest,
                attributes={"package": package, "version": match.group(1)},
            )
        )
    return rows


def _candidate_paths_by_type(evidence_binding_plan: dict[str, Any] | None) -> dict[str, set[str]] | None:
    if not evidence_binding_plan:
        return None
    result: dict[str, set[str]] = {}
    for item in evidence_binding_plan.get("binding_plan", []):
        evidence_type = item.get("evidence_type")
        if not evidence_type:
            continue
        if "candidate_paths" in item:
            result[str(evidence_type)] = {str(path) for path in item.get("candidate_paths", [])}
    return result


def _path_allowed(candidate_paths: dict[str, set[str]] | None, evidence_type: str, path: str) -> bool:
    if candidate_paths is None:
        return True
    if evidence_type == "resolved_version":
        allowed = candidate_paths.get("resolved_version") or candidate_paths.get("dependency_declaration")
    else:
        allowed = candidate_paths.get(evidence_type)
    return any(path == candidate or fnmatch(path, candidate) for candidate in (allowed or set()))


def _import_use_evidence(text: str, path: str, package: str, file_digest: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        if not re.search(rf"\bimport\s+{re.escape(package)}\b|\b{re.escape(package)}\.", line):
            continue
        rows.append(
            _evidence_item(
                evidence_type="import_use_site",
                path=path,
                line_start=line_no,
                line_end=line_no,
                excerpt=line.strip(),
                file_digest=file_digest,
                attributes={"package": package},
            )
        )
    return rows


def _evidence_item(
    *,
    evidence_type: str,
    path: str,
    line_start: int | None,
    line_end: int | None,
    excerpt: str,
    file_digest: str,
    attributes: dict[str, Any] | None = None,
) -> dict[str, Any]:
    base = {
        "evidence_type": evidence_type,
        "path": path,
        "line_start": line_start,
        "line_end": line_end,
        "excerpt": excerpt,
        "file_digest": file_digest,
        "attributes": attributes or {},
    }
    return {"evidence_id": sha256_json(base), **base}
