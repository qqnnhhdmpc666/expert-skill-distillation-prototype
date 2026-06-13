from __future__ import annotations

import argparse
import difflib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from skill_deployment import ControlledTaskCase, SkillPackage, controlled_task_case_from_directory  # noqa: E402
from skill_deployment.evidence import write_json, write_text  # noqa: E402
from skill_deployment.install_state import load_active_pointer, read_skill_version, skill_version_dir  # noqa: E402
from skill_deployment.qualification import build_skill_qualification_cards  # noqa: E402

import scripts.run_skill_marginal_utility as marginal  # noqa: E402


OUTPUT_ROOT = ROOT / "outputs" / "skill_evolution_lab" / "secure_code_review"
MARGINAL_ROOT = ROOT / "outputs" / "validation" / "skill_marginal_utility"
INSTALL_ROOT = ROOT / "outputs" / "installed_skills"
CONFIG_CASE_DIR = ROOT / "data" / "task_cases" / "config_security_001"
MINI_SUITE_CASES = ROOT / "data" / "external_security_mini_suite" / "cases.json"
MINI_SUITE_SUMMARY = ROOT / "outputs" / "external_security_mini_suite" / "mini_suite_summary.json"
MINI_SUITE_LIMITATIONS = ROOT / "outputs" / "external_security_mini_suite" / "limitation_or_rejected_evidence.json"
SMALL_CANDIDATE_REPORT = ROOT / "reports" / "SMALL_CANDIDATE_EVOLUTION_STATUS.md"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def ensure_marginal_utility() -> dict[str, Any]:
    path = MARGINAL_ROOT / "skill_marginal_utility.json"
    if not path.exists():
        marginal.main(["--cases", "upload,data_quality", "--backend", "offline_deterministic", "--output-dir", str(MARGINAL_ROOT)])
    return load_json(path)


