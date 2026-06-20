from __future__ import annotations

import pytest

from expert_skill_system.registry.artifacts import ArtifactCorruptionError, ArtifactStore


def test_content_addressed_store_reuses_digest_and_detects_corruption(tmp_path) -> None:
    store = ArtifactStore(tmp_path / "artifacts")
    first = store.put_json({"b": 2, "a": 1}, schema_version="demo.v1")
    second = store.put_json({"a": 1, "b": 2}, schema_version="demo.v1")

    assert first.digest == second.digest
    assert store.get_json(first) == {"a": 1, "b": 2}

    store.path_for_digest(first.digest).write_bytes(b"corrupt")
    with pytest.raises(ArtifactCorruptionError):
        store.get_bytes(first)

