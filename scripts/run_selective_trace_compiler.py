from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from run_mvp_vertical_slice import estimate_tokens


OUT_DIR = Path("outputs/mvp_vertical_slice/selective_trace_compiler_001")
CASE_PATH = Path("data/harbor_api_review_tasks/api-review-001-compact-v1/case_001_openapi.md")
PROTOCOLIZED_SKILL = Path("outputs/mvp_vertical_slice/skill_to_agent_loop_001/skill_variants/protocolized_compressed_skill.md")
TOKEN_BUDGET = 237
RULE_IDS = ["R001", "R002", "R003", "R004", "R005", "R006"]
FINDINGS = {
    "R001": {
        "issue": "Authentication is underspecified.",
        "severity": "high",
        "evidence": "Notes say the endpoint requires login but do not define roles, scopes, or auth failure behavior.",
        "trigger": "login requirement without roles/scopes/auth failure behavior",
        "span": "The endpoint requires login.",
    },
    "R002": {
        "issue": "Request validation rules are incomplete.",
        "severity": "high",
        "evidence": "Request fields are listed without required/default status, type constraints, ranges, length, or enum rules.",
        "trigger": "request fields lack validation constraints",
        "span": "Request body lists fields but no required/type/range/enum constraints.",
    },
    "R003": {
        "issue": "Error code coverage is incomplete.",
        "severity": "high",
        "evidence": "Error table only includes success and server/system error.",
        "trigger": "error codes do not cover validation, auth, duplicate, and server classes",
        "span": "Error Codes table only defines 0 and 500.",
    },
    "R004": {
        "issue": "Response exposes sensitive or internal information.",
        "severity": "high",
        "evidence": "Response includes access_token, internal_trace, phone, or personal data.",
        "trigger": "sensitive response data is present",
        "span": "Response data contains token/trace/phone-like fields.",
    },
    "R005": {
        "issue": "Response envelope lacks request_id.",
        "severity": "medium",
        "evidence": "Response contains code, message, and data but no request_id.",
        "trigger": "response envelope missing request_id",
        "span": "Response JSON has code, message, data.",
    },
    "R006": {
        "issue": "Mutation endpoint does not document idempotency or duplicate submission behavior.",
        "severity": "medium",
        "evidence": "POST endpoint notes do not describe idempotency or duplicate handling.",
        "trigger": "mutation endpoint lacks idempotency/duplicate handling",
        "span": "Endpoint uses POST.",
    },
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


def split_protocol(skill_text: str) -> tuple[str, str]:
    marker = "## Skill Invocation Protocol"
    rules, protocol = skill_text.split(marker, 1)
    return rules.rstrip() + "\n", marker + protocol


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
        "simple_verifier_pass": bool(simple["passed"]),
        "semantic_verifier_pass": bool(semantic["passed"]),
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
    semantic_only_rules = [rule_id for rule_id in RULE_IDS if rule_id not in traced_rule_ids]
    passed = not errors
    return {
        "passed": passed,
        "failure_type": "none" if passed else "partial_trace_error",
        "traced_rule_ids": traced_rule_ids,
        "semantic_only_rule_ids": semantic_only_rules,
        "trace_required_rules_missing_trace": [rule_id for rule_id in traced_rule_ids if rule_id not in app_by_rule],
        "trace_errors": errors,
        "message": "partial trace verifier passed" if passed else "; ".join(errors),
    }


def evaluate_variant(variant_id: str, traced_rule_ids: list[str], gate_enabled: bool) -> dict[str, Any]:
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
    semantic_only_rules_weak = [] if base["semantic_verifier_pass"] else [rule_id for rule_id in RULE_IDS if rule_id not in traced_rule_ids]
    accepted = bool(base["simple_verifier_pass"] and base["semantic_verifier_pass"] and partial_trace["passed"] and not over_budget)
    if not gate_enabled:
        decision = "not_gated"
        accepted_by_gate = None
        explanation = "Validation gate disabled for comparison."
    elif over_budget:
        decision = "reject_over_budget"
        accepted_by_gate = False
        explanation = "Skill plus protocol exceeds fixed token budget."
    elif not partial_trace["passed"]:
        decision = "reject_trace_required_rules_missing_trace"
        accepted_by_gate = False
        explanation = "At least one traced rule lacks a valid rule_application."
    elif not base["semantic_verifier_pass"]:
        decision = "reject_semantic_only_rules_weak"
        accepted_by_gate = False
        explanation = "Semantic verifier failed for one or more findings."
    elif accepted:
        decision = "accept"
        accepted_by_gate = True
        explanation = "Required coverage, semantic checks, partial trace checks, and budget constraints pass."
    else:
        decision = "reject_inconclusive"
        accepted_by_gate = False
        explanation = "Variant did not satisfy all gate constraints."
    payload = {
        "variant_id": variant_id,
        "traced_rule_ids": traced_rule_ids,
        "untraced_rule_ids": [rule_id for rule_id in RULE_IDS if rule_id not in traced_rule_ids],
        "skill_tokens": skill_tokens,
        "protocol_tokens": protocol_tokens,
        "output_trace_tokens": output_trace_tokens,
        "total_tokens": total_tokens,
        "token_budget": TOKEN_BUDGET,
        "over_budget": over_budget,
        **base,
        "partial_trace_verifier_result": partial_trace,
        "partial_trace_verifier_pass": partial_trace["passed"],
        "shortcut_probe_partial_trace_result": shortcut_partial,
        "shortcut_blocked": shortcut_blocked,
        "trace_required_rules_missing_trace": partial_trace["trace_required_rules_missing_trace"],
        "semantic_only_rules_weak": semantic_only_rules_weak,
        "validation_gate_decision": decision,
        "accepted_by_gate": accepted_by_gate,
        "explanation": explanation,
    }
    write_json(run_dir / "variant_summary.json", payload)
    return payload


def render_summary(payload: dict[str, Any]) -> str:
    lines = [
        "# Selective Trace Compiler 001",
        "",
        "## Positioning",
        "",
        "Toy slice for deciding where traceability cost should be spent under a fixed budget.",
        "",
        "| Variant | Traced Rules | Tokens | Trace Pass | Shortcut Blocked | Gate |",
        "|---|---|---:|---|---|---|",
    ]
    for row in payload["variants"]:
        lines.append(
            f"| {row['variant_id']} | {', '.join(row['traced_rule_ids']) or 'none'} | "
            f"{row['total_tokens']} / {row['token_budget']} | {row['partial_trace_verifier_pass']} | "
            f"{row['shortcut_blocked']} | {row['validation_gate_decision']} |"
        )
    lines.extend(
        [
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
    variants = [
        evaluate_variant("A_no_trace", [], gate_enabled=True),
        evaluate_variant("B_full_trace", RULE_IDS, gate_enabled=True),
        evaluate_variant("C_selective_trace_failure_critical", ["R005", "R006"], gate_enabled=True),
        evaluate_variant("D_selective_trace_high_risk_or_patched", ["R001", "R003", "R005", "R006"], gate_enabled=True),
    ]
    full = next(row for row in variants if row["variant_id"] == "B_full_trace")
    selective = next(row for row in variants if row["variant_id"] == "C_selective_trace_failure_critical")
    no_trace = next(row for row in variants if row["variant_id"] == "A_no_trace")
    if selective["accepted_by_gate"] and selective["total_tokens"] < full["total_tokens"] and selective["shortcut_blocked"] and not no_trace["shortcut_blocked"]:
        status = "partially_supported"
        finding = "Selective trace reduces protocol overhead while preserving traceability for failure-critical rules in this toy slice."
    elif selective["over_budget"]:
        status = "inconclusive_under_current_protocol_cost"
        finding = "Selective trace still exceeds the current budget and needs protocol compression or amortization."
    elif not selective["shortcut_blocked"]:
        status = "not_supported"
        finding = "Current selective trace policy does not block shortcut behavior."
    else:
        status = "inconclusive"
        finding = "Selective trace shows mixed evidence under current toy constraints."
    payload = {
        "run_id": OUT_DIR.name,
        "created_at": created_at,
        "token_budget": TOKEN_BUDGET,
        "variants": variants,
        "conclusion": {
            "status": status,
            "finding": finding,
            "boundary": "Toy selective-trace slice only. It does not prove a mature protocol or general correctness.",
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
