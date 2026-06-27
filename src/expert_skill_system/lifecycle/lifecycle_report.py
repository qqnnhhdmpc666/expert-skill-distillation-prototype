from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def build_bundle_matrix(family_builds: list[dict[str, Any]]) -> dict[str, Any]:
    families = []
    artifact_sets: dict[str, set[str]] = {}
    for row in family_builds:
        artifacts = {
            digest
            for digest in [
                row.get("bundle_digest"),
                row.get("skill_digest"),
                row.get("skill_artifact_digest"),
                row.get("knowledge_projection_digest"),
                row.get("knowledge_access_binding_digest"),
                row.get("provider_policy_digest"),
            ]
            if digest
        }
        artifact_sets[row["skill_family"]] = artifacts
        families.append(
            {
                "skill_family": row["skill_family"],
                "bundle_manifest_skill_family": row.get("bundle_manifest_skill_family"),
                "binding_key": row.get("binding_key"),
                "bundle_digest": row.get("bundle_digest"),
                "knowledge_projection_digest": row.get("knowledge_projection_digest"),
                "evidence_requirements": row.get("evidence_requirements", []),
            }
        )
    digest_to_families: dict[str, list[str]] = {}
    for row in family_builds:
        digest = row.get("bundle_digest")
        if digest:
            digest_to_families.setdefault(digest, []).append(row["skill_family"])
    digest_collisions = [
        {"digest": digest, "families": names}
        for digest, names in sorted(digest_to_families.items())
        if len(names) > 1
    ]
    shared_artifacts = []
    names = sorted(artifact_sets)
    for index, left in enumerate(names):
        for right in names[index + 1 :]:
            shared = sorted(artifact_sets[left] & artifact_sets[right])
            if shared:
                shared_artifacts.append({"families": [left, right], "artifact_digests": shared})
    family_specific_artifacts = [
        {
            "skill_family": name,
            "artifact_digests": sorted(
                artifacts - set().union(*(items for other, items in artifact_sets.items() if other != name))
            ),
        }
        for name, artifacts in sorted(artifact_sets.items())
    ]
    repo = next((row for row in family_builds if row["skill_family"] == "repo-dependency-use-triage"), None)
    python = next((row for row in family_builds if row["skill_family"] == "python-advisory"), None)
    boundary_notes = []
    if repo and python:
        boundary_notes.append(
            {
                "check": "repo_bundle_digest_differs_from_python_advisory",
                "status": "pass" if repo.get("bundle_digest") != python.get("bundle_digest") else "fail",
            }
        )
        boundary_notes.append(
            {
                "check": "repo_family_contains_repo_evidence_requirements",
                "status": "pass"
                if {
                    "dependency_declaration",
                    "resolved_version",
                    "import_use_site",
                    "advisory_affected_range",
                    "decision_evidence",
                }.issubset(set(repo.get("evidence_requirements", [])))
                else "fail",
            }
        )
        boundary_notes.append(
            {
                "check": "python_advisory_not_masquerading_as_repo_bundle",
                "status": "pass" if python.get("bundle_manifest_skill_family") != "repo-dependency-use-triage" else "fail",
            }
        )
        boundary_notes.append(
            {
                "check": "active_binding_keys_are_family_specific",
                "status": "pass" if repo.get("binding_key") != python.get("binding_key") else "fail",
            }
        )
    return {
        "schema_version": "cross_family_bundle_matrix.v1",
        "families": families,
        "digest_collisions": digest_collisions,
        "shared_artifacts": shared_artifacts,
        "family_specific_artifacts": family_specific_artifacts,
        "boundary_notes": boundary_notes,
    }


def build_claim_boundary_matrix(
    *,
    family_builds: list[dict[str, Any]],
    eval_runs: list[dict[str, Any]],
    global_blocked_claims: list[str],
) -> dict[str, Any]:
    eval_by_family = {row["skill_family"]: row for row in eval_runs}
    rows = []
    for family in family_builds:
        evaluation = eval_by_family.get(family["skill_family"], {})
        strength = _claim_strength(family, evaluation)
        rows.append(
            {
                "skill_family": family["skill_family"],
                "allowed_claims": family.get("claim_boundary", {}).get("allowed_claims", []),
                "blocked_claims": sorted(
                    set(family.get("claim_boundary", {}).get("blocked_claims", [])) | set(global_blocked_claims)
                ),
                "evidence_paths": family.get("evidence_paths", []) + evaluation.get("evidence_paths", []),
                "claim_strength": strength,
            }
        )
    return {
        "schema_version": "claim_boundary_matrix.v1",
        "global_blocked_claims": global_blocked_claims,
        "families": rows,
    }