def build_trajectory_store(marginal_payload: dict[str, Any], cards_payload: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for row in marginal_payload.get("results", []):
        metrics = row["metrics"]
        status = "success" if metrics["v2_over_v1_gain"] > 0 and metrics["false_positive_delta"] <= 0 else "inconclusive"
        records.append(
            {
                "record_id": f"marginal::{row['case_id']}",
                "case_id": row["case_id"],
                "source": row["artifact_dir"],
                "status": status,
                "evidence_type": "marginal_utility",
                "v2_over_v1_gain": metrics["v2_over_v1_gain"],
                "v2_over_no_skill_gain": metrics["v2_over_no_skill_gain"],
                "single_trajectory_can_patch_skill": False,
            }
        )
    for card in cards_payload.get("cards", []):
        if card.get("card_type") != "RevisionQualificationCard":
            continue
        decision = card.get("qualification_decision")
        status = "success" if decision == "promote_with_scope_limit" else "failure"
        records.append(
            {
                "record_id": f"qualification::{card['card_id']}",
                "case_id": card.get("scenario", card["card_id"]),
                "source": card["artifact"],
                "status": status,
                "evidence_type": "qualification_card",
                "decision": decision,
                "single_trajectory_can_patch_skill": False,
            }
        )
    return records


def build_failure_contrast(cards_payload: dict[str, Any]) -> list[dict[str, Any]]:
    contrasts: list[dict[str, Any]] = []
    for card in cards_payload.get("cards", []):
        if card.get("card_type") != "RevisionQualificationCard":
            continue
        gates = card.get("gates", {})
        integrity = gates.get("integrity_gate", {})
        behavior = gates.get("behavior_gate", {})
        if card.get("qualification_decision") in {"reject", "quarantine"}:
            contrasts.append(
                {
                    "case_id": card.get("scenario", card["card_id"]),
                    "artifact": card["artifact"],
                    "a1_failure_pattern": card.get("observed_delta", {}).get("a1_feedback_type", "unknown"),
                    "a2_success_pattern": "none",
                    "contrastive_lesson": behavior.get("evidence") or integrity.get("evidence", ""),
                    "text_gradient": text_gradient_for_failure(card),
                    "candidate_patch": "do_not_promote_without_manifest_diff_and_behavior_gain",
                    "patch_risk": integrity.get("failure_origin") or behavior.get("failure_origin") or "unclassified_failure",
                }
            )
    return contrasts


def text_gradient_for_failure(card: dict[str, Any]) -> str:
    card_id = card["card_id"]
    if "config" in card_id:
        return "Capability presence is insufficient; output templates must force realization in the generated finding."
    if "api" in card_id:
        return "Patch operators must verify a manifest diff before rerun; no-op capability patches must be rejected early."
    return "Rejected or quarantined edits must be converted into bounded operator constraints before another proposal."


def build_candidate_pool(marginal_payload: dict[str, Any], budget: int) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for row in marginal_payload.get("results", []):
        metrics = row["metrics"]
        if metrics["v2_over_v1_gain"] <= 0:
            continue
        candidates.append(
            {
                "candidate_id": f"candidate_{row['case_id']}_v2",
                "case_id": row["case_id"],
                "source": row["artifact_dir"],
                "proposal_type": "bounded_skill_v2_promotion",
                "edit_budget": min(budget, 3),
                "protected_sections": ["Safety Boundary", "Output Contract", "Qualification Scope"],
                "marginal_utility": metrics,
                "status": "candidate",
            }
        )
    return candidates[:budget]


def build_rejected_buffer(contrasts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rejected = []
    for item in contrasts:
        rejected.append(
            {
                "rejected_edit_id": f"rejected::{item['case_id']}",
                "case_id": item["case_id"],
                "reason": item["patch_risk"],
                "score_delta": -1.0,
                "text_gradient": item["text_gradient"],
                "avoid_next": item["candidate_patch"],
            }
        )
    if not rejected:
        rejected.append(
            {
                "rejected_edit_id": "rejected::synthetic_no_single_trace_patch",
                "case_id": "policy",
                "reason": "single_trajectory_overfit_risk",
                "score_delta": 0.0,
                "text_gradient": "Do not rewrite a Skill from one isolated trajectory; require repeated evidence or validation-set gain.",
                "avoid_next": "single_badcase_direct_patch",
            }
        )
    return rejected


def build_elite_pool(candidates: list[dict[str, Any]], k: int) -> list[dict[str, Any]]:
    ranked = sorted(
        candidates,
        key=lambda item: (
            item["marginal_utility"]["v2_over_v1_gain"],
            item["marginal_utility"]["v2_over_no_skill_gain"],
            -item["marginal_utility"]["false_positive_delta"],
        ),
        reverse=True,
    )
    elite = []
    for rank, item in enumerate(ranked[:k], start=1):
        elite.append(
            {
                "rank": rank,
                "candidate_id": item["candidate_id"],
                "case_id": item["case_id"],
                "selection_rule": "strict_positive_marginal_gain_and_no_false_positive_increase",
                "status": "elite_candidate",
                "marginal_utility": item["marginal_utility"],
            }
        )
    return elite


def build_retirement_decisions(cards_payload: dict[str, Any], marginal_payload: dict[str, Any], rejected: list[dict[str, Any]]) -> list[dict[str, Any]]:
    decisions: list[dict[str, Any]] = []
    rejected_by_case = Counter(item["case_id"] for item in rejected)
    for card in cards_payload.get("cards", []):
        if card.get("card_type") != "RevisionQualificationCard":
            continue
        decision = card.get("qualification_decision")
        if decision == "reject":
            action = "retire"
        elif decision == "quarantine":
            action = "quarantine"
        else:
            continue
        case_id = str(card.get("scenario", card["card_id"]))
        decisions.append(
            {
                "skill_id": card["card_id"],
                "case_id": case_id,
                "action": action,
                "trigger": card.get("gates", {}).get("behavior_gate", {}).get("failure_origin")
                or card.get("gates", {}).get("integrity_gate", {}).get("failure_origin")
                or "non_promotable_qualification",
                "evidence": card["artifact"],
                "rejected_edit_count": rejected_by_case.get(case_id, 0),
            }
        )
    for row in marginal_payload.get("results", []):
        metrics = row["metrics"]
        if metrics["v2_over_v1_gain"] <= 0 or metrics["false_positive_delta"] > 0:
            decisions.append(
                {
                    "skill_id": f"{row['case_id']}_v2",
                    "case_id": row["case_id"],
                    "action": "downgrade",
                    "trigger": "no_positive_marginal_gain_or_false_positive_increase",
                    "evidence": row["artifact_dir"],
                    "rejected_edit_count": rejected_by_case.get(row["case_id"], 0),
                }
            )
    return decisions


def build_skill_state_registry(retirement: list[dict[str, Any]], elite: list[dict[str, Any]]) -> dict[str, Any]:
    retirement_by_case = {str(item["case_id"]): item for item in retirement}
    elite_cases = {str(item["case_id"]) for item in elite}
    base_registry_path = INSTALL_ROOT / "registry.json"
    base_registry = load_json(base_registry_path) if base_registry_path.exists() else {"skills": []}
    rows = []
    for row in base_registry.get("skills", []):
        skill_id = str(row.get("skill_id", row.get("case_id", "unknown")))
        decision = retirement_by_case.get(skill_id)
        if decision:
            lifecycle_state = decision["action"]
            reason = decision["trigger"]
        elif skill_id in elite_cases:
            lifecycle_state = "elite_candidate"
            reason = "positive_marginal_utility_candidate"
        else:
            lifecycle_state = "installed_controlled"
            reason = "no_new_evolution_decision"
        rows.append({**row, "evolution_state": lifecycle_state, "evolution_reason": reason})
    return {
        "generated_at": utc_now(),
        "registry_type": "controlled_skill_evolution_state_overlay",
        "source_registry": "outputs/installed_skills/registry.json",
        "skills": rows,
        "boundary": "This overlays evolution states on the generated install registry; it is not a production package manager.",
    }


def render_text_gradient(contrasts: list[dict[str, Any]], rejected: list[dict[str, Any]]) -> str:
    lines = [
        "# Text Gradients From Failure Contrast",
        "",
        "These gradients are optimizer-facing constraints. They are not direct Skill edits.",
        "",
    ]
    for item in contrasts:
        lines.extend(
            [
                f"## {item['case_id']}",
                "",
                f"- Failure pattern: `{item['a1_failure_pattern']}`",
                f"- Lesson: {item['contrastive_lesson']}",
                f"- Text gradient: {item['text_gradient']}",
                f"- Patch risk: `{item['patch_risk']}`",
                "",
            ]
        )
    lines.extend(["## Rejected Edit Memory", ""])
    for item in rejected:
        lines.append(f"- `{item['rejected_edit_id']}`: {item['text_gradient']}")
    return "\n".join(lines) + "\n"


def render_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Skill Evolution Lab Report",
        "",
        f"- Suite: `{payload['suite']}`",
        f"- Gate: `{payload['gate']}`",
        f"- Candidate count: `{len(payload['candidate_pool'])}`",
        f"- Elite count: `{len(payload['elite_pool'])}`",
        f"- Rejected edits: `{len(payload['rejected_edit_buffer'])}`",
        f"- Retirement decisions: `{len(payload['retirement_decisions'])}`",
        "",
        "## Boundary",
        "",
        "This is a minimal controlled evolution lab. It prevents single-trajectory direct Skill edits and records rejected edits, marginal utility, and retirement decisions before promotion.",
    ]
    return "\n".join(lines) + "\n"


def build_candidate_from_contrast(contrast: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    case = controlled_task_case_from_directory(CONFIG_CASE_DIR)
    baseline_v2 = SkillPackage(
        skill_id=case.case_id,
        version="v2",
        task_family=case.task_family,
        capabilities=case.expected_capabilities,
        output_contract=("capability_id", "evidence_span", "recommended_fix"),
        trace_contract=("trajectory.jsonl", "target_reads.json", "skill_reads.json"),
        metadata={"source": "offline_expected_capability_baseline"},
    )
    baseline_text = marginal.render_skill(case.case_id, case.task_family, baseline_v2.capabilities, "v2")
    candidate_id = f"{case.case_id}__v3_candidate_001"
    candidate_dir = out_dir / "candidates" / candidate_id
    candidate_text = baseline_text + "\n## Candidate Realization Constraint\n\n- Force explicit expression of CONFIG_ENV_GUARD in the generated finding.\n"
    candidate_manifest = SkillPackage(
        skill_id=case.case_id,
        version="v3",
        task_family=case.task_family,
        capabilities=baseline_v2.capabilities,
        output_contract=baseline_v2.output_contract,
        trace_contract=baseline_v2.trace_contract,
        metadata={
            "candidate_id": candidate_id,
            "contrast_case_id": contrast["case_id"],
            "text_gradient": contrast["text_gradient"],
            "patch_risk": contrast["patch_risk"],
        },
    ).to_dict()
    write_text(candidate_dir / "SKILL.v3.md", candidate_text)
    write_json(candidate_dir / "manifest.v3.json", candidate_manifest)
    write_text(candidate_dir / "SKILL.md", candidate_text)
    write_json(candidate_dir / "manifest.json", candidate_manifest)
    diff = "\n".join(
        difflib.unified_diff(
            baseline_text.splitlines(),
            candidate_text.splitlines(),
            fromfile="SKILL.v2.md",
            tofile="SKILL.v3.md",
            lineterm="",
        )
    )
    write_text(candidate_dir / "skill_diff.md", diff + "\n")
    return {
        "candidate_id": candidate_id,
        "candidate_dir": candidate_dir,
        "baseline_skill": baseline_v2,
        "baseline_text": baseline_text,
        "candidate_skill": SkillPackage.from_dict(candidate_manifest),
        "candidate_text": candidate_text,
        "case": case,
    }


def validate_candidate(candidate: dict[str, Any], output_root: Path) -> tuple[dict[str, Any], dict[str, Any] | None]:
    baseline_spec = marginal.VariantSpec(name="skill_v2", skill=candidate["baseline_skill"], skill_text=candidate["baseline_text"])
    candidate_spec = marginal.VariantSpec(
        name="candidate_v3",
        skill=candidate["candidate_skill"],
        skill_text=candidate["candidate_text"],
        skill_dir=candidate["candidate_dir"],
    )
    validation = marginal.compare_two_variants(candidate["case"], "offline_deterministic", baseline_spec, candidate_spec, output_root / "candidate_validation")
    promoted = validation["score_delta"] > 0 and validation["false_positive_delta"] <= 0 and validation["schema_error_delta"] <= 0
    decision = {
        "candidate_id": candidate["candidate_id"],
        "decision": "promote" if promoted else "not_promoted",
        "reason": "strictly_better_than_v2" if promoted else "candidate_v3_not_strictly_better_than_v2",
        "score_delta": validation["score_delta"],
        "false_positive_delta": validation["false_positive_delta"],
        "schema_error_delta": validation["schema_error_delta"],
    }
    rejected = None
    if not promoted:
        rejected = {
            "rejected_edit_id": f"rejected::{candidate['candidate_id']}",
            "case_id": candidate["case"].case_id,
            "reason": decision["reason"],
            "score_delta": validation["score_delta"],
            "text_gradient": candidate["candidate_skill"].metadata.get("text_gradient", "candidate not better than v2"),
            "avoid_next": "do_not_promote_without_strict_gain_over_v2",
        }
    return validation, rejected if rejected is not None else None


def load_active_secure_skill() -> dict[str, Any]:
    pointer = load_active_pointer(ROOT, "secure_code_review")
    active_version = str(pointer.get("active_version") or "v2")
    active_dir = Path(str(pointer.get("skill_dir") or skill_version_dir(ROOT, "secure_code_review", active_version))).resolve()
    if not active_dir.exists():
        active_dir = skill_version_dir(ROOT, "secure_code_review", "v2")
    package, skill_text, manifest = read_skill_version(active_dir)
    return {
        "pointer": pointer,
        "active_dir": active_dir,
        "package": package,
        "skill_text": skill_text,
        "manifest": manifest,
    }


def clone_package_with_metadata(base: SkillPackage, *, version: str, metadata_updates: dict[str, Any]) -> SkillPackage:
    metadata = dict(base.metadata or {})
    for key, value in metadata_updates.items():
        metadata[key] = value
    return SkillPackage(
        skill_id=base.skill_id,
        version=version,
        task_family=base.task_family,
        capabilities=base.capabilities,
        output_contract=base.output_contract,
        trace_contract=base.trace_contract,
        metadata=metadata,
    )


def updated_groups(base: SkillPackage, updater) -> list[dict[str, Any]]:
    groups: list[dict[str, Any]] = []
    for group in base.metadata.get("capability_groups", []):
        if isinstance(group, dict):
            groups.append({key: list(value) if isinstance(value, list) else value for key, value in group.items()})
    return updater(groups)


def render_candidate_text(base_text: str, title: str, rationale: str, scope_note: str) -> str:
    return "\n".join(
        [
            base_text.rstrip(),
            "",
            f"## Candidate Constraint: {title}",
            "",
            f"- Evidence-bound rationale: {rationale}",
            f"- Scope note: {scope_note}",
            "- Promotion requires strict score gain, no false-positive increase, no schema-error increase, and no scope violation.",
            "",
        ]
    )


def load_mini_suite_cases_by_id() -> dict[str, dict[str, Any]]:
    if not MINI_SUITE_CASES.exists():
        return {}
    payload = load_json(MINI_SUITE_CASES)
    return {str(item["case_id"]): item for item in payload.get("cases", [])}


def mini_case_to_controlled(case_payload: dict[str, Any]) -> ControlledTaskCase:
    visible = case_payload["agent_visible"]
    verifier = case_payload["verifier_only"]
    case_id = str(case_payload["case_id"])
    task_family = str(visible["task_family"])
    target = "\n".join(
        [
            f"Task: {visible['task_text']}",
            "",
            "Snippet:",
            visible["snippet"],
            "",
            f"Requested output schema: {', '.join(visible.get('requested_output_schema', []))}",
        ]
    ).strip()
    return ControlledTaskCase(
        case_id=case_id,
        aliases=(case_id, task_family),
        title=f"Mini-suite validation case {case_id}",
        task_family=task_family,
        expert_material="Agent-visible mini-suite case; verifier-only oracle not used for candidate generation.",
        target_asset=target,
        expected_capabilities=tuple(str(item) for item in verifier.get("expected_capabilities", [])),
        v1_capabilities=(),
        typical_feedback="mini_suite_validation_only",
        typical_repair="mini_suite_validation_only",
        verifier_contract={"required_fields": ["capability_id", "evidence_span", "recommended_fix"]},
        a1_defect="none",
        defect_capabilities=(),
        negative_control=bool(verifier.get("clean_or_negative")),
        metadata={"oracle_used_for_validation_only": True},
        source_dir=str(MINI_SUITE_CASES),
    )


def write_candidate_artifacts(candidate_dir: Path, *, base_text: str, candidate_text: str, candidate_package: SkillPackage, title: str, source_summary: dict[str, Any]) -> None:
    write_text(candidate_dir / "SKILL.md", candidate_text)
    write_json(candidate_dir / "manifest.json", candidate_package.to_dict())
    diff = "\n".join(
        difflib.unified_diff(
            base_text.splitlines(),
            candidate_text.splitlines(),
            fromfile="active_installed_SKILL.md",
            tofile=f"{candidate_package.version}_SKILL.md",
            lineterm="",
        )
    )
    diff_summary = [
        f"# Skill Diff: {title}",
        "",
        "## Evidence Binding",
        "",
        f"- Source type: `{source_summary.get('source_type')}`",
        f"- Source case: `{source_summary.get('case_id')}`",
        f"- Failure or limitation: `{source_summary.get('failure_or_limitation')}`",
        "",
        "## Scope Analysis",
        "",
        f"- Capability group changed: `{source_summary.get('capability_group_changed')}`",
        f"- Scope expansion risk: `{source_summary.get('scope_expansion_risk')}`",
        f"- Held-out or negative risk case: `{source_summary.get('risk_case_id')}`",
        "",
        "## Unified Diff",
        "",
        "```diff",
        diff,
        "```",
        "",
    ]
    write_text(candidate_dir / "skill_diff.md", "\n".join(diff_summary))
    write_json(candidate_dir / "candidate_generation_inputs.json", source_summary | {"verifier_only_oracle_fields_read": False})


def build_small_candidate_specs(out_dir: Path) -> list[dict[str, Any]]:
    active = load_active_secure_skill()
    base_package: SkillPackage = active["package"]
    base_text: str = active["skill_text"]
    cases = load_mini_suite_cases_by_id()
    limitations = load_json(MINI_SUITE_LIMITATIONS) if MINI_SUITE_LIMITATIONS.exists() else []
    mini_summary = load_json(MINI_SUITE_SUMMARY) if MINI_SUITE_SUMMARY.exists() else {}
    allowed_generation_sources = {
        "mini_suite_summary": str(MINI_SUITE_SUMMARY) if MINI_SUITE_SUMMARY.exists() else None,
        "limitation_summary": str(MINI_SUITE_LIMITATIONS) if MINI_SUITE_LIMITATIONS.exists() else None,
        "active_skill_dir": str(active["active_dir"]),
        "policy": "Candidate generation may read failure reports, verifier feedback, evidence summaries, and limitation summaries; it must not read verifier-only oracle expected findings or spans.",
    }

    candidate_specs: list[dict[str, Any]] = []

    config_package = clone_package_with_metadata(
        base_package,
        version="v3_config_realization_candidate",
        metadata_updates={
            "candidate_id": "config_security_001__v3_candidate_001",
            "candidate_type": "config_realization_constraint",
            "candidate_generation_sources": allowed_generation_sources,
        },
    )
    config_text = render_candidate_text(
        base_text,
        "config realization constraint",
        "Mini-suite and internal evidence require config findings to express environment-aware audit/export reasoning without broadening scope.",
        "No new task family is added; only config_security wording is constrained.",
    )
    candidate_specs.append(
        {
            "candidate_id": "config_security_001__v3_candidate_001",
            "candidate_dir": out_dir / "candidates" / "config_security_001__v3_candidate_001",
            "package": config_package,
            "text": config_text,
            "validation_case": controlled_task_case_from_directory(CONFIG_CASE_DIR),
            "source_summary": {
                "source_type": "verifier_feedback_and_evidence_summary",
                "case_id": "config_security_001",
                "failure_or_limitation": "configuration realization can regress to capability presence without explicit evidence realization",
                "capability_group_changed": "config_security",
                "scope_expansion_risk": "low",
                "risk_case_id": "mini_clean_out_of_scope_001",
            },
        }
    )

    def add_clean_to_upload(groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
        for group in groups:
            if group.get("name") == "upload_security":
                families = list(group.get("task_families", []))
                if "clean_business_logic_review" not in families:
                    families.append("clean_business_logic_review")
                group["task_families"] = families
        return groups

    fp_package = clone_package_with_metadata(
        base_package,
        version="v3_false_positive_stress_candidate",
        metadata_updates={
            "candidate_id": "clean_false_positive_guard__v3_candidate_002",
            "candidate_type": "false_positive_stress_scope_violation",
            "capability_groups": updated_groups(base_package, add_clean_to_upload),
            "candidate_generation_sources": allowed_generation_sources,
        },
    )
    fp_text = render_candidate_text(
        base_text,
        "false-positive stress scope expansion",
        "Stress test candidate intentionally maps a clean out-of-scope task to upload_security to verify rejection/quarantine logic.",
        "This is expected to be rejected if it introduces false positives or scope violation.",
    )
    if "mini_clean_out_of_scope_001" in cases:
        candidate_specs.append(
            {
                "candidate_id": "clean_false_positive_guard__v3_candidate_002",
                "candidate_dir": out_dir / "candidates" / "clean_false_positive_guard__v3_candidate_002",
                "package": fp_package,
                "text": fp_text,
                "validation_case": mini_case_to_controlled(cases["mini_clean_out_of_scope_001"]),
                "source_summary": {
                    "source_type": "negative_control_evidence_summary",
                    "case_id": "mini_clean_out_of_scope_001",
                    "failure_or_limitation": "false-positive control must remain zero on clean out-of-scope tasks",
                    "capability_group_changed": "upload_security",
                    "scope_expansion_risk": "high",
                    "risk_case_id": "mini_clean_out_of_scope_001",
                },
            }
        )

    def add_dependency_group(groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
        groups.append(
            {
                "name": "dependency_version_risk",
                "task_families": ["dependency_version_risk"],
                "capabilities": ["API_OVERBROAD_RISK"],
            }
        )
        return groups

    dependency_package = clone_package_with_metadata(
        base_package,
        version="v3_dependency_scope_expansion_candidate",
        metadata_updates={
            "candidate_id": "dependency_version_risk__v3_candidate_003",
            "candidate_type": "unsupported_dependency_scope_expansion",
            "capability_groups": updated_groups(base_package, add_dependency_group),
            "candidate_generation_sources": allowed_generation_sources,
            "unsupported_limitation_source_count": len(limitations),
        },
    )
    dependency_text = render_candidate_text(
        base_text,
        "unsupported dependency expansion",
        "Dependency/version-risk mini-suite evidence is intentionally a limitation; this candidate tests whether unsupported expansion is rejected.",
        "Adding dependency audit to secure_code_review core scope is not allowed in this sprint.",
    )
    if "mini_dependency_version_risk_001" in cases:
        candidate_specs.append(
            {
                "candidate_id": "dependency_version_risk__v3_candidate_003",
                "candidate_dir": out_dir / "candidates" / "dependency_version_risk__v3_candidate_003",
                "package": dependency_package,
                "text": dependency_text,
                "validation_case": mini_case_to_controlled(cases["mini_dependency_version_risk_001"]),
                "source_summary": {
                    "source_type": "limitation_summary",
                    "case_id": "mini_dependency_version_risk_001",
                    "failure_or_limitation": "dependency/version risk is unsupported and must remain outside secure_code_review core capability",
                    "capability_group_changed": "dependency_version_risk",
                    "scope_expansion_risk": "high",
                    "risk_case_id": "mini_dependency_version_risk_001",
                    "mini_suite_status": mini_summary.get("unsupported_limitation_status"),
                },
            }
        )

    return candidate_specs


def validate_small_candidate(candidate: dict[str, Any], active: dict[str, Any], output_root: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    baseline_spec = marginal.VariantSpec(
        name="active_installed",
        skill=active["package"],
        skill_text=active["skill_text"],
        skill_dir=active["active_dir"],
        runtime_source="active_installed_package",
        active_pointer_snapshot=active["pointer"],
    )
    candidate_spec = marginal.VariantSpec(
        name="candidate_package",
        skill=candidate["package"],
        skill_text=candidate["text"],
        skill_dir=candidate["candidate_dir"],
        runtime_source="candidate_package",
        active_pointer_snapshot=active["pointer"],
    )
    validation_slug = {
        "config_security_001__v3_candidate_001": "c001",
        "clean_false_positive_guard__v3_candidate_002": "c002",
        "dependency_version_risk__v3_candidate_003": "c003",
    }.get(candidate["candidate_id"], "candidate")
    validation = marginal.compare_two_variants(
        candidate["validation_case"],
        "offline_deterministic",
        baseline_spec,
        candidate_spec,
        output_root / "cand_val" / validation_slug,
    )
    scope_violation = validation["false_positive_delta"] > 0 or "dependency_scope_expansion" in candidate["package"].version
    promoted = (
        validation["score_delta"] > 0
        and validation["false_positive_delta"] <= 0
        and validation["schema_error_delta"] <= 0
        and not scope_violation
    )
    decision = {
        "candidate_id": candidate["candidate_id"],
        "decision": "promote" if promoted else "not_promoted",
        "reason": "strictly_better_than_active_installed" if promoted else "candidate_not_strictly_better_or_scope_safe",
        "score_delta": validation["score_delta"],
        "false_positive_delta": validation["false_positive_delta"],
        "schema_error_delta": validation["schema_error_delta"],
        "scope_violation": scope_violation,
        "promotion_rule": "candidate_score > active_score and no false-positive/schema/scope regression",
    }
    rejected = {
        "rejected_edit_id": f"rejected::{candidate['candidate_id']}",
        "case_id": candidate["validation_case"].case_id,
        "reason": decision["reason"],
        "score_delta": validation["score_delta"],
        "false_positive_delta": validation["false_positive_delta"],
        "scope_violation": scope_violation,
        "text_gradient": candidate["source_summary"]["failure_or_limitation"],
        "avoid_next": "do_not_promote_without_strict_gain_and_scope_safety",
        "oracle_fields_read_for_generation": False,
    }
    return validation, decision, rejected


def render_small_candidate_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Small Candidate Evolution Status",
        "",
        f"Run id: `{payload['run_id']}`",
        f"Candidate count: `{len(payload['candidate_outputs'])}`",
        "",
        "## Boundary",
        "",
        "This is a small candidate comparison, not a multi-round autonomous search. Candidate generation reads failure reports, verifier feedback, evidence summaries, and limitation summaries only; verifier-only oracle fields are not used for generation.",
        "",
        "| Candidate | Validation case | Decision | Score delta | FP delta | Scope violation |",
        "|---|---|---|---:|---:|---|",
    ]
    for item in payload["candidate_outputs"]:
        decision = item["promotion_decision_payload"]
        validation = item["validation_result_payload"]
        lines.append(
            f"| {item['candidate_id']} | {validation['case_id']} | {decision['decision']} | "
            f"{validation['score_delta']} | {validation['false_positive_delta']} | {decision['scope_violation']} |"
        )
    lines.extend(
        [
            "",
            "## Rejected Buffer",
            "",
            f"- Rejected edit count: `{len(payload['rejected_edit_buffer'])}`",
            f"- Reported buffer: `{payload['rejected_edit_buffer_path']}`",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a minimal evidence-gated Skill Evolution Lab.")
    parser.add_argument("--suite", default="secure_code_review")
    parser.add_argument("--budget", type=int, default=3)
    parser.add_argument("--gate", default="qgse_pareto")
    parser.add_argument("--elite-k", type=int, default=3)
    parser.add_argument("--output-dir", default=str(OUTPUT_ROOT))
    args = parser.parse_args(argv)

    if args.suite != "secure_code_review":
        raise SystemExit("only secure_code_review suite is supported in the P1 lab")
    marginal_payload = ensure_marginal_utility()
    cards_payload = build_skill_qualification_cards(ROOT)
    trajectory_store = build_trajectory_store(marginal_payload, cards_payload)
    contrasts = build_failure_contrast(cards_payload)
    candidates = build_candidate_pool(marginal_payload, args.budget)
    rejected = build_rejected_buffer(contrasts)
    elite = build_elite_pool(candidates, args.elite_k)
    retirement = build_retirement_decisions(cards_payload, marginal_payload, rejected)
    state_registry = build_skill_state_registry(retirement, elite)
    out_dir = Path(args.output_dir)

    candidate_outputs: list[dict[str, Any]] = []
    blocked_reason = None
    try:
        active_secure_skill = load_active_secure_skill()
        for candidate in build_small_candidate_specs(out_dir)[: max(1, min(args.budget, 3))]:
            write_candidate_artifacts(
                candidate["candidate_dir"],
                base_text=active_secure_skill["skill_text"],
                candidate_text=candidate["text"],
                candidate_package=candidate["package"],
                title=candidate["candidate_id"],
                source_summary=candidate["source_summary"],
            )
            validation, promotion_decision, rejected_candidate = validate_small_candidate(candidate, active_secure_skill, out_dir)
            write_json(candidate["candidate_dir"] / "validation_result.json", validation)
            write_json(candidate["candidate_dir"] / "promotion_decision.json", promotion_decision)
            if promotion_decision["decision"] != "promote":
                rejected.append(rejected_candidate)
            candidate_outputs.append(
                {
                    "candidate_id": candidate["candidate_id"],
                    "candidate_dir": str(candidate["candidate_dir"]),
                    "validation_result": str(candidate["candidate_dir"] / "validation_result.json"),
                    "promotion_decision": str(candidate["candidate_dir"] / "promotion_decision.json"),
                    "validation_result_payload": validation,
                    "promotion_decision_payload": promotion_decision,
                    "oracle_fields_read_for_generation": False,
                }
            )
    except Exception as exc:
        blocked_reason = f"small_candidate_generation_failed: {exc}"

    payload = {
        "run_id": "skill_evolution_lab_secure_code_review",
        "created_at": utc_now(),
        "suite": args.suite,
        "gate": args.gate,
        "single_trajectory_direct_edit_allowed": False,
        "trajectory_store": trajectory_store,
        "failure_contrast": contrasts,
        "candidate_pool": candidates,
        "candidate_outputs": candidate_outputs,
        "rejected_edit_buffer": rejected,
        "elite_pool": elite,
        "retirement_decisions": retirement,
        "skill_state_registry": state_registry,
        "blocked_reason": blocked_reason,
        "rejected_edit_buffer_path": str(out_dir / "rejected_edit_buffer.json"),
        "candidate_generation_policy": {
            "allowed_sources": ["failure report", "verifier feedback", "evidence summary", "limitation summary"],
            "forbidden_sources": ["verifier-only expected finding", "verifier-only expected evidence span", "verifier-only clean/negative answer label"],
            "oracle_fields_read_for_generation": False,
        },
        "claim_boundary": "minimal controlled Skill evolution lab; not broad autonomous self-improvement evidence",
    }
    write_json(out_dir / "trajectory_store.json", trajectory_store)
    write_json(out_dir / "failure_contrast.json", contrasts)
    write_text(out_dir / "text_gradient.md", render_text_gradient(contrasts, rejected))
    write_json(out_dir / "candidate_pool.json", candidates)
    write_json(out_dir / "rejected_edit_buffer.json", rejected)
    write_json(out_dir / "elite_pool.json", elite)
    write_json(out_dir / "retirement_decisions.json", retirement)
    write_json(out_dir / "skill_state_registry.json", state_registry)
    write_json(INSTALL_ROOT / "evolution_state_registry.json", state_registry)
    write_json(out_dir / "evolution_summary.json", payload)
    write_text(out_dir / "evolution_report.md", render_report(payload))
    write_text(SMALL_CANDIDATE_REPORT, render_small_candidate_report(payload))
    print(json.dumps({"output": str(out_dir / "evolution_summary.json"), "candidate_outputs": len(candidate_outputs), "blocked_reason": blocked_reason}, indent=2))
    return 0 if candidate_outputs else 1


if __name__ == "__main__":
    raise SystemExit(main())
