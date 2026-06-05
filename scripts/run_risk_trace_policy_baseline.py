from __future__ import annotations

import json
import random
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from run_mvp_vertical_slice import estimate_tokens
from run_selective_trace_compiler import CASE_PATH, FINDINGS, PROTOCOLIZED_SKILL, RULE_IDS, TOKEN_BUDGET, split_protocol


OUT_DIR = Path("outputs/mvp_vertical_slice/risk_trace_policy_baseline_001")
RANDOM_SEED = 4
FAILURE_CRITICAL_RULES = {"R005", "R006"}
RISK_SIGNALS: dict[str, set[str]] = {
    "failure_critical": {"R005", "R006"},
    "previously_missed": {"R005", "R006"},
    "newly_patched": {"R005", "R006"},
    "high_priority": {"R001", "R002", "R003", "R004"},
    "output_contract_sensitive": {"R005"},
    "semantic_compressed": set(RULE_IDS),
}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def protocol_for(traced_rule_ids: list[str]) -> str:
    if not traced_rule_ids:
        return ""
    return (
        "For traced rules only, output rule_applications with rule_id, finding_id, "
        "trigger_condition_found, evidence_span, applicable=true, and confidence. "
        f"Traced rules: {', '.join(traced_rule_ids)}."
    )


def build_review(traced_rule_ids: list[str], shortcut: bool = False) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    applications: list[dict[str, Any]] = []
    for idx, rule_id in enumerate(RULE_IDS, start=1):
        finding_id = f"F{idx}"
        if shortcut:
            findings.append({"id": finding_id, "rule_id": rule_id, "issue": "rule id only", "severity": "medium", "evidence": "n/a"})
            continue
        item = FINDINGS[rule_id]
        findings.append(
            {
                "id": finding_id,
                "rule_id": rule_id,
                "issue": item["issue"],
                "severity": item["severity"],
                "evidence": item["evidence"],
            }
        )
        if rule_id in traced_rule_ids:
            applications.append(
                {
                    "rule_id": rule_id,
                    "applicable": True,
                    "trigger_condition_found": item["trigger"],
                    "evidence_span": item["span"],
                    "finding_id": finding_id,
                    "confidence": "medium",
                }
            )
    payload: dict[str, Any] = {"findings": findings}
    if traced_rule_ids:
        payload["rule_applications"] = applications
    return payload


def run_command(command: list[str]) -> None:
    subprocess.run(command, text=True, capture_output=True, check=False)


def run_base_verifiers(review_path: Path, run_dir: Path) -> dict[str, Any]:
    simple_path = run_dir / "simple_verification.json"
    semantic_path = run_dir / "semantic_verification.json"
    run_command([sys.executable, "scripts/verify_api_review_json.py", "--review", str(review_path), "--output", str(simple_path)])
    run_command([sys.executable, "scripts/verify_api_review_semantic_json.py", "--review", str(review_path), "--case", str(CASE_PATH), "--output", str(semantic_path)])
    simple = read_json(simple_path)
    semantic = read_json(semantic_path)
    return {
        "simple_verifier_result": simple,
        "semantic_verifier_result": semantic,
        "semantic_verifier_pass": bool(semantic["passed"]),
        "simple_verifier_pass": bool(simple["passed"]),
    }


def partial_trace_verify(review: dict[str, Any], traced_rule_ids: list[str]) -> dict[str, Any]:
    findings = review.get("findings", [])
    applications = review.get("rule_applications", [])
    seen_rule_ids = {str(item.get("rule_id")) for item in findings if isinstance(item, dict)}
    app_by_rule = {str(item.get("rule_id")): item for item in applications if isinstance(item, dict)}
    errors: list[str] = []
    for rule_id in traced_rule_ids:
        if rule_id not in seen_rule_ids:
            errors.append(f"traced rule {rule_id} has no finding")
            continue
        app = app_by_rule.get(rule_id)
        if not app:
            errors.append(f"traced rule {rule_id} missing rule_application")
            continue
        for field in ["finding_id", "trigger_condition_found", "evidence_span", "confidence"]:
            if not str(app.get(field, "")).strip():
                errors.append(f"traced rule {rule_id} missing {field}")
        if app.get("applicable") is not True:
            errors.append(f"traced rule {rule_id} must set applicable=true")
    return {
        "passed": not errors,
        "trace_required_rules_missing_trace": [rule_id for rule_id in traced_rule_ids if rule_id not in app_by_rule],
        "trace_errors": errors,
        "message": "partial trace verifier passed" if not errors else "; ".join(errors),
    }


