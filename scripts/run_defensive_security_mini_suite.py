from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from skill_deployment import (  # noqa: E402
    ControlledTaskCase,
    RunnerContext,
    SkillPackage,
    before_after_verifier,
    get_backend_runner,
    hash_file_sha256,
    hash_json_file_sha256,
    normalize_live_execution_report,
    resolve_installed_skill,
    resolve_task_conditioned_activation,
    score_from_verifier,
    verify_controlled_execution,
    write_evidence_bundle,
)
from skill_deployment.evidence import false_positive_count, skill_cost, write_json, write_text  # noqa: E402
from skill_deployment.install_state import load_active_pointer, read_skill_version, skill_version_dir  # noqa: E402


SUITE_PATH = ROOT / "data" / "external_security_mini_suite" / "cases.json"
OUTPUT_ROOT = ROOT / "outputs" / "external_security_mini_suite"
REPORT_PATH = ROOT / "reports" / "DEFENSIVE_SECURITY_MINI_SUITE_STATUS.md"


@dataclass(frozen=True)
class VariantSpec:
    name: str
    skill_package: SkillPackage | None
    skill_text: str
    skill_dir: Path | None
    runtime_source: str


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def case_target_text(case_payload: dict[str, Any]) -> str:
    visible = case_payload["agent_visible"]
    schema = ", ".join(visible.get("requested_output_schema", []))
    return "\n".join(
        [
            f"Task: {visible['task_text']}",
            "",
            "Snippet:",
            visible["snippet"],
            "",
            f"Requested output schema: {schema}",
        ]
    ).strip()


def make_agent_visible_case(case_payload: dict[str, Any]) -> ControlledTaskCase:
    visible = case_payload["agent_visible"]
    case_id = str(case_payload["case_id"])
    task_family = str(visible["task_family"])
    return ControlledTaskCase(
        case_id=case_id,
        aliases=(case_id, task_family),
        title=f"External defensive mini-suite case {case_id}",
        task_family=task_family,
        expert_material="Agent-visible defensive review task. Verifier-only oracle fields are intentionally omitted.",
        target_asset=case_target_text(case_payload),
        expected_capabilities=(),
        v1_capabilities=(),
        typical_feedback="not_exposed_to_runner",
        typical_repair="not_exposed_to_runner",
        verifier_contract={
            "checks": [
                "capability_coverage_score",
                "evidence_binding_score",
                "output_contract_score",
                "regression_safety_score",
                "trace_observability_score",
            ],
            "required_fields": ["capability_id", "evidence_span", "recommended_fix"],
            "oracle_visible_to_runner": False,
        },
        a1_defect="none",
        defect_capabilities=(),
        negative_control=bool(case_payload["verifier_only"].get("clean_or_negative")),
        metadata={
            "agent_visible_only": True,
            "oracle_fields_removed_from_runner_case": True,
            "forbidden_behavior": case_payload.get("forbidden_behavior"),
        },
        source_dir=str(SUITE_PATH),
    )


def version_integrity(installed_skill: str) -> dict[str, Any]:
    result: dict[str, Any] = {"installed_skill": installed_skill, "versions": {}, "version_content_identical": None}
    for version in ("v1", "v2"):
        version_dir = skill_version_dir(ROOT, installed_skill, version)
        if not version_dir.exists():
            result["versions"][version] = {"available": False, "reason": f"missing {version_dir}"}
            continue
        result["versions"][version] = {
            "available": True,
            "skill_dir": str(version_dir),
            "skill_hash": hash_file_sha256(version_dir / "SKILL.md"),
            "manifest_hash": hash_json_file_sha256(version_dir / "manifest.json"),
        }
    v1 = result["versions"].get("v1", {})
    v2 = result["versions"].get("v2", {})
    if v1.get("available") and v2.get("available"):
        result["version_content_identical"] = (
            v1.get("skill_hash") == v2.get("skill_hash")
            and v1.get("manifest_hash") == v2.get("manifest_hash")
        )
    return result


