from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


OUT_DIR = Path("outputs/mvp_vertical_slice/posterior_revision_signal_audit_001")
REAL_EFFECT = Path("outputs/mvp_vertical_slice/real_effect_eval_001/summary.json")
DIRECT_SUMMARY = Path("outputs/mvp_vertical_slice/component_baseline_direct_summary_001/summary.json")
COUNTERFACTUAL = Path("outputs/mvp_vertical_slice/counterfactual_patch_utility_001/summary.json")
ROLLBACK = Path("outputs/mvp_vertical_slice/rollback_gate_001/rollback_decision.json")
TRACE_ROBUSTNESS = Path("outputs/mvp_vertical_slice/risk_trace_policy_robustness_001/summary.json")
REVISION_MATRIX = Path("outputs/mvp_vertical_slice/revision_decision_matrix_001/summary.json")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def variant(rows: list[dict[str, Any]], name: str) -> dict[str, Any]:
    matches = [row for row in rows if row["variant"] == name]
    if not matches:
        raise ValueError(f"missing variant: {name}")
    return matches[0]


def counterfactual_record(records: list[dict[str, Any]], failure_case: str, patch_variant: str) -> dict[str, Any]:
    matches = [row for row in records if row["failure_case"] == failure_case and row["patch_variant"] == patch_variant]
    if not matches:
        raise ValueError(f"missing counterfactual record: {failure_case}/{patch_variant}")
    return matches[0]


def safe_delta(after: float, before: float) -> float:
    return round(after - before, 4)


