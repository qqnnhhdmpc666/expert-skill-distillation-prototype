from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any

from ..core.canonical import canonical_json_bytes, sha256_bytes
from ..core.models import ArtifactRef


class ArtifactCorruptionError(RuntimeError):
    pass


class ArtifactStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def path_for_digest(self, digest: str) -> Path:
        if not digest.startswith("sha256:") or len(digest) != 71:
            raise ValueError(f"invalid sha256 digest: {digest}")
        hex_digest = digest.removeprefix("sha256:")
        return self.root / hex_digest[:2] / hex_digest

    def put_bytes(self, payload: bytes, *, media_type: str, schema_version: str, artifact_id: str | None = None) -> ArtifactRef:
        digest = sha256_bytes(payload)
        target = self.path_for_digest(digest)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            existing = target.read_bytes()
            if sha256_bytes(existing) != digest:
                raise ArtifactCorruptionError(f"stored artifact does not match its path digest: {target}")
        else:
            fd, temporary_name = tempfile.mkstemp(prefix=".artifact-", dir=target.parent)
            try:
                with os.fdopen(fd, "wb") as handle:
                    handle.write(payload)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(temporary_name, target)
            finally:
                temporary = Path(temporary_name)
                if temporary.exists():
                    temporary.unlink()
        return ArtifactRef(
            artifact_id=artifact_id or f"{schema_version}:{digest[-16:]}",
            digest=digest,
            media_type=media_type,
            artifact_schema_version=schema_version,
            size_bytes=len(payload),
        )

    def put_json(self, payload: Any, *, schema_version: str, artifact_id: str | None = None) -> ArtifactRef:
        return self.put_bytes(
            canonical_json_bytes(payload),
            media_type="application/json",
            schema_version=schema_version,
            artifact_id=artifact_id,
        )

    def get_bytes(self, ref: ArtifactRef) -> bytes:
        path = self.path_for_digest(ref.digest)
        if not path.exists():
            raise FileNotFoundError(f"artifact not found: {ref.digest}")
        payload = path.read_bytes()
        if sha256_bytes(payload) != ref.digest:
            raise ArtifactCorruptionError(f"artifact digest mismatch: {ref.digest}")
        return payload

    def get_json(self, ref: ArtifactRef) -> Any:
        import json

        return json.loads(self.get_bytes(ref).decode("utf-8"))

    def contains(self, ref: ArtifactRef) -> bool:
        try:
            self.get_bytes(ref)
        except (FileNotFoundError, ArtifactCorruptionError):
            return False
        return True

