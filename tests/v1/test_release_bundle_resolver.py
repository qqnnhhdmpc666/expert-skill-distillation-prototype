from __future__ import annotations

from pathlib import Path

import pytest

from expert_skill_system.runtime.release_bundle_resolver import BundleResolutionError, resolve_release_bundle


def test_release_bundle_resolver_requires_real_bundle_by_default(tmp_path: Path) -> None:
    with pytest.raises(BundleResolutionError, match="bundle_not_available"):
        resolve_release_bundle(state_dir=tmp_path / "state", use_active_binding=True)


def test_release_bundle_resolver_can_record_explicit_partial_mode(tmp_path: Path) -> None:
    result = resolve_release_bundle(
        state_dir=tmp_path / "state",
        use_active_binding=True,
        allow_local_manifest_only=True,
    )
    assert result["bundle_attachment_mode"] == "partial_local_manifest_only"
    assert result["bundle_digest"] is None
    assert "bundle_not_available" in result["limitation"]
