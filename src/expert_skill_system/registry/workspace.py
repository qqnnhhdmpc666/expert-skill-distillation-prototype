from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..core.models import ArtifactRef
from .artifacts import ArtifactStore
from .metadata import MetadataStore


@dataclass
class Workspace:
    root: Path
    artifacts: ArtifactStore
    metadata: MetadataStore

    @classmethod
    def open(cls, root: Path) -> Workspace:
        resolved = root.resolve()
        resolved.mkdir(parents=True, exist_ok=True)
        return cls(
            root=resolved,
            artifacts=ArtifactStore(resolved / "artifacts" / "sha256"),
            metadata=MetadataStore(resolved / "metadata.sqlite"),
        )

    def put_json(self, payload: Any, *, schema_version: str, artifact_id: str | None = None) -> ArtifactRef:
        ref = self.artifacts.put_json(payload, schema_version=schema_version, artifact_id=artifact_id)
        self.metadata.register_artifact(ref)
        return ref

    def put_bytes(self, payload: bytes, *, media_type: str, schema_version: str, artifact_id: str | None = None) -> ArtifactRef:
        ref = self.artifacts.put_bytes(payload, media_type=media_type, schema_version=schema_version, artifact_id=artifact_id)
        self.metadata.register_artifact(ref)
        return ref