def render_summary(payload: dict[str, Any]) -> str:
    lines = [
        "# Posterior Revision Signal Audit 001",
        "",
        "## Purpose",
        "",
        "This slice asks whether post-execution evidence is doing nontrivial method work beyond prior skill generation.",
        "It does not introduce a new task family or a new model. It audits existing artifacts through a method-level lens.",
        "",
        "## Candidate Method Statement",
        "",
        payload["candidate_method_statement"],
        "",
        "## Diagnostic Axes",
        "",
        "| Axis | Diagnostic Question | Current Evidence | Status |",
        "|---|---|---|---|",
    ]
    for axis in payload["diagnostic_axes"]:
        lines.append(
            f"| {axis['axis']} | {axis['question']} | {axis['evidence']} | {axis['status']} |"
        )
    lines.extend(
        [
            "",
            "## Key Quantitative Signals",
            "",
        ]
    )
    for key, value in payload["signals"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(
        [
            "",
            "## What This Supports",
            "",
            payload["conclusion"]["finding"],
            "",
            "## Boundary",
            "",
            payload["conclusion"]["boundary"],
            "",
            "## Falsification Pressure",
            "",
        ]
    )
    for item in payload["falsification_pressure"]:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    created_at = datetime.now(timezone.utc).isoformat()

    real_effect = read_json(REAL_EFFECT)
    direct_summary = read_json(DIRECT_SUMMARY)
    counterfactual = read_json(COUNTERFACTUAL)
    rollback = read_json(ROLLBACK)
    trace_robustness = read_json(TRACE_ROBUSTNESS)
    revision_matrix = read_json(REVISION_MATRIX)

    real_rows = real_effect["per_variant_results"]
    direct_rows = direct_summary["per_variant_results"]
    compact_v1 = variant(real_rows, "compact_v1")
    patched = variant(real_rows, "patched_compact")
    selective_trace = variant(real_rows, "patched_compact_selective_trace")
    direct = variant(direct_rows, "direct_summary_skill")
    full = variant(real_rows, "full_skill")

    records = counterfactual["records"]
    missing_no = counterfactual_record(records, "missing_rule", "no_patch")
    missing_random = counterfactual_record(records, "missing_rule", "random_patch_any")
    missing_wrong = counterfactual_record(records, "missing_rule", "wrong_type_patch")
    missing_compiler = counterfactual_record(records, "missing_rule", "compiler_patch")
    format_wrong = counterfactual_record(records, "output_format_error", "wrong_missing_rule_patch")
    format_contract = counterfactual_record(records, "output_format_error", "output_contract_patch")

    missing_specificity_margin = int(missing_compiler["failure_resolved"]) - max(
        int(missing_no["failure_resolved"]),
        int(missing_random["failure_resolved"]),
        int(missing_wrong["failure_resolved"]),
    )
    format_specificity_margin = int(format_contract["failure_resolved"]) - int(format_wrong["failure_resolved"])

    aggregate = trace_robustness["aggregate"]
    trace_uniqueness = {
        "full_coverage_combinations": aggregate["full_failure_critical_coverage_count"],
        "total_combinations": aggregate["total_combinations"],
        "coverage_rate": round(aggregate["full_failure_critical_coverage_count"] / aggregate["total_combinations"], 4),
    }

    rollback_decision = rollback.get("decision") or rollback.get("gate_decision") or rollback.get("action")
    if not rollback_decision:
        rollback_decision = json.dumps(rollback, ensure_ascii=False)[:120]

    signals = {
        "direct_summary_avg_coverage": direct["avg_checklist_coverage"],
        "compact_v1_avg_coverage": compact_v1["avg_checklist_coverage"],
        "patched_compact_avg_coverage": patched["avg_checklist_coverage"],
        "patched_selective_trace_avg_coverage": selective_trace["avg_checklist_coverage"],
        "full_skill_avg_tokens": full["avg_total_tokens"],
        "direct_summary_avg_tokens": direct["avg_total_tokens"],
        "patched_compact_avg_tokens": patched["avg_total_tokens"],
        "patched_selective_trace_avg_tokens": selective_trace["avg_total_tokens"],
        "posterior_recovery_gain_over_compact_v1": safe_delta(
            patched["avg_checklist_coverage"], compact_v1["avg_checklist_coverage"]
        ),
        "posterior_recovery_gain_over_direct_summary": safe_delta(
            patched["avg_checklist_coverage"], direct["avg_checklist_coverage"]
        ),
        "selective_trace_token_saving_vs_full_skill": round(
            1 - selective_trace["avg_total_tokens"] / full["avg_total_tokens"], 4
        ),
        "missing_rule_type_specificity_margin": missing_specificity_margin,
        "output_format_type_specificity_margin": format_specificity_margin,
        "risk_trace_unique_full_coverage_pair": trace_uniqueness,
        "rollback_gate_decision_observed": rollback_decision,
        "revision_matrix_rows": len(revision_matrix["matrix"]),
    }

    diagnostic_axes = [
        {
            "axis": "posterior recovery",
            "question": "Does execution feedback recover residual failures that prior skill generation missed?",
            "evidence": (
                f"compact_v1 coverage {compact_v1['avg_checklist_coverage']} -> patched_compact "
                f"{patched['avg_checklist_coverage']}; direct summary {direct['avg_checklist_coverage']} -> "
                f"patched {patched['avg_checklist_coverage']}."
            ),
            "status": "partially_supported",
        },
        {
            "axis": "attribution specificity",
            "question": "Does the failure type matter, or can any patch work?",
            "evidence": (
                f"missing_rule compiler_patch resolved={missing_compiler['failure_resolved']} while no/random/wrong-type "
                f"patches did not; output_format wrong_missing_rule resolved={format_wrong['failure_resolved']} vs "
                f"output_contract_patch resolved={format_contract['failure_resolved']}."
            ),
            "status": "partially_supported",
        },
        {
            "axis": "revision safety",
            "question": "Can a patch that fixes the observed failure still be unsafe?",
            "evidence": f"rollback gate decision: {rollback_decision}.",
            "status": "supported_in_toy_slice",
        },
        {
            "axis": "posterior trace allocation",
            "question": "Can failure-critical evidence guide trace budget better than arbitrary allocation?",
            "evidence": (
                f"only {trace_uniqueness['full_coverage_combinations']}/{trace_uniqueness['total_combinations']} "
                "size-2 trace allocations cover both failure-critical rules; risk policy selects that pair."
            ),
            "status": "partially_supported",
        },
    ]

    payload = {
        "run_id": OUT_DIR.name,
        "created_at": created_at,
        "positioning": "method exploration over existing toy artifacts; not a benchmark",
        "candidate_method_statement": (
            "Posterior skill revision treats a generated skill as a deployable hypothesis, not a final artifact. "
            "The method question is whether environment/verifier feedback can diagnose residual failure, choose a "
            "type-specific revision action, validate against regressions, and allocate trace evidence to high-risk "
            "rules under budget."
        ),
        "related_work_delta": {
            "spark_pdi_inspiration": (
                "SPARK-PDI argues that posterior execution evidence is more reliable than prior plans for skill "
                "distillation. This audit adapts the timing insight to skill deployment revision rather than claiming "
                "trajectory-level PDI."
            ),
            "colleague_skill_inspiration": (
                "COLLEAGUE.SKILL motivates versioned, correctable skill artifacts. This audit focuses on what signal "
                "should trigger a bounded revision after deployment feedback."
            ),
            "not_claimed": [
                "not a replacement for PDI",
                "not a general benchmark",
                "not proof that this policy transfers across domains",
            ],
        },
        "signals": signals,
        "diagnostic_axes": diagnostic_axes,
        "falsification_pressure": [
            "If larger holdouts show direct summary has no residual misses, posterior recovery is less central.",
            "If random or wrong-type patches resolve failures as often as targeted patches, attribution specificity is weak.",
            "If realistic patches rarely cause regressions, rollback becomes a safeguard rather than a method contribution.",
            "If risk-based trace does not outperform random allocation beyond this rule pool, trace allocation remains a toy result.",
        ],
        "conclusion": {
            "status": "partially_supported",
            "finding": (
                "Existing artifacts support a method-level hypothesis: post-execution evidence can function as a "
                "revision signal that changes what gets patched, gated, and traced, rather than merely increasing a "
                "token budget. The strongest current evidence is attribution-specific patch utility plus rollback and "
                "selective trace diagnostics."
            ),
            "boundary": (
                "Controlled API-review family only. This audit reuses toy-slice artifacts and does not establish a "
                "broad method like PDI. It identifies a promising method gap to test next: posterior revision utility "
                "across more task families and failure modes."
            ),
        },
    }

    write_json(OUT_DIR / "summary.json", payload)
    write_json(OUT_DIR / "diagnostic_axes.json", diagnostic_axes)
    write_text(OUT_DIR / "summary.md", render_summary(payload))
    write_json(
        OUT_DIR / "manifest.json",
        {
            "run_id": OUT_DIR.name,
            "created_at": created_at,
            "artifacts": ["summary.json", "summary.md", "diagnostic_axes.json", "manifest.json"],
            "source_artifacts": [
                str(REAL_EFFECT),
                str(DIRECT_SUMMARY),
                str(COUNTERFACTUAL),
                str(ROLLBACK),
                str(TRACE_ROBUSTNESS),
                str(REVISION_MATRIX),
            ],
            "boundary": payload["conclusion"]["boundary"],
        },
    )
    print(
        json.dumps(
            {
                "output_dir": str(OUT_DIR),
                "status": payload["conclusion"]["status"],
                "posterior_recovery_gain_over_compact_v1": signals["posterior_recovery_gain_over_compact_v1"],
                "missing_rule_type_specificity_margin": missing_specificity_margin,
                "output_format_type_specificity_margin": format_specificity_margin,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
