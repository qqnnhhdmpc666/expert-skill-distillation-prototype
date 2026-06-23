from __future__ import annotations

import pytest

from expert_skill_system.compiler.evidence_binding import bind_task_aware_evidence


def test_dependency_use_evidence_binding_declares_required_evidence() -> None:
    result = bind_task_aware_evidence(
        {
            "task_type": "dependency_use_triage",
            "skill_requirements": ["identify dependency declaration"],
            "available_knowledge_sources": ["PYSEC-2018-28"],
            "repo_manifest": {
                "files": [
                    {"path": "requirements.txt"},
                    {"path": "src/app/client.py"},
                ]
            },
        }
    )
    assert result["schema_version"] == "evidence_binding_plan.v1"
    assert set(result["required_evidence"]) == {
        "dependency_declaration",
        "resolved_version",
        "import_or_use_site",
        "advisory_affected_range",
        "decision_evidence",
    }
    assert result["missing_evidence_policy"]["policy"] == "abstain_or_fail_safe"
    assert any(item["evidence_type"] == "import_or_use_site" for item in result["binding_plan"])


def test_evidence_binding_rejects_unsupported_task_type() -> None:
    with pytest.raises(ValueError, match="unsupported task_type"):
        bind_task_aware_evidence({"task_type": "vulnerability_discovery"})
