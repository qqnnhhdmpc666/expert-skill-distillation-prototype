from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from run_mvp_vertical_slice import estimate_tokens
from run_real_effect_eval import (
    CASES_DIR,
    FINDING_TEMPLATES,
    RULE_IDS,
    TRACE_RULES,
    build_review,
    evaluate_review,
    read_json,
    read_text,
    variant_config,
    write_json,
    write_text,
)


OUT_DIR = Path("outputs/mvp_vertical_slice/component_baseline_direct_summary_001")

DIRECT_SUMMARY_SKILL = """# Direct Summary API Review Skill

This is a direct first-pass summary of the expert materials. It is intentionally not a rule ledger, not evidence mapped, and not patch aware.

Review an API design for these common concerns:

- Authentication and authorization should be explicit.
- Request fields should document required status, types, constraints, and defaults.
- Error behavior should be clear enough for client handling and monitoring.
- Responses should avoid leaking tokens, secrets, internal traces, or unnecessary personal data.
- Response shape should be consistent and include useful request tracking metadata.

Return JSON findings with rule_id, issue, severity, and evidence when a concern applies.
"""

SUMMARY_RULE_CUES = {
    "R001": ("authentication", "authorization"),
    "R002": ("request fields", "types", "constraints", "defaults"),
    "R003": ("error behavior", "client handling", "monitoring"),
    "R004": ("tokens", "secrets", "internal traces", "personal data"),
    "R005": ("response shape", "request tracking", "metadata"),
    "R006": ("idempotency", "duplicate", "retry"),
}

VARIANTS = [
    "direct_summary_skill",
    "full_skill",
    "compact_v1",
    "patched_compact",
    "patched_compact_selective_trace",
]


def infer_direct_summary_rules(skill_text: str) -> list[str]:
    lowered = skill_text.lower()
    available: list[str] = []
    for rule_id in RULE_IDS:
        if any(cue.lower() in lowered for cue in SUMMARY_RULE_CUES[rule_id]):
            available.append(rule_id)
    return available


def get_variant_config(variant: str) -> dict[str, Any]:
    if variant != "direct_summary_skill":
        return variant_config(variant)
    return {
        "available_rule_ids": infer_direct_summary_rules(DIRECT_SUMMARY_SKILL),
        "skill_tokens": estimate_tokens(DIRECT_SUMMARY_SKILL),
        "protocol_tokens": 0,
        "source_path": str(OUT_DIR / "direct_summary_skill.md"),
        "raw_protocol_tokens": 0,
    }


def render_summary(payload: dict[str, Any]) -> str:
    lines = [
        "# Component Baseline Direct Summary 001",
        "",
        "## Purpose",
        "",
        "Compare a plain direct-summary skill against existing structured skill variants on the controlled API-review holdout.",
        "",
        "This is a component attribution slice, not a benchmark.",
        "",
        "| Variant | Avg Coverage | Pass@1 | Critical Misses | False Positives | Avg Total Tokens |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in payload["per_variant_results"]:
        lines.append(
            f"| {row['variant']} | {row['avg_checklist_coverage']:.2f} | "
            f"{row['pass_at_1_count']} / {row['case_count']} | {row['critical_missed_count']} | "
            f"{row['false_positive_count']} | {row['avg_total_tokens']:.1f} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            f"- Status: {payload['conclusion']['status']}",
            f"- Finding: {payload['conclusion']['finding']}",
            f"- Boundary: {payload['conclusion']['boundary']}",
            "",
        ]
    )
    return "\n".join(lines)


