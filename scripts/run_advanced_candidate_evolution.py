from __future__ import annotations

import argparse
import difflib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from skill_deployment import SkillPackage, score_from_verifier  # noqa: E402
from skill_deployment.evidence import write_json, write_text  # noqa: E402
from skill_deployment.install_state import load_active_pointer, read_skill_version, skill_version_dir  # noqa: E402

import scripts.run_defensive_security_mini_suite as mini  # noqa: E402


OUTPUT_ROOT = ROOT / "outputs" / "skill_evolution_lab" / "secure_code_review" / "advanced_candidates"
REPORT = ROOT / "reports" / "ADVANCED_CANDIDATE_EVOLUTION_STATUS.md"
MECHANISM_REPORT = ROOT / "reports" / "QGSE_PARETO_MARGINAL_UTILITY_MECHANISM.md"
REJECTED_BUFFER = OUTPUT_ROOT / "rejected_edit_buffer.json"
PROMOTION_PROPOSAL = OUTPUT_ROOT / "promotion_proposal.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_active(installed: str) -> tuple[SkillPackage, str, Path, dict[str, Any]]:
    pointer = load_active_pointer(ROOT, installed)
    version = str(pointer.get("active_version") or "v2")
    active_dir = Path(str(pointer.get("skill_dir") or skill_version_dir(ROOT, installed, version))).resolve()
    package, text, _manifest = read_skill_version(active_dir)
    return package, text, active_dir, pointer


def clone_package(base: SkillPackage, *, version: str, metadata: dict[str, Any]) -> SkillPackage:
    return SkillPackage(
        skill_id=base.skill_id,
        version=version,
        task_family=base.task_family,
        capabilities=base.capabilities,
        output_contract=base.output_contract,
        trace_contract=base.trace_contract,
        metadata=metadata,
    )


def holdout_cases_by_id() -> dict[str, dict[str, Any]]:
    payload = read_json(ROOT / "data" / "external_security_mini_suite" / "holdout_cases.json", {})
    return {str(case["case_id"]): case for case in payload.get("cases", [])}


def mini_cases_by_id() -> dict[str, dict[str, Any]]:
    payload = read_json(ROOT / "data" / "external_security_mini_suite" / "cases.json", {})
    return {str(case["case_id"]): case for case in payload.get("cases", [])}


def package_metadata_with_note(base: SkillPackage, *, candidate_id: str, candidate_type: str, updates: dict[str, Any] | None = None) -> dict[str, Any]:
    metadata = json.loads(json.dumps(dict(base.metadata or {})))
    metadata["advanced_candidate_id"] = candidate_id
    metadata["candidate_type"] = candidate_type
    metadata["candidate_generation_sources"] = [
        "failure report",
        "verifier feedback summary",
        "evidence summary",
        "limitation summary",
    ]
    metadata["verifier_only_oracle_fields_read"] = False
    if updates:
        metadata.update(updates)
    return metadata


def add_dependency_group(metadata: dict[str, Any]) -> dict[str, Any]:
    groups = list(metadata.get("capability_groups", []))
    groups.append({"name": "dependency_version_risk", "task_families": ["dependency_version_risk"], "capabilities": ["API_OVERBROAD_RISK"]})
    metadata["capability_groups"] = groups
    return metadata


def add_clean_to_upload(metadata: dict[str, Any]) -> dict[str, Any]:
    groups = list(metadata.get("capability_groups", []))
    for group in groups:
        if group.get("name") == "upload_security":
            group["task_families"] = sorted(set(group.get("task_families", []) + ["clean_business_logic_review"]))
    metadata["capability_groups"] = groups
    return metadata