def build_variant_specs(installed_skill: str) -> tuple[list[VariantSpec], dict[str, Any], list[dict[str, Any]]]:
    unavailable: list[dict[str, Any]] = []
    specs = [VariantSpec("no_skill", None, "", None, "no_skill")]
    for version in ("v1", "v2"):
        version_dir = skill_version_dir(ROOT, installed_skill, version)
        if not version_dir.exists():
            unavailable.append({"variant": f"installed_{version}", "reason": f"missing installed version {version}"})
            continue
        package, skill_text, _manifest = read_skill_version(version_dir)
        specs.append(VariantSpec(f"installed_{version}", package, skill_text, version_dir, "installed_variant_package"))
    pointer = load_active_pointer(ROOT, installed_skill)
    active_version = str(pointer.get("active_version") or "")
    active_dir = skill_version_dir(ROOT, installed_skill, active_version) if active_version else None
    if active_dir and active_dir.exists():
        package, skill_text, _manifest = read_skill_version(active_dir)
        specs.append(VariantSpec("active_installed", package, skill_text, active_dir, "active_installed_package"))
    else:
        unavailable.append({"variant": "active_installed", "reason": "active pointer is missing or invalid"})
    return specs, dict(pointer), unavailable


def run_variant(
    *,
    case_payload: dict[str, Any],
    agent_case: ControlledTaskCase,
    verifier_only: dict[str, Any],
    spec: VariantSpec,
    backend: str,
    output_dir: Path,
    active_pointer_snapshot: dict[str, Any],
    runner_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    target_dir = output_dir / "target"
    write_text(target_dir / "target.md", agent_case.target_asset)
    runner = get_backend_runner(backend, project_root=ROOT)
    activation = (
        resolve_task_conditioned_activation(spec.skill_package, agent_case)
        if spec.skill_package is not None
        else {
            "task_family": agent_case.task_family,
            "activated_capability_group": "no_skill",
            "capabilities": (),
            "out_of_scope": False,
            "unsupported_task_family": None,
            "supported_task_families": [],
        }
    )
    metadata = {
        "runtime_source": spec.runtime_source,
        "skill_dir": spec.skill_dir,
        "task_family": agent_case.task_family,
        "activated_capability_group": activation["activated_capability_group"],
        "active_capabilities": list(activation["capabilities"]),
        "supported_task_families": activation["supported_task_families"],
        "out_of_scope": activation["out_of_scope"],
        "unsupported_task_family": activation["unsupported_task_family"],
        "oracle_fields_visible_to_runner": False,
    }
    metadata.update(runner_metadata or {})
    context = RunnerContext(
        scenario_id=agent_case.case_id,
        backend=backend,
        target_dir=target_dir,
        output_dir=output_dir / "agent",
        attempt_id=spec.name,
        skill_package=spec.skill_package,
        task_case=agent_case,
        metadata=metadata,
    )
    result = runner.run(context)
    raw_execution = result.report.to_dict()
    execution = raw_execution
    expected_group = str(verifier_only.get("expected_capability_group") or "")
    activated_group = str(activation["activated_capability_group"])
    normalization_trace: dict[str, Any] | None = None
    before_after: dict[str, Any] | None = None
    if bool(metadata.get("enable_evidence_normalizer")):
        normalization = normalize_live_execution_report(
            raw_execution,
            target_text=agent_case.target_asset,
            active_capabilities=list(activation["capabilities"]),
            activated_capability_group=activated_group,
            out_of_scope=bool(activation["out_of_scope"]),
        )
        execution = normalization.normalized_execution
        normalization_trace = normalization.trace
        before_after = before_after_verifier(
            expected_capabilities=tuple(str(item) for item in verifier_only.get("expected_capabilities", [])),
            raw_execution=normalization.raw_execution,
            normalized_execution=normalization.normalized_execution,
            target_text=agent_case.target_asset,
        )
        write_json(output_dir / "raw_execution_before_normalization.json", normalization.raw_execution)
        write_json(output_dir / "normalized_execution.json", normalization.normalized_execution)
        write_json(output_dir / "normalization_trace.json", normalization.trace)
        write_json(output_dir / "pre_normalization_verifier_report.json", before_after["before"])
        write_json(output_dir / "post_normalization_verifier_report.json", before_after["after"])
    verifier = verify_controlled_execution(
        tuple(str(item) for item in verifier_only.get("expected_capabilities", [])),
        execution,
        target_text=agent_case.target_asset,
    ).to_dict()
    capability_group_correct = activated_group == expected_group if spec.name != "no_skill" else activated_group == "no_skill"
    fp_count = false_positive_count(verifier)
    finding_detected = bool(execution.get("findings"))
    out_of_scope_correct = bool(activation["out_of_scope"]) if expected_group == "out_of_scope_guard" else not bool(activation["out_of_scope"])
    schema_valid = not verifier.get("schema_errors")
    evidence_grounded = not verifier.get("weak_evidence_capabilities") and not verifier.get("unsupported_evidence_capabilities")
    patch_or_recommendation_valid = schema_valid
    run_metadata = {
        "run_id": f"{case_payload['case_id']}::{backend}::{spec.name}",
        "case_id": case_payload["case_id"],
        "backend": backend,
        "variant": spec.name,
        "runtime_source": spec.runtime_source,
        "task_family": agent_case.task_family,
        "activated_capability_group": activated_group,
        "expected_capability_group": expected_group,
        "capability_group_correct": capability_group_correct,
        "out_of_scope": activation["out_of_scope"],
        "unsupported_task_family": activation["unsupported_task_family"],
        "skill_package_path": str(spec.skill_dir) if spec.skill_dir else "none",
        "skill_hash": hash_file_sha256(spec.skill_dir / "SKILL.md") if spec.skill_dir else "none",
        "manifest_hash": hash_json_file_sha256(spec.skill_dir / "manifest.json") if spec.skill_dir else "none",
        "active_pointer_snapshot": active_pointer_snapshot,
        "schema_version": "external_security_mini_suite.run_metadata.v1",
        "timestamp": utc_now(),
        "oracle_fields_visible_to_runner": False,
        "model": backend,
        "cost": None,
        "tokens": skill_cost(spec.skill_package, spec.skill_text) if spec.skill_package is not None else None,
    }
    if normalization_trace is not None:
        run_metadata.update(
            {
                "evidence_normalizer_enabled": True,
                "normalizer_version": normalization_trace.get("normalizer_version"),
                "evidence_exact_match_rate": normalization_trace.get("evidence_exact_match_rate"),
                "normalizer_taxonomy_counts": normalization_trace.get("failure_taxonomy_counts"),
            }
        )
    else:
        run_metadata["evidence_normalizer_enabled"] = False
    write_json(output_dir / "run_metadata.json", run_metadata)
    write_json(output_dir / "verifier_report.json", verifier)
    provenance = {
        **run_metadata,
        "safety_boundary": "defensive_review_only_no_exploit_generation",
    }
    bundle = write_evidence_bundle(
        output_dir / "evidence_bundle",
        case_id=str(case_payload["case_id"]),
        backend=backend,
        variant=spec.name,
        target_text=agent_case.target_asset,
        skill=spec.skill_package,
        skill_text=spec.skill_text,
        execution=execution,
        verifier=verifier,
        status="completed",
        provenance=provenance,
    )
    summary = {
        "variant": spec.name,
        "score": score_from_verifier(verifier),
        "pass": verifier["pass"],
        "feedback_type": verifier["feedback_type"],
        "activated_capability_group": activated_group,
        "expected_capability_group": expected_group,
        "capability_group_correct": capability_group_correct,
        "finding_detected": finding_detected,
        "evidence_grounded": evidence_grounded,
        "patch_or_recommendation_valid": patch_or_recommendation_valid,
        "schema_valid": schema_valid,
        "false_positive": fp_count > 0,
        "false_positive_count": fp_count,
        "out_of_scope_correct": out_of_scope_correct,
        "unsupported_limitation": bool(verifier_only.get("unsupported_limitation")),
        "clean_or_negative": bool(verifier_only.get("clean_or_negative")),
        "run_metadata": run_metadata,
        "normalization_trace": normalization_trace,
        "pre_normalization_verifier": before_after["before"] if before_after else None,
        "post_normalization_verifier": before_after["after"] if before_after else None,
        "pre_normalization_verifier_taxonomy": before_after["before_failure_taxonomy"] if before_after else None,
        "post_normalization_verifier_taxonomy": before_after["after_failure_taxonomy"] if before_after else None,
        "evidence_bundle_summary": str(output_dir / "evidence_bundle" / "summary.json"),
        "bundle": bundle,
    }
    write_json(output_dir / "variant_summary.json", summary)
    return summary


def case_status(case_payload: dict[str, Any], variants: dict[str, dict[str, Any]]) -> dict[str, Any]:
    verifier_only = case_payload["verifier_only"]
    active = variants.get("active_installed") or variants.get("installed_v2") or {}
    is_negative = bool(verifier_only.get("clean_or_negative"))
    unsupported = bool(verifier_only.get("unsupported_limitation"))
    false_positive_control_pass = is_negative and active.get("false_positive_count") == 0
    effective_pass = bool(active.get("pass")) and bool(active.get("capability_group_correct"))
    if unsupported:
        status = "unsupported_limitation"
    elif is_negative:
        status = "false_positive_control_pass" if false_positive_control_pass else "false_positive_control_fail"
    else:
        status = "pass" if effective_pass else "fail"
    return {
        "case_id": case_payload["case_id"],
        "task_family": case_payload["agent_visible"]["task_family"],
        "status": status,
        "active_variant": active.get("variant"),
        "active_score": active.get("score"),
        "active_pass": active.get("pass"),
        "activated_capability_group": active.get("activated_capability_group"),
        "expected_capability_group": active.get("expected_capability_group"),
        "capability_group_correct": active.get("capability_group_correct"),
        "false_positive_count": active.get("false_positive_count"),
        "false_positive_control_pass": false_positive_control_pass,
        "unsupported_limitation": unsupported,
        "out_of_scope_correct": active.get("out_of_scope_correct"),
        "artifact_dir": str(OUTPUT_ROOT / "cases" / str(case_payload["case_id"])),
    }


def compute_marginal(case_summaries: list[dict[str, Any]], variant_results: dict[str, dict[str, dict[str, Any]]], integrity: dict[str, Any]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for case in case_summaries:
        variants = variant_results[case["case_id"]]
        v1 = variants.get("installed_v1", {})
        v2 = variants.get("installed_v2", {})
        active = variants.get("active_installed", {})
        row = {
            "case_id": case["case_id"],
            "task_family": case["task_family"],
            "version_content_identical": integrity.get("version_content_identical"),
            "scores": {key: value.get("score") for key, value in variants.items()},
            "false_positive_counts": {key: value.get("false_positive_count") for key, value in variants.items()},
            "metrics": {},
        }
        if v1 and v2 and integrity.get("version_content_identical") is False:
            row["metrics"]["installed_v2_over_installed_v1_gain"] = round(float(v2["score"]) - float(v1["score"]), 4)
            row["metrics"]["installed_v2_false_positive_delta"] = int(v2["false_positive_count"]) - int(v1["false_positive_count"])
        else:
            row["metrics"]["installed_v2_over_installed_v1_gain"] = None
            row["metrics"]["version_gain_claim_allowed"] = False
        if active and v1 and integrity.get("version_content_identical") is False:
            row["metrics"]["active_over_installed_v1_gain"] = round(float(active["score"]) - float(v1["score"]), 4)
        rows.append(row)
    valid_gains = [
        row["metrics"]["installed_v2_over_installed_v1_gain"]
        for row in rows
        if row["metrics"].get("installed_v2_over_installed_v1_gain") is not None
    ]
    return {
        "generated_at": utc_now(),
        "version_integrity": integrity,
        "case_count": len(rows),
        "average_installed_v2_over_installed_v1_gain": round(sum(valid_gains) / len(valid_gains), 4) if valid_gains else None,
        "version_gain_claim_allowed": integrity.get("version_content_identical") is False,
        "rows": rows,
    }


def render_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Defensive Security Mini-Suite Status",
        "",
        f"Run id: `{payload['run_id']}`",
        f"Generated at: `{payload['generated_at']}`",
        "",
        "## Claim Boundary",
        "",
        "This is a local AutoPatchBench-style defensive approximation. It is not an official AutoPatchBench, CyberSecEval, or CVE-Bench run.",
        "It uses installed Skill packages and records fresh runtime evidence, but it does not prove real-world vulnerability scanning effectiveness.",
        "",
        "## Version Integrity",
        "",
        f"- `version_content_identical`: `{payload['version_integrity'].get('version_content_identical')}`",
    ]
    for version, info in payload["version_integrity"].get("versions", {}).items():
        lines.append(f"- `{version}`: skill_hash=`{info.get('skill_hash')}`, manifest_hash=`{info.get('manifest_hash')}`")
    lines.extend(
        [
            "",
            "## Case Results",
            "",
            "| Case | Task family | Status | Active group | Expected group | Group correct | FP count |",
            "|---|---|---|---|---|---:|---:|",
        ]
    )
    for row in payload["case_summaries"]:
        lines.append(
            f"| {row['case_id']} | {row['task_family']} | {row['status']} | "
            f"{row.get('activated_capability_group')} | {row.get('expected_capability_group')} | "
            f"{row.get('capability_group_correct')} | {row.get('false_positive_count')} |"
        )
    lines.extend(
        [
            "",
            "## Summary",
            "",
            f"- Fresh case count: `{payload['fresh_case_count']}`",
            f"- Positive security effective pass count: `{payload['positive_security_effective_pass_count']}`",
            f"- False-positive control status: `{payload['false_positive_control_status']}`",
            f"- Unsupported limitation status: `{payload['unsupported_limitation_status']}`",
            f"- Package-level marginal utility artifact: `{payload['package_marginal_utility_path']}`",
            "",
            "## Oracle Leakage Guard",
            "",
            "Runner inputs are built from agent-visible fields only. Verifier-only expected findings, evidence spans, capability groups, and clean labels are used only after execution.",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the local defensive security mini-suite through installed Skill packages.")
    parser.add_argument("--installed", default="secure_code_review")
    parser.add_argument("--backend", default="offline_deterministic")
    parser.add_argument("--suite", default=str(SUITE_PATH))
    parser.add_argument("--output-dir", default=str(OUTPUT_ROOT))
    args = parser.parse_args(argv)

    suite = read_json(Path(args.suite))
    output_root = Path(args.output_dir)
    integrity = version_integrity(args.installed)
    specs, active_pointer_snapshot, unavailable = build_variant_specs(args.installed)
    if len(specs) <= 1:
        raise SystemExit(f"no installed variants found for {args.installed}: {unavailable}")

    variant_results: dict[str, dict[str, dict[str, Any]]] = {}
    case_summaries: list[dict[str, Any]] = []
    sanitized_limitations: list[dict[str, Any]] = []
    for case_payload in suite["cases"]:
        agent_case = make_agent_visible_case(case_payload)
        verifier_only = case_payload["verifier_only"]
        case_dir = output_root / "cases" / str(case_payload["case_id"])
        variant_results[str(case_payload["case_id"])] = {}
        write_json(
            case_dir / "agent_visible_case.json",
            {
                "case_id": case_payload["case_id"],
                "agent_visible": case_payload["agent_visible"],
                "minimal_defensive_patch_or_recommendation": case_payload["minimal_defensive_patch_or_recommendation"],
                "forbidden_behavior": case_payload["forbidden_behavior"],
                "oracle_fields_visible_to_runner": False,
            },
        )
        write_json(
            case_dir / "verifier_only_oracle.redacted_summary.json",
            {
                "case_id": case_payload["case_id"],
                "expected_capability_count": len(verifier_only.get("expected_capabilities", [])),
                "expected_capability_group": verifier_only.get("expected_capability_group"),
                "clean_or_negative": bool(verifier_only.get("clean_or_negative")),
                "unsupported_limitation": bool(verifier_only.get("unsupported_limitation")),
                "note": "Full oracle fields are not written into runner inputs.",
            },
        )
        for spec in specs:
            variant_results[str(case_payload["case_id"])][spec.name] = run_variant(
                case_payload=case_payload,
                agent_case=agent_case,
                verifier_only=verifier_only,
                spec=spec,
                backend=args.backend,
                output_dir=case_dir / spec.name,
                active_pointer_snapshot=active_pointer_snapshot,
            )
        summary = case_status(case_payload, variant_results[str(case_payload["case_id"])])
        case_summaries.append(summary)
        if summary["unsupported_limitation"] or summary["status"] in {"fail", "false_positive_control_fail"}:
            sanitized_limitations.append(
                {
                    "case_id": summary["case_id"],
                    "task_family": summary["task_family"],
                    "status": summary["status"],
                    "activated_capability_group": summary["activated_capability_group"],
                    "capability_group_correct": summary["capability_group_correct"],
                    "false_positive_count": summary["false_positive_count"],
                    "source": summary["artifact_dir"],
                    "oracle_fields_included": False,
                }
            )

    marginal = compute_marginal(case_summaries, variant_results, integrity)
    package_marginal_path = output_root / "package_marginal_utility.json"
    write_json(package_marginal_path, marginal)
    write_json(output_root / "limitation_or_rejected_evidence.json", sanitized_limitations)

    positive = [row for row in case_summaries if not row["unsupported_limitation"] and row["status"] not in {"false_positive_control_pass", "false_positive_control_fail"}]
    positive_pass = [row for row in positive if row["status"] == "pass"]
    negative_rows = [row for row in case_summaries if row["status"].startswith("false_positive_control")]
    limitation_rows = [row for row in case_summaries if row["unsupported_limitation"]]
    false_positive_control_status = "pass" if negative_rows and all(row["false_positive_count"] == 0 for row in negative_rows) else "fail"
    unsupported_limitation_status = "retained" if limitation_rows else "missing"
    payload = {
        "run_id": "defensive_security_mini_suite_installed_runtime",
        "generated_at": utc_now(),
        "installed_skill": args.installed,
        "backend": args.backend,
        "suite_path": str(Path(args.suite)),
        "output_root": str(output_root),
        "version_integrity": integrity,
        "unavailable_variants": unavailable,
        "fresh_case_count": len(case_summaries),
        "positive_security_effective_pass_count": len(positive_pass),
        "false_positive_control_status": false_positive_control_status,
        "unsupported_limitation_status": unsupported_limitation_status,
        "case_summaries": case_summaries,
        "package_marginal_utility_path": str(package_marginal_path),
        "limitation_or_rejected_evidence_path": str(output_root / "limitation_or_rejected_evidence.json"),
        "claim_boundary": "bounded local defensive security evidence; not official AutoPatchBench/CyberSecEval",
    }
    write_json(output_root / "mini_suite_summary.json", payload)
    write_text(REPORT_PATH, render_report(payload))
    print(
        json.dumps(
            {
                "summary": str(output_root / "mini_suite_summary.json"),
                "report": str(REPORT_PATH),
                "fresh_case_count": len(case_summaries),
                "false_positive_control_status": false_positive_control_status,
                "unsupported_limitation_status": unsupported_limitation_status,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