def render_component_attribution(payload: dict[str, Any]) -> str:
    by_variant = {row["variant"]: row for row in payload["per_variant_results"]}
    direct = by_variant["direct_summary_skill"]
    full = by_variant["full_skill"]
    compact = by_variant["compact_v1"]
    patched = by_variant["patched_compact"]
    selective = by_variant["patched_compact_selective_trace"]
    lines = [
        "# Component Attribution Notes",
        "",
        "## What This Baseline Tests",
        "",
        "`direct_summary_skill` checks whether a normal summary of expert materials is already enough for the controlled API-review family.",
        "",
        "## Observations",
        "",
        f"- Direct summary coverage: {direct['avg_checklist_coverage']:.2f}, pass@1: {direct['pass_at_1_count']} / {direct['case_count']}, avg tokens: {direct['avg_total_tokens']:.1f}.",
        f"- Full skill coverage: {full['avg_checklist_coverage']:.2f}, avg tokens: {full['avg_total_tokens']:.1f}.",
        f"- Compact v1 coverage: {compact['avg_checklist_coverage']:.2f}, avg tokens: {compact['avg_total_tokens']:.1f}.",
        f"- Patched compact coverage: {patched['avg_checklist_coverage']:.2f}, avg tokens: {patched['avg_total_tokens']:.1f}.",
        f"- Patched selective trace coverage: {selective['avg_checklist_coverage']:.2f}, avg tokens: {selective['avg_total_tokens']:.1f}.",
        "",
        "## Conservative Reading",
        "",
        "Plain summarization can cover several high-salience API-review concerns in this small family. The structured loop is therefore not valuable merely because it names obvious rules.",
        "",
        "The current added value is narrower and more defensible: verifier feedback identifies the missed long-tail/failure-critical rule, the patch loop restores it, and trace/gate machinery controls deployment risk.",
        "",
        "## Boundary",
        "",
        "This is a deterministic toy attribution slice. It does not prove direct summarization is generally strong or weak, and it does not prove the structured system is broadly superior.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    created_at = datetime.now(timezone.utc).isoformat()
    configs = {variant: get_variant_config(variant) for variant in VARIANTS}
    rows: list[dict[str, Any]] = []
    for case_dir in sorted(path for path in CASES_DIR.iterdir() if path.is_dir()):
        case_text = read_text(case_dir / "case.md")
        expected = read_json(case_dir / "expected.json")
        for variant in VARIANTS:
            config = configs[variant]
            traced_rule_ids = set(TRACE_RULES.get(variant, set())) & set(expected["expected_rule_ids"])
            review = build_review(case_text, expected["expected_rule_ids"], config["available_rule_ids"], traced_rule_ids)
            evaluation = evaluate_review(review, expected, traced_rule_ids)
            output_tokens = estimate_tokens(json.dumps(review, ensure_ascii=False))
            trace_tokens = estimate_tokens(json.dumps(review.get("rule_applications", []), ensure_ascii=False)) if traced_rule_ids else 0
            row = {
                "case_id": expected["case_id"],
                "variant": variant,
                "agent_type": "mock_case_aware",
                "expected_rule_ids": expected["expected_rule_ids"],
                "negative_rule_ids": expected["negative_rule_ids"],
                "available_rule_ids": config["available_rule_ids"],
                "traced_rule_ids": sorted(traced_rule_ids),
                "input_tokens": config["skill_tokens"],
                "protocol_tokens": config["protocol_tokens"],
                "output_tokens": output_tokens,
                "trace_tokens": trace_tokens,
                "total_tokens": config["skill_tokens"] + config["protocol_tokens"] + output_tokens,
                "retry_count": 0,
                "verifier_result": evaluation,
                **evaluation,
            }
            rows.append(row)
            case_out = OUT_DIR / expected["case_id"] / variant
            write_json(case_out / "review.json", review)
            write_json(case_out / "result.json", row)

    per_variant_results: list[dict[str, Any]] = []
    for variant in VARIANTS:
        subset = [row for row in rows if row["variant"] == variant]
        per_variant_results.append(
            {
                "variant": variant,
                "case_count": len(subset),
                "avg_checklist_coverage": round(sum(row["checklist_coverage"] for row in subset) / len(subset), 4),
                "pass_at_1_count": sum(1 for row in subset if row["pass_at_1"]),
                "critical_missed_count": sum(len(row["critical_missed_rules"]) for row in subset),
                "false_positive_count": sum(len(row["false_positive_rules"]) for row in subset),
                "failure_recurrence_count": sum(1 for row in subset if row["failure_recurrence"]),
                "avg_total_tokens": round(sum(row["total_tokens"] for row in subset) / len(subset), 2),
            }
        )

    by_variant = {row["variant"]: row for row in per_variant_results}
    direct = by_variant["direct_summary_skill"]
    patched = by_variant["patched_compact"]
    if patched["avg_checklist_coverage"] > direct["avg_checklist_coverage"]:
        status = "partially_supported"
        finding = "Structured patch loop improves over direct summarization in this controlled slice by recovering a missed long-tail/failure-critical rule."
    else:
        status = "inconclusive"
        finding = "Direct summarization is competitive in this controlled slice; more cases are needed before attributing gains to the structured loop."
    payload = {
        "run_id": OUT_DIR.name,
        "created_at": created_at,
        "case_count": len({row["case_id"] for row in rows}),
        "variants": VARIANTS,
        "direct_summary_available_rule_ids": configs["direct_summary_skill"]["available_rule_ids"],
        "per_case_results": rows,
        "per_variant_results": per_variant_results,
        "conclusion": {
            "status": status,
            "finding": finding,
            "boundary": "Controlled 4-case attribution slice only. This is not a benchmark and does not prove broad superiority over direct summarization.",
        },
    }
    write_text(OUT_DIR / "direct_summary_skill.md", DIRECT_SUMMARY_SKILL)
    write_json(OUT_DIR / "summary.json", payload)
    write_json(OUT_DIR / "per_case_results.json", rows)
    write_json(OUT_DIR / "per_variant_results.json", per_variant_results)
    write_text(OUT_DIR / "summary.md", render_summary(payload))
    write_text(OUT_DIR / "component_attribution.md", render_component_attribution(payload))
    write_json(
        OUT_DIR / "manifest.json",
        {
            "run_id": OUT_DIR.name,
            "created_at": created_at,
            "artifacts": [
                "direct_summary_skill.md",
                "summary.json",
                "summary.md",
                "per_case_results.json",
                "per_variant_results.json",
                "component_attribution.md",
            ],
            "boundary": payload["conclusion"]["boundary"],
        },
    )
    print(json.dumps({"output_dir": str(OUT_DIR), "status": status}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