def candidate_specs(base: SkillPackage, base_text: str, budget: int) -> list[dict[str, Any]]:
    holdout = holdout_cases_by_id()
    mini_cases = mini_cases_by_id()
    ablation = read_json(ROOT / "outputs" / "ablation" / "task_conditioned_activation" / "activation_ablation_summary.json", {})
    non_oracle = read_json(ROOT / "outputs" / "non_oracle_validation" / "non_oracle_validation_summary.json", {})
    mini_summary = read_json(ROOT / "outputs" / "external_security_mini_suite" / "mini_suite_summary.json", {})
    specs: list[dict[str, Any]] = []

    specs.append(
        {
            "candidate_id": "advanced_config_holdout_realization_001",
            "case": holdout.get("holdout_config_prod_secret_001"),
            "source_type": "holdout_evidence_summary",
            "failure_or_limitation": "config realization must stay environment-aware on holdout cases",
            "capability_group_changed": "config_security",
            "scope_expansion_risk": "low",
            "risk_case_id": "holdout_clean_tax_math_001",
            "text_addition": "## Advanced Candidate Constraint: config holdout realization\n\n- Keep CONFIG_AUDIT_EXPORT and CONFIG_ENV_GUARD evidence grounded in prod/dev environment boundaries on holdout cases.\n",
            "metadata_updates": {},
        }
    )
    specs.append(
        {
            "candidate_id": "advanced_non_oracle_discrepancy_002",
            "case": holdout.get("holdout_api_overbroad_schema_001"),
            "source_type": "non_oracle_discrepancy_summary",
            "failure_or_limitation": f"non_oracle_completed_rows={non_oracle.get('non_oracle_completed_rows')}; preserve schema grounding under non-oracle backend",
            "capability_group_changed": "api_or_code_review",
            "scope_expansion_risk": "low",
            "risk_case_id": "holdout_clean_tax_math_001",
            "text_addition": "## Advanced Candidate Constraint: non-oracle schema grounding\n\n- Require API findings to keep structured evidence spans under non-oracle local semantic execution.\n",
            "metadata_updates": {},
        }
    )
    specs.append(
        {
            "candidate_id": "advanced_router_boundary_003",
            "case": holdout.get("holdout_clean_tax_math_001"),
            "source_type": "activation_ablation_failure",
            "failure_or_limitation": f"ablation mechanism_status={ablation.get('mechanism_status')}; guard out-of-scope routing against always-on capability variants",
            "capability_group_changed": "out_of_scope_guard",
            "scope_expansion_risk": "medium",
            "risk_case_id": "holdout_clean_tax_math_001",
            "text_addition": "## Advanced Candidate Constraint: task router boundary\n\n- Preserve out_of_scope_guard for clean business-logic tasks and avoid always-on security findings.\n",
            "metadata_updates": {},
        }
    )
    dep_meta = add_dependency_group(package_metadata_with_note(base, candidate_id="advanced_dependency_scope_expansion_004", candidate_type="unsupported_dependency_scope_expansion"))
    specs.append(
        {
            "candidate_id": "advanced_dependency_scope_expansion_004",
            "case": holdout.get("holdout_dependency_no_advisory_001") or mini_cases.get("mini_dependency_version_risk_001"),
            "source_type": "mini_suite_limitation_summary",
            "failure_or_limitation": f"unsupported limitation retained={mini_summary.get('unsupported_limitation_status')}; dependency audit remains out of core scope",
            "capability_group_changed": "dependency_version_risk",
            "scope_expansion_risk": "high",
            "risk_case_id": "holdout_dependency_no_advisory_001",
            "text_addition": "## Advanced Candidate Constraint: unsupported dependency expansion\n\n- This candidate intentionally tests adding dependency audit and should be rejected if it expands secure_code_review scope.\n",
            "metadata_override": dep_meta,
        }
    )
    fp_meta = add_clean_to_upload(package_metadata_with_note(base, candidate_id="advanced_false_positive_stress_005", candidate_type="negative_control_scope_stress"))
    specs.append(
        {
            "candidate_id": "advanced_false_positive_stress_005",
            "case": holdout.get("holdout_clean_tax_math_001"),
            "source_type": "ablation_negative_control_stress",
            "failure_or_limitation": "clean negative must not be routed into upload_security",
            "capability_group_changed": "upload_security",
            "scope_expansion_risk": "high",
            "risk_case_id": "holdout_clean_tax_math_001",
            "text_addition": "## Advanced Candidate Constraint: false-positive stress\n\n- This candidate intentionally maps clean tasks into upload scope and should be rejected by scope checks.\n",
            "metadata_override": fp_meta,
        }
    )
    return [spec for spec in specs if spec.get("case") is not None][: max(1, min(budget, 5))]


