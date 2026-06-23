from __future__ import annotations

from typing import Any

SUPPORTED_TASK_TYPES = {"dependency_use_triage"}

DEPENDENCY_USE_EVIDENCE = (
    "dependency_declaration",
    "resolved_version",
    "import_or_use_site",
    "advisory_affected_range",
    "decision_evidence",
)


def bind_task_aware_evidence(payload: dict[str, Any]) -> dict[str, Any]:
    """Plan task-specific evidence requirements before runtime execution.

    This is intentionally a small algorithmic hook: it does not retrieve
    evidence itself, and it does not inspect verifier-only gold labels.
    """

    task_type = str(payload.get("task_type", ""))
    if task_type not in SUPPORTED_TASK_TYPES:
        raise ValueError(f"unsupported task_type: {task_type!r}")
    skill_requirements = list(payload.get("skill_requirements", []))
    knowledge_sources = list(payload.get("available_knowledge_sources", []))
    repo_manifest = dict(payload.get("repo_manifest", {}))
    repo_files = [item.get("path") for item in repo_manifest.get("files", []) if item.get("path")]

    binding_plan = [
        {
            "evidence_type": "dependency_declaration",
            "source_kind": "repo_file",
            "candidate_paths": [path for path in repo_files if path.endswith(("requirements.txt", "pyproject.toml"))],
            "required_for_decision": True,
        },
        {
            "evidence_type": "resolved_version",
            "source_kind": "repo_file",
            "candidate_paths": [path for path in repo_files if path.endswith(("requirements.txt", "pyproject.toml"))],
            "required_for_decision": True,
        },
        {
            "evidence_type": "import_or_use_site",
            "source_kind": "repo_source",
            "candidate_paths": [path for path in repo_files if path.endswith(".py")],
            "required_for_decision": True,
        },
        {
            "evidence_type": "advisory_affected_range",
            "source_kind": "allowed_knowledge",
            "candidate_sources": knowledge_sources,
            "required_for_decision": True,
        },
        {
            "evidence_type": "decision_evidence",
            "source_kind": "derived",
            "depends_on": list(DEPENDENCY_USE_EVIDENCE[:-1]),
            "required_for_decision": True,
        },
    ]
    return {
        "schema_version": "evidence_binding_plan.v1",
        "task_type": task_type,
        "skill_requirements": skill_requirements,
        "required_evidence": list(DEPENDENCY_USE_EVIDENCE),
        "binding_plan": binding_plan,
        "missing_evidence_policy": {
            "policy": "abstain_or_fail_safe",
            "runtime_decision": "unresolved",
            "reason_code": "REQUIRED_EVIDENCE_MISSING",
        },
    }
