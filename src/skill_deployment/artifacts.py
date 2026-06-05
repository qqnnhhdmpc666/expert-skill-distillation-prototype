from __future__ import annotations

import fnmatch
import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ManifestCheckResult:
    manifest_path: str
    ok: bool
    missing_fields: tuple[str, ...]
    missing_artifacts: tuple[str, ...]


def _artifact_exists(root: Path, pattern: str) -> bool:
    if any(char in pattern for char in "*?[]"):
        return any(fnmatch.fnmatch(str(path.relative_to(root)).replace("\\", "/"), pattern) for path in root.rglob("*"))
    return (root / pattern).exists()


def check_artifact_manifest(run_dir: Path) -> ManifestCheckResult:
    manifest_path = run_dir / "manifest.json"
    if not manifest_path.exists():
        return ManifestCheckResult(str(manifest_path), False, ("manifest.json",), ())
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    required_fields = ("run_id", "created_at", "artifacts")
    missing_fields = tuple(field for field in required_fields if field not in payload)
    artifacts = payload.get("artifacts", [])
    missing_artifacts = tuple(str(item) for item in artifacts if not _artifact_exists(run_dir, str(item)))
    return ManifestCheckResult(
        manifest_path=str(manifest_path),
        ok=not missing_fields and not missing_artifacts,
        missing_fields=missing_fields,
        missing_artifacts=missing_artifacts,
    )