def write_candidate(base: SkillPackage, base_text: str, spec: dict[str, Any]) -> tuple[SkillPackage, str, Path]:
    candidate_id = str(spec["candidate_id"])
    candidate_dir = OUTPUT_ROOT / candidate_id
    metadata = spec.get("metadata_override") or package_metadata_with_note(
        base,
        candidate_id=candidate_id,
        candidate_type=str(spec["source_type"]),
        updates=spec.get("metadata_updates") or {},
    )
    package = clone_package(base, version=f"advanced_{candidate_id}", metadata=metadata)
    candidate_text = base_text.rstrip() + "\n\n" + str(spec["text_addition"]).strip() + "\n"
    write_text(candidate_dir / "SKILL.md", candidate_text)
    write_json(candidate_dir / "manifest.json", package.to_dict())
    diff = "\n".join(
        difflib.unified_diff(
            base_text.splitlines(),
            candidate_text.splitlines(),
            fromfile="active_installed_SKILL.md",
            tofile=f"{candidate_id}_SKILL.md",
            lineterm="",
        )
    )
    diff_doc = [
        f"# Skill Diff: {candidate_id}",
        "",
        "## Evidence Binding",
        "",
        f"- Solves failure / limitation: `{spec['failure_or_limitation']}`",
        f"- Modified capability group: `{spec['capability_group_changed']}`",
        f"- Changes out_of_scope_guard: `{'out_of_scope_guard' in str(spec['capability_group_changed'])}`",
        f"- Scope expansion risk: `{spec['scope_expansion_risk']}`",
        f"- Held-out/negative risk case: `{spec['risk_case_id']}`",
        "",
        "## Why Scope Should Not Expand",
        "",
        "Promotion is forbidden unless validation shows strict gain, no false-positive increase, no schema regression, and no scope violation.",
        "",
        "## Diff",
        "",
        "```diff",
        diff,
        "```",
        "",
    ]
    write_text(candidate_dir / "skill_diff.md", "\n".join(diff_doc))
    write_json(
        candidate_dir / "candidate_generation_inputs.json",
        {
            "candidate_id": candidate_id,
            "allowed_sources": ["failure report", "verifier feedback", "evidence summary", "limitation summary"],
            "forbidden_sources": ["verifier-only expected finding", "verifier-only expected evidence span", "verifier-only clean/negative label"],
            "source_type": spec["source_type"],
            "source_case_id": spec["case"]["case_id"],
            "failure_or_limitation": spec["failure_or_limitation"],
            "verifier_only_oracle_fields_read": False,
        },
    )
    write_json(
        candidate_dir / "risk_assessment.json",
        {
            "candidate_id": candidate_id,
            "scope_expansion_risk": spec["scope_expansion_risk"],
            "risk_case_id": spec["risk_case_id"],
            "may_affect_out_of_scope_guard": "out_of_scope_guard" in str(spec["capability_group_changed"]),
            "requires_negative_control": True,
        },
    )
    return package, candidate_text, candidate_dir


def scope_violation(summary: dict[str, Any], expected_group: str) -> bool:
    activated = str(summary.get("activated_capability_group") or "")
    if expected_group == "out_of_scope_guard":
        return activated != "out_of_scope_guard" or not summary.get("out_of_scope_correct")
    return activated != expected_group


