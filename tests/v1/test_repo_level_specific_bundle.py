from __future__ import annotations

import json
from pathlib import Path

from expert_skill_system.compiler.repo_level_bundle_builder import REPO_LEVEL_SKILL_ID, RepoLevelBundleBuilder
from expert_skill_system.core.models import ArtifactRef
from expert_skill_system.evaluation.repo_security_task import run_dependency_use_triage
from expert_skill_system.registry.workspace import Workspace
from expert_skill_system.runtime.release_bundle_resolver import resolve_release_bundle

DATA_DIR = Path("data/repo_level_bundle")


def test_repo_level_specific_bundle_contains_dependency_use_triage_requirements(tmp_path: Path) -> None:
    workspace = Workspace.open(tmp_path / "state")
    result = RepoLevelBundleBuilder(workspace).build(data_dir=DATA_DIR, promote=True)

    assert result.status == "pass"
    assert result.skill_family == REPO_LEVEL_SKILL_ID
    assert result.bundle_digest != result.skill_ir_digest

    resolved = resolve_release_bundle(
        state_dir=tmp_path / "state",
        use_active_binding=True,
        binding_key=REPO_LEVEL_SKILL_ID,
    )
    assert resolved["bundle_attachment_mode"] == "real_release_bundle_pinned"
    assert resolved["skill_family"] == REPO_LEVEL_SKILL_ID
    assert resolved["limitation"] is None

    manifest = resolved["bundle_manifest"]
    skill = workspace.artifacts.get_json(ArtifactRef.from_dict(manifest["skill_ir_refs"][0]))
    assert skill["invocation"]["task_family"] == REPO_LEVEL_SKILL_ID
    requirement_names = {item["semantic_requirement"] for item in skill["knowledge_requirements"]}
    assert requirement_names == {
        "dependency_declaration",
        "resolved_version",
        "import_use_site",
        "advisory_affected_range",
        "decision_evidence",
    }

    access = workspace.artifacts.get_json(ArtifactRef.from_dict(manifest["knowledge_access_binding_refs"][0]))
    evidence_binding_ref = ArtifactRef.from_dict(access["evidence_binding_plan_ref"])
    evidence_binding = workspace.artifacts.get_json(evidence_binding_ref)
    assert evidence_binding["task_type"] == "dependency_use_triage"
    assert evidence_binding["missing_evidence_policy"]["policy"] == "abstain_or_fail_safe"
    assert evidence_binding["required_evidence"] == [
        "dependency_declaration",
        "resolved_version",
        "import_use_site",
        "advisory_affected_range",
        "decision_evidence",
    ]


def test_repo_level_specific_bundle_drives_repo_harness_provenance(tmp_path: Path) -> None:
    workspace = Workspace.open(tmp_path / "state")
    result = RepoLevelBundleBuilder(workspace).build(data_dir=DATA_DIR, promote=True)
    resolved = resolve_release_bundle(
        state_dir=tmp_path / "state",
        use_active_binding=True,
        binding_key=REPO_LEVEL_SKILL_ID,
    )

    run = run_dependency_use_triage(
        Path("data/repo_security_tasks/dependency_use_triage_requests_demo"),
        tmp_path / "run",
        bundle_resolution=resolved,
    )
    assert run["verifier_pass"] is True
    provenance = json.loads((tmp_path / "run" / "trajectory_evidence" / "provenance.json").read_text(encoding="utf-8"))
    assert provenance["bundle_digest"] == result.bundle_digest
    assert provenance["skill_family"] == REPO_LEVEL_SKILL_ID
    assert provenance["knowledge_access_binding_digest"] == result.knowledge_access_binding_digest
    assert provenance["provider_policy_digest"] == result.provider_policy_digest


def test_missing_import_use_does_not_become_used_and_affected(tmp_path: Path) -> None:
    run = run_dependency_use_triage(
        Path("data/repo_security_tasks/dependency_use_triage_declared_not_used"),
        tmp_path / "declared_not_used",
    )
    prediction = json.loads(Path(run["prediction_path"]).read_text(encoding="utf-8"))
    assert run["verifier_pass"] is True
    assert prediction["decision"] == "dependency_present_not_used"
    assert prediction["decision"] != "dependency_used_and_affected"
