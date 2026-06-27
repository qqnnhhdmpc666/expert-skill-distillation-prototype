from __future__ import annotations

import pytest

from expert_skill_system.registry.metadata import ConcurrentBindingUpdate
from expert_skill_system.registry.workspace import Workspace


def test_active_binding_cas_rejection_and_rollback_are_real_transactions(tmp_path) -> None:
    workspace = Workspace.open(tmp_path / ".eskill")
    bundle_a = workspace.put_json({"bundle": "A"}, schema_version="release_bundle.v1")
    bundle_b = workspace.put_json({"bundle": "B"}, schema_version="release_bundle.v1")
    bundle_c = workspace.put_json({"bundle": "C"}, schema_version="release_bundle.v1")

    active_a = workspace.metadata.change_binding(
        binding_key="python-advisory/default", target_digest=bundle_a.digest, expected_generation=0, event_type="promote"
    )
    assert active_a.generation == 1

    with pytest.raises(ConcurrentBindingUpdate):
        workspace.metadata.change_binding(
            binding_key="python-advisory/default", target_digest=bundle_b.digest, expected_generation=0, event_type="promote"
        )

    active_b = workspace.metadata.change_binding(
        binding_key="python-advisory/default", target_digest=bundle_b.digest, expected_generation=1, event_type="promote"
    )
    rejected = workspace.metadata.record_rejection(
        binding_key="python-advisory/default", candidate_digest=bundle_c.digest, reason_codes=("SCOPE_OVERREACH",)
    )
    assert rejected.generation_after == active_b.generation
    assert workspace.metadata.get_active_binding("python-advisory/default").bundle_digest == bundle_b.digest

    rolled_back = workspace.metadata.change_binding(
        binding_key="python-advisory/default", target_digest=bundle_a.digest, expected_generation=2, event_type="rollback"
    )
    assert rolled_back.bundle_digest == bundle_a.digest
    assert [row["event_type"] for row in workspace.metadata.deployment_history("python-advisory/default")] == [
        "promote",
        "promote",
        "reject",
        "rollback",
    ]