def validate_candidate(
    *,
    spec: dict[str, Any],
    active_package: SkillPackage,
    active_text: str,
    active_dir: Path,
    pointer: dict[str, Any],
    candidate_package: SkillPackage,
    candidate_text: str,
    candidate_dir: Path,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any] | None]:
    case_payload = spec["case"]
    agent_case = mini.make_agent_visible_case(case_payload)
    expected_group = str(case_payload["verifier_only"].get("expected_capability_group") or "")
    active_spec = mini.VariantSpec("active_installed", active_package, active_text, active_dir, "active_installed_package")
    candidate_spec = mini.VariantSpec("candidate_package", candidate_package, candidate_text, candidate_dir, "advanced_candidate_package")
    active_summary = mini.run_variant(
        case_payload=case_payload,
        agent_case=agent_case,
        verifier_only=case_payload["verifier_only"],
        spec=active_spec,
        backend="offline_deterministic",
        output_dir=candidate_dir / "validation" / "active_installed",
        active_pointer_snapshot=pointer,
    )
    candidate_summary = mini.run_variant(
        case_payload=case_payload,
        agent_case=agent_case,
        verifier_only=case_payload["verifier_only"],
        spec=candidate_spec,
        backend="offline_deterministic",
        output_dir=candidate_dir / "validation" / "candidate_package",
        active_pointer_snapshot=pointer,
    )
    active_score = score_from_verifier(active_summary)
    candidate_score = score_from_verifier(candidate_summary)
    fp_delta = int(candidate_summary.get("false_positive_count") or 0) - int(active_summary.get("false_positive_count") or 0)
    schema_delta = len(candidate_summary.get("schema_errors", [])) - len(active_summary.get("schema_errors", []))
    scope_bad = scope_violation(candidate_summary, expected_group)
    validation = {
        "candidate_id": spec["candidate_id"],
        "case_id": case_payload["case_id"],
        "expected_capability_group": expected_group,
        "active_score": active_score,
        "candidate_score": candidate_score,
        "score_delta": round(candidate_score - active_score, 4),
        "false_positive_delta": fp_delta,
        "schema_error_delta": schema_delta,
        "scope_violation": scope_bad,
        "active_summary": active_summary,
        "candidate_summary": candidate_summary,
    }
    promoted = validation["score_delta"] > 0 and fp_delta <= 0 and schema_delta <= 0 and not scope_bad
    decision = {
        "candidate_id": spec["candidate_id"],
        "decision": "staged_promotion_proposal" if promoted else "not_promoted",
        "reason": "strictly_better_than_active_installed" if promoted else "not_strictly_better_or_scope_safe",
        "promotion_rule": "candidate_score > active_installed_score and false_positive_delta <= 0 and schema_error_delta <= 0 and scope_violation = false",
        "qgse_pareto_gate": "scoped_promote" if promoted else "reject",
        "auto_installed": False,
    }
    rejected = None
    if not promoted:
        rejected = {
            "rejected_edit_id": f"advanced::{spec['candidate_id']}",
            "candidate_id": spec["candidate_id"],
            "case_id": case_payload["case_id"],
            "rejected_reason": decision["reason"],
            "score_delta": validation["score_delta"],
            "false_positive_delta": fp_delta,
            "schema_error_delta": schema_delta,
            "scope_violation": scope_bad,
            "avoid_next": "do_not_repeat_without_strict_marginal_gain_and_scope_safety",
        }
    return validation, decision, rejected


def render_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Advanced Candidate Evolution Status",
        "",
        f"Generated at: `{payload['generated_at']}`",
        "",
        "Candidates are generated from failure reports, verifier feedback summaries, evidence summaries, and limitation summaries only. Verifier-only oracle fields are not read.",
        "",
        "| Candidate | Source | Case | Decision | Score delta | FP delta | Scope violation |",
        "|---|---|---|---|---:|---:|---:|",
    ]
    for item in payload["candidate_outputs"]:
        validation = item["validation_result"]
        decision = item["promotion_decision"]
        lines.append(
            f"| {item['candidate_id']} | {item['source_type']} | {validation['case_id']} | {decision['decision']} | "
            f"{validation['score_delta']} | {validation['false_positive_delta']} | {validation['scope_violation']} |"
        )
    lines.extend(["", "## Summary", "", f"- Rejected edits: `{len(payload['rejected_edit_buffer'])}`", f"- Promotion proposals: `{len(payload['promotion_proposals'])}`"])
    return "\n".join(lines) + "\n"