def risk_score(rule_id: str) -> int:
    weights = {
        "failure_critical": 5,
        "previously_missed": 4,
        "newly_patched": 4,
        "output_contract_sensitive": 3,
        "high_priority": 2,
        "semantic_compressed": 1,
    }
    return sum(weight for signal, weight in weights.items() if rule_id in RISK_SIGNALS[signal])


def select_risk_based(k: int) -> list[str]:
    return sorted(RULE_IDS, key=lambda rule_id: (-risk_score(rule_id), rule_id))[:k]


def evaluate_variant(variant_id: str, traced_rule_ids: list[str], selection_method: str) -> dict[str, Any]:
    skill_text = read_text(PROTOCOLIZED_SKILL)
    rules_text, full_protocol_text = split_protocol(skill_text)
    protocol_text = full_protocol_text if variant_id == "B_full_trace" else protocol_for(traced_rule_ids)
    skill_tokens = estimate_tokens(rules_text)
    protocol_tokens = estimate_tokens(protocol_text) if protocol_text else 0
    review = build_review(traced_rule_ids)
    shortcut_review = build_review(traced_rule_ids, shortcut=True)
    output_trace_tokens = estimate_tokens(json.dumps(review.get("rule_applications", []), ensure_ascii=False)) if traced_rule_ids else 0
    total_tokens = skill_tokens + protocol_tokens
    over_budget = total_tokens > TOKEN_BUDGET
    run_dir = OUT_DIR / variant_id
    review_path = run_dir / "review.json"
    shortcut_path = run_dir / "shortcut_probe_review.json"
    write_json(review_path, review)
    write_json(shortcut_path, shortcut_review)
    base = run_base_verifiers(review_path, run_dir)
    partial_trace = partial_trace_verify(review, traced_rule_ids)
    shortcut_partial = partial_trace_verify(shortcut_review, traced_rule_ids)
    shortcut_blocked = bool(traced_rule_ids) and not shortcut_partial["passed"]
    failure_critical_trace_coverage = round(
        len(set(traced_rule_ids) & FAILURE_CRITICAL_RULES) / len(FAILURE_CRITICAL_RULES),
        4,
    )
    if over_budget:
        gate_decision = "reject_over_budget"
        accepted_by_gate = False
    elif not base["semantic_verifier_pass"]:
        gate_decision = "reject_semantic_failure"
        accepted_by_gate = False
    elif not partial_trace["passed"]:
        gate_decision = "reject_trace_failure"
        accepted_by_gate = False
    else:
        gate_decision = "accept"
        accepted_by_gate = True
    payload = {
        "variant_id": variant_id,
        "selection_method": selection_method,
        "traced_rule_ids": traced_rule_ids,
        "sampled_rule_ids": traced_rule_ids if selection_method == "random" else [],
        "random_seed": RANDOM_SEED if selection_method == "random" else None,
        "whether_hit_failure_critical_rule": bool(set(traced_rule_ids) & FAILURE_CRITICAL_RULES),
        "failure_critical_trace_coverage": failure_critical_trace_coverage,
        "risk_scores": {rule_id: risk_score(rule_id) for rule_id in traced_rule_ids},
        "skill_tokens": skill_tokens,
        "protocol_tokens": protocol_tokens,
        "output_trace_tokens": output_trace_tokens,
        "total_tokens": total_tokens,
        "token_budget": TOKEN_BUDGET,
        "over_budget": over_budget,
        **base,
        "partial_trace_verifier_result": partial_trace,
        "partial_trace_verifier_pass": bool(partial_trace["passed"]),
        "shortcut_probe_partial_trace_result": shortcut_partial,
        "shortcut_blocked": shortcut_blocked,
        "gate_decision": gate_decision,
        "accepted_by_gate": accepted_by_gate,
    }
    write_json(run_dir / "variant_summary.json", payload)
    return payload