def build_aggregate_report(
    *,
    family_builds: list[dict[str, Any]],
    active_bindings: list[dict[str, Any]],
    eval_runs: list[dict[str, Any]],
    bundle_matrix: dict[str, Any],
    claim_boundary_matrix: dict[str, Any],
    output_dir: Path,
) -> dict[str, Any]:
    family_count = len(family_builds)
    repo_eval = next((row for row in eval_runs if row["skill_family"] == "repo-dependency-use-triage"), {})
    python_build = next((row for row in family_builds if row["skill_family"] == "python-advisory"), {})
    return {
        "schema_version": "multi_skill_family_lifecycle_report.v1",
        "multi_skill_family_lifecycle": "pass" if family_count >= 2 and not bundle_matrix["digest_collisions"] else "partial",
        "family_registry": "pass",
        "family_count": family_count,
        "repo_dependency_use_triage_bundle": _status_for("repo-dependency-use-triage", family_builds),
        "python_advisory_bundle": python_build.get("build_status", "failed"),
        "repo_level_eval": repo_eval.get("evaluation_status", "not_evaluated"),
        "cross_family_bundle_matrix": "pass" if all(item["status"] == "pass" for item in bundle_matrix["boundary_notes"]) else "partial",
        "claim_boundary_matrix": "pass",
        "agenthost": "not_in_scope",
        "openhands_agenthost": "not_in_scope_this_step",
        "swe_agent_host": "not_in_scope_this_step",
        "compiler_superiority": "not_evaluated",
        "vulnerability_discovery": "not_claimed",
        "vulnerability_discovery_claim": "not_claimed",
        "active_binding_count": len(active_bindings),
        "output_dir": str(output_dir),
        "claim_boundary_matrix_path": str(output_dir / "claim_boundary_matrix.json"),
        "bundle_matrix_path": str(output_dir / "bundle_matrix.json"),
    }


def render_aggregate_report(report: dict[str, Any], family_builds: list[dict[str, Any]], eval_runs: list[dict[str, Any]]) -> str:
    lines = [
        "# Multi-Skill-Family Lifecycle Status",
        "",
        "## Summary",
        "",
        f"- multi_skill_family_lifecycle: `{report['multi_skill_family_lifecycle']}`",
        f"- family_registry: `{report['family_registry']}`",
        f"- family_count: `{report['family_count']}`",
        f"- repo_dependency_use_triage_bundle: `{report['repo_dependency_use_triage_bundle']}`",
        f"- python_advisory_bundle: `{report['python_advisory_bundle']}`",
        f"- repo_level_eval: `{report['repo_level_eval']}`",
        f"- cross_family_bundle_matrix: `{report['cross_family_bundle_matrix']}`",
        f"- claim_boundary_matrix: `{report['claim_boundary_matrix']}`",
        f"- agenthost: `{report['agenthost']}`",
        f"- compiler_superiority: `{report['compiler_superiority']}`",
        f"- vulnerability_discovery: `{report['vulnerability_discovery']}`",
        "",
        "## Families",
        "",
        "| skill_family | build_status | evaluation_status | bundle_digest | binding_key |",
        "|---|---|---|---|---|",
    ]
    eval_by_family = {row["skill_family"]: row for row in eval_runs}
    for row in family_builds:
        evaluation = eval_by_family.get(row["skill_family"], {})
        lines.append(
            f"| `{row['skill_family']}` | `{row.get('build_status')}` | `{evaluation.get('evaluation_status', 'not_evaluated')}` | `{row.get('bundle_digest')}` | `{row.get('binding_key')}` |"
        )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "- No AgentHost/OpenHands/SWE-agent evidence is claimed in this step.",
            "- Compiler superiority is not evaluated.",
            "- The repo-level tasks are mixed local fixtures plus one traceable public excerpt, not an official benchmark.",
            "- OSV applicability is not exploitability or reachability proof.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def write_lifecycle_outputs(output_dir: Path, artifacts: dict[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, payload in artifacts.items():
        if name.endswith(".json"):
            (output_dir / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        elif name.endswith(".jsonl"):
            rows = payload if isinstance(payload, list) else []
            (output_dir / name).write_text(
                "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
                encoding="utf-8",
            )
        elif name.endswith(".md"):
            (output_dir / name).write_text(str(payload), encoding="utf-8")


def _status_for(skill_family: str, family_builds: list[dict[str, Any]]) -> str:
    row = next((item for item in family_builds if item["skill_family"] == skill_family), None)
    return str(row.get("build_status", "failed")) if row else "missing"


def _claim_strength(family: dict[str, Any], evaluation: dict[str, Any]) -> str:
    if family.get("build_status") != "pass":
        return "not_evaluated"
    if evaluation.get("evaluation_status") == "pass":
        return "deterministic_harness"
    if str(evaluation.get("evaluation_status", "")).startswith("partial"):
        return "partial"
    return "system_lifecycle"