def render_mechanism_report() -> str:
    return """# QGSE-Pareto + Marginal Utility Mechanism

## Role of QGSE-Pareto

QGSE-Pareto is the promotion control layer. It is not the whole project and it is not a reward-only selector. It decides whether a candidate can be staged, quarantined, rejected, or retained for further evidence.

## Marginal Utility

Marginal utility is package-level evidence: the same case, target, verifier, and backend compare active installed packages or candidate packages. A candidate must improve over `active_installed`, not only over a weak baseline.

## Task-Conditioned Activation

Task-conditioned activation routes each task family to a bounded capability group and sends unsupported tasks to `out_of_scope_guard`. Its purpose is to reduce false positives and negative transfer.

## Rejected Buffer

The rejected edit buffer stores rejected candidate direction, score deltas, false-positive deltas, and scope violations. It prevents repeated bad updates rather than deleting inconvenient failures.

## Retirement / Quarantine

Retirement and quarantine are lifecycle controls. They mark stale, risky, no-benefit, or scope-expanding edits as non-promotable until new evidence changes the decision.

## Difference From Simple Pass/Fail

Simple pass/fail asks whether one run passed. This mechanism asks whether a package version has positive marginal value, preserves negative controls, keeps schema and scope constraints, and remains supported by evidence type labels.
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run advanced evidence-driven candidate evolution.")
    parser.add_argument("--installed", default="secure_code_review")
    parser.add_argument("--budget", type=int, default=5)
    args = parser.parse_args(argv)

    active_package, active_text, active_dir, pointer = load_active(args.installed)
    outputs: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    proposals: list[dict[str, Any]] = []
    for spec in candidate_specs(active_package, active_text, args.budget):
        package, candidate_text, candidate_dir = write_candidate(active_package, active_text, spec)
        validation, decision, rejected_item = validate_candidate(
            spec=spec,
            active_package=active_package,
            active_text=active_text,
            active_dir=active_dir,
            pointer=pointer,
            candidate_package=package,
            candidate_text=candidate_text,
            candidate_dir=candidate_dir,
        )
        write_json(candidate_dir / "validation_result.json", validation)
        write_json(candidate_dir / "promotion_decision.json", decision)
        if rejected_item:
            rejected.append(rejected_item)
        if decision["decision"] == "staged_promotion_proposal":
            proposals.append({"candidate_id": spec["candidate_id"], "candidate_dir": str(candidate_dir), "qgse_pareto_gate": decision["qgse_pareto_gate"]})
        outputs.append(
            {
                "candidate_id": spec["candidate_id"],
                "candidate_dir": str(candidate_dir),
                "source_type": spec["source_type"],
                "validation_result": validation,
                "promotion_decision": decision,
                "risk_assessment": str(candidate_dir / "risk_assessment.json"),
                "oracle_fields_read_for_generation": False,
            }
        )
    payload = {
        "run_id": "advanced_candidate_evolution_secure_code_review",
        "generated_at": utc_now(),
        "candidate_outputs": outputs,
        "rejected_edit_buffer": rejected,
        "promotion_proposals": proposals,
        "candidate_generation_policy": {
            "allowed_sources": ["failure report", "verifier feedback", "evidence summary", "limitation summary"],
            "forbidden_sources": ["verifier-only expected finding", "verifier-only expected evidence span", "verifier-only clean/negative label"],
            "oracle_fields_read_for_generation": False,
        },
        "claim_boundary": "advanced candidate search remains local controlled evidence; no auto-promotion to active pointer.",
    }
    write_json(OUTPUT_ROOT / "advanced_evolution_summary.json", payload)
    write_json(REJECTED_BUFFER, rejected)
    write_json(PROMOTION_PROPOSAL, {"generated_at": utc_now(), "proposals": proposals})
    write_text(REPORT, render_report(payload))
    write_text(MECHANISM_REPORT, render_mechanism_report())
    print(json.dumps({"summary": str(OUTPUT_ROOT / "advanced_evolution_summary.json"), "report": str(REPORT), "candidates": len(outputs), "promotions": len(proposals)}, indent=2))
    return 0 if outputs else 1


if __name__ == "__main__":
    raise SystemExit(main())
