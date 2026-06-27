from __future__ import annotations

from typing import Any

SUPPORTED_TASK_TYPES = {"dependency_use_triage"}

DEPENDENCY_USE_EVIDENCE = (
    "dependency_declaration",
    "resolved_version",
    "import_use_site",
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
    required_evidence = _normalize_required_evidence(payload.get("required_evidence"))
    candidate_path_overrides = {
        str(key): [str(path) for path in value]
        for key, value in dict(payload.get("candidate_path_overrides", {})).items()
    }
    decision_policy = {
        "version_range_comparison_required": True,
        **dict(payload.get("decision_policy", {})),
    }

    full_binding_plan = [
        {
            "evidence_type": "dependency_declaration",
            "source_kind": "repo_file",
            "candidate_paths": candidate_path_overrides.get(
                "dependency_declaration",
                [path for path in repo_files if path.endswith(("requirements.txt", "pyproject.toml"))],
            ),
            "required_for_decision": True,
        },
        {
            "evidence_type": "resolved_version",
            "source_kind": "repo_file",
            "candidate_paths": candidate_path_overrides.get(
                "resolved_version",
                [path for path in repo_files if path.endswith(("requirements.txt", "pyproject.toml"))],
            ),
            "required_for_decision": True,
        },
        {
            "evidence_type": "import_use_site",
            "source_kind": "repo_source",
            "candidate_paths": candidate_path_overrides.get(
                "import_use_site",
                ["*.py"],
            ),
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
            "depends_on": [item for item in required_evidence if item != "decision_evidence"],
            "required_for_decision": True,
        },
    ]
    binding_plan = [item for item in full_binding_plan if item["evidence_type"] in required_evidence]
    return {
        "schema_version": "evidence_binding_plan.v1",
        "task_type": task_type,
        "skill_requirements": skill_requirements,
        "required_evidence": list(required_evidence),
        "decision_policy": decision_policy,
        "binding_plan": binding_plan,
        "repo_evidence_requirements": [
            item
            for item in ("dependency_declaration", "resolved_version", "import_use_site")
            if item in required_evidence
        ]
        + [
            "repo_file_digest",
        ],
        "knowledge_evidence_requirements": [
            item for item in ("advisory_affected_range",) if item in required_evidence
        ],
        "decision_evidence_requirements": [item for item in ("decision_evidence",) if item in required_evidence],
        "missing_evidence_policy": {
            "policy": "abstain_or_fail_safe",
            "runtime_decision": "unresolved",
            "reason_code": "REQUIRED_EVIDENCE_MISSING",
        },
    }


def _normalize_required_evidence(value: Any) -> tuple[str, ...]:
    if value is None:
        return DEPENDENCY_USE_EVIDENCE
    if not isinstance(value, list | tuple):
        raise ValueError("required_evidence must be a list when provided")
    required = tuple(str(item) for item in value)
    if not required:
        raise ValueError("required_evidence cannot be empty")
    unknown = sorted(set(required) - set(DEPENDENCY_USE_EVIDENCE))
    if unknown:
        raise ValueError(f"unsupported dependency-use evidence type(s): {unknown}")
    if "decision_evidence" not in required:
        raise ValueError("required_evidence must include decision_evidence")
    return required