def render_summary(payload: dict[str, Any]) -> str:
    lines = [
        "# Risk Trace Policy Baseline 001",
        "",
        "## Purpose",
        "",
        "Compare risk-based selective trace against no trace, full trace, and same-size random selective trace.",
        "",
        "| Variant | Selection | Traced Rules | Tokens | Failure-Critical Trace Coverage | Shortcut Blocked | Gate |",
        "|---|---|---|---:|---:|---|---|",
    ]
    for row in payload["variants"]:
        lines.append(
            f"| {row['variant_id']} | {row['selection_method']} | {', '.join(row['traced_rule_ids']) or 'none'} | "
            f"{row['total_tokens']} / {row['token_budget']} | {row['failure_critical_trace_coverage']:.2f} | "
            f"{row['shortcut_blocked']} | {row['gate_decision']} |"
        )
    lines.extend(
        [
            "",
            "## Randomness",
            "",
            f"- random_seed: {payload['random_seed']}",
            f"- random_sampled_rule_ids: {', '.join(payload['random_sampled_rule_ids'])}",
            f"- random_hit_failure_critical_rule: {payload['random_hit_failure_critical_rule']}",
            "",
            "## Conservative Conclusion",
            "",
            f"- Status: {payload['conclusion']['status']}",
            f"- Finding: {payload['conclusion']['finding']}",
            f"- Boundary: {payload['conclusion']['boundary']}",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    created_at = datetime.now(timezone.utc).isoformat()
    random_sample = sorted(random.Random(RANDOM_SEED).sample(RULE_IDS, 2))
    risk_based = select_risk_based(2)
    variants = [
        evaluate_variant("A_no_trace", [], "none"),
        evaluate_variant("B_full_trace", RULE_IDS, "full"),
        evaluate_variant("C_random_selective_trace", random_sample, "random"),
        evaluate_variant("D_risk_based_selective_trace", risk_based, "risk_based"),
    ]
    random_row = next(row for row in variants if row["variant_id"] == "C_random_selective_trace")
    risk_row = next(row for row in variants if row["variant_id"] == "D_risk_based_selective_trace")
    if (
        risk_row["failure_critical_trace_coverage"] > random_row["failure_critical_trace_coverage"]
        and risk_row["total_tokens"] <= random_row["total_tokens"] + 5
        and risk_row["accepted_by_gate"]
    ):
        status = "partially_supported"
        finding = "Risk signals help allocate trace budget to failure-critical rules in this toy slice."
    elif risk_row["failure_critical_trace_coverage"] == random_row["failure_critical_trace_coverage"]:
        status = "inconclusive"
        finding = "Current toy slice does not show risk-based selection is better than same-size random selective trace."
    else:
        status = "not_supported"
        finding = "Risk-based trace did not improve failure-critical trace coverage under this toy setup."
    payload = {
        "run_id": OUT_DIR.name,
        "created_at": created_at,
        "random_seed": RANDOM_SEED,
        "random_sampled_rule_ids": random_sample,
        "random_hit_failure_critical_rule": bool(set(random_sample) & FAILURE_CRITICAL_RULES),
        "risk_signals": {signal: sorted(rule_ids) for signal, rule_ids in RISK_SIGNALS.items()},
        "variants": variants,
        "conclusion": {
            "status": status,
            "finding": finding,
            "boundary": "Toy risk-trace policy baseline only. Random hit or miss can change results in this small rule pool; this is not statistical evidence.",
        },
    }
    write_json(OUT_DIR / "summary.json", payload)
    write_json(OUT_DIR / "variant_results.json", variants)
    write_text(OUT_DIR / "summary.md", render_summary(payload))
    write_json(
        OUT_DIR / "manifest.json",
        {
            "run_id": OUT_DIR.name,
            "created_at": created_at,
            "artifacts": ["summary.json", "summary.md", "variant_results.json", "*/variant_summary.json"],
            "boundary": payload["conclusion"]["boundary"],
        },
    )
    print(json.dumps({"output_dir": str(OUT_DIR), "status": status}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
