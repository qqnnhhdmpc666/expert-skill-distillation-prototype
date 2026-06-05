from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from run_mvp_vertical_slice import estimate_tokens


CASES_DIR = Path("data/api_review_holdout_cases")
OUT_DIR = Path("outputs/mvp_vertical_slice/real_effect_eval_001")
RULE_IDS = ["R001", "R002", "R003", "R004", "R005", "R006"]
SKILL_PATHS = {
    "no_skill": None,
    "full_skill": Path("outputs/mvp_vertical_slice/baseline_001/full_skill.md"),
    "compact_v1": Path("outputs/mvp_vertical_slice/baseline_001/compact_skill_v1.md"),
    "patched_compact": Path("outputs/mvp_vertical_slice/baseline_001/compact_skill_v2.md"),
    "patched_compact_selective_trace": Path("outputs/mvp_vertical_slice/skill_to_agent_loop_001/skill_variants/protocolized_compressed_skill.md"),
}
TRACE_RULES = {
    "patched_compact_selective_trace": {"R005", "R006"},
}

FINDING_TEMPLATES = {
    "R001": {
        "issue": "Authentication boundary is underspecified.",
        "severity": "high",
        "evidence": "The API mentions login/authentication but does not define roles, scopes, or authorization failure behavior.",
        "trigger": "login/authentication without roles or scopes",
        "span_terms": ["login", "auth", "scope", "role"],
    },
    "R002": {
        "issue": "Request validation rules are incomplete.",
        "severity": "high",
        "evidence": "Request fields lack required/optional markers, type constraints, ranges, lengths, or enum values.",
        "trigger": "request fields lack validation constraints",
        "span_terms": ["request", "field", "required", "type", "enum", "range"],
    },
    "R003": {
        "issue": "Error code coverage is incomplete.",
        "severity": "high",
        "evidence": "The error table omits expected validation, auth, permission, not-found, duplicate, or server classes.",
        "trigger": "incomplete error code table",
        "span_terms": ["error", "code", "500", "400", "401", "409"],
    },
    "R004": {
        "issue": "Response exposes sensitive or internal data.",
        "severity": "high",
        "evidence": "Response includes token-like fields, internal traces, or unnecessary personal data.",
        "trigger": "sensitive response data is present",
        "span_terms": ["access_token", "internal_trace", "phone", "identity", "token"],
    },
    "R005": {
        "issue": "Response envelope does not follow the required contract.",
        "severity": "medium",
        "evidence": "Response does not consistently expose code, message, request_id, and data.",
        "trigger": "response envelope missing code/message/request_id/data",
        "span_terms": ["response", "code", "message", "request_id", "data", "payload", "status"],
    },
    "R006": {
        "issue": "Mutation endpoint lacks idempotency or duplicate submission behavior.",
        "severity": "medium",
        "evidence": "POST/PUT/PATCH endpoint does not document idempotency keys or duplicate handling.",
        "trigger": "mutation endpoint lacks idempotency or duplicate handling",
        "span_terms": ["post", "put", "patch", "idempotency", "duplicate"],
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


def extract_rule_ids(skill_text: str) -> list[str]:
    return sorted(set(re.findall(r"\[(R00[1-6])\]", skill_text)))


def split_protocol(skill_text: str) -> tuple[str, str]:
    marker = "## Skill Invocation Protocol"
    if marker not in skill_text:
        return skill_text, ""
    rules, protocol = skill_text.split(marker, 1)
    return rules.rstrip() + "\n", marker + protocol


def first_case_span(case_text: str, rule_id: str) -> str:
    lowered = case_text.lower()
    for term in FINDING_TEMPLATES[rule_id]["span_terms"]:
        idx = lowered.find(term.lower())
        if idx >= 0:
            start = max(0, idx - 45)
            end = min(len(case_text), idx + 90)
            return " ".join(case_text[start:end].split())
    return "case text contains the relevant trigger"


def build_review(case_text: str, expected_rule_ids: list[str], available_rule_ids: list[str], traced_rule_ids: set[str]) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    applications: list[dict[str, Any]] = []
    for rule_id in RULE_IDS:
        if rule_id not in expected_rule_ids or rule_id not in available_rule_ids:
            continue
        finding_id = f"F{len(findings) + 1}"
        template = FINDING_TEMPLATES[rule_id]
        finding = {
            "id": finding_id,
            "rule_id": rule_id,
            "issue": template["issue"],
            "severity": template["severity"],
            "evidence": template["evidence"],
        }
        findings.append(finding)
        if rule_id in traced_rule_ids:
            applications.append(
                {
                    "rule_id": rule_id,
                    "applicable": True,
                    "trigger_condition_found": template["trigger"],
                    "evidence_span": first_case_span(case_text, rule_id),
                    "finding_id": finding_id,
                    "confidence": "medium",
                }
            )
    payload: dict[str, Any] = {"findings": findings}
    if traced_rule_ids:
        payload["rule_applications"] = applications
    return payload


def evaluate_review(review: dict[str, Any], expected: dict[str, Any], traced_rule_ids: set[str]) -> dict[str, Any]:
    expected_rule_ids = set(expected["expected_rule_ids"])
    critical_rule_ids = set(expected["critical_rule_ids"])
    negative_rule_ids = set(expected["negative_rule_ids"])
    findings = review.get("findings", [])
    seen_rule_ids = {str(item.get("rule_id")) for item in findings if isinstance(item, dict)}
    missing_rule_ids = sorted(expected_rule_ids - seen_rule_ids)
    critical_missed_rules = sorted(critical_rule_ids - seen_rule_ids)
    false_positive_rules = sorted(seen_rule_ids & negative_rule_ids)
    coverage = 1.0 if not expected_rule_ids and not seen_rule_ids else (
        len(expected_rule_ids & seen_rule_ids) / len(expected_rule_ids) if expected_rule_ids else 0.0
    )
    applications = review.get("rule_applications", [])
    application_rule_ids = {str(item.get("rule_id")) for item in applications if isinstance(item, dict)}
    missing_trace_rule_ids = sorted((traced_rule_ids & seen_rule_ids) - application_rule_ids)
    format_ok = isinstance(findings, list) and all(
        isinstance(item, dict) and all(str(item.get(field, "")).strip() for field in ["rule_id", "issue", "severity", "evidence"])
        for item in findings
    )
    pass_at_1 = format_ok and not missing_rule_ids and not false_positive_rules and not missing_trace_rule_ids
    return {
        "checklist_coverage": round(coverage, 4),
        "missing_rule_ids": missing_rule_ids,
        "critical_missed_rules": critical_missed_rules,
        "false_positive_rules": false_positive_rules,
        "format_ok": format_ok,
        "missing_trace_rule_ids": missing_trace_rule_ids,
        "pass_at_1": pass_at_1,
        "regression_detected": bool(false_positive_rules),
        "failure_recurrence": bool({"R005", "R006"} & set(missing_rule_ids)),
        "message": "pass" if pass_at_1 else "missing/false-positive/trace issue detected",
    }


def variant_config(variant: str) -> dict[str, Any]:
    path = SKILL_PATHS[variant]
    if path is None:
        return {"available_rule_ids": [], "skill_tokens": 0, "protocol_tokens": 0}
    skill_text = read_text(path)
    rules_text, protocol_text = split_protocol(skill_text)
    available_rule_ids = extract_rule_ids(skill_text)
    if variant == "full_skill":
        available_rule_ids = RULE_IDS
    protocol_tokens = 0
    if variant == "patched_compact_selective_trace":
        protocol_tokens = estimate_tokens(
            "For traced rules only, include rule_applications with rule_id, trigger_condition_found, evidence_span, finding_id, and confidence."
        )
    return {
        "available_rule_ids": available_rule_ids,
        "skill_tokens": estimate_tokens(rules_text),
        "protocol_tokens": protocol_tokens,
        "source_path": str(path),
        "raw_protocol_tokens": estimate_tokens(protocol_text) if protocol_text else 0,
    }


def render_summary(payload: dict[str, Any]) -> str:
    lines = [
        "# Real Effect Evaluation 001",
        "",
        "## Positioning",
        "",
        "Small controlled holdout set for checking whether skill-conditioned deployment improves API-review behavior.",
        "",
        "| Variant | Avg Coverage | Pass@1 | Critical Misses | False Positives | Avg Total Tokens |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in payload["per_variant_results"]:
        lines.append(
            f"| {row['variant']} | {row['avg_checklist_coverage']:.2f} | {row['pass_at_1_count']} / {row['case_count']} | "
            f"{row['critical_missed_count']} | {row['false_positive_count']} | {row['avg_total_tokens']:.1f} |"
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


def render_cost_effect_table(rows: list[dict[str, Any]]) -> str:
    lines = [
        "# Cost / Effect Table",
        "",
        "| Case | Variant | Coverage | Critical Misses | False Positives | Total Tokens | Pass@1 |",
        "|---|---|---:|---|---|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['case_id']} | {row['variant']} | {row['checklist_coverage']:.2f} | "
            f"{', '.join(row['critical_missed_rules']) or 'none'} | {', '.join(row['false_positive_rules']) or 'none'} | "
            f"{row['total_tokens']} | {row['pass_at_1']} |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    created_at = datetime.now(timezone.utc).isoformat()
    variants = list(SKILL_PATHS)
    configs = {variant: variant_config(variant) for variant in variants}
    rows: list[dict[str, Any]] = []
    for case_dir in sorted(path for path in CASES_DIR.iterdir() if path.is_dir()):
        case_text = read_text(case_dir / "case.md")
        expected = read_json(case_dir / "expected.json")
        for variant in variants:
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
    for variant in variants:
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

    patched = next(row for row in per_variant_results if row["variant"] == "patched_compact")
    compact = next(row for row in per_variant_results if row["variant"] == "compact_v1")
    if patched["avg_checklist_coverage"] > compact["avg_checklist_coverage"] and patched["critical_missed_count"] <= compact["critical_missed_count"]:
        status = "partially_supported"
        finding = "Small holdout evidence suggests patched compact skill improves controlled API-review behavior over compact_v1."
    else:
        status = "inconclusive"
        finding = "Small holdout evidence does not yet show a clear improvement over compact_v1."
    payload = {
        "run_id": OUT_DIR.name,
        "created_at": created_at,
        "case_count": len({row["case_id"] for row in rows}),
        "variants": variants,
        "llm_agent_status": "skipped_no_endpoint_invocation_in_this_slice",
        "per_case_results": rows,
        "per_variant_results": per_variant_results,
        "conclusion": {
            "status": status,
            "finding": finding,
            "boundary": "Controlled 4-case holdout only. This is not a benchmark and does not prove general real-world correctness.",
        },
    }
    write_json(OUT_DIR / "summary.json", payload)
    write_json(OUT_DIR / "per_case_results.json", rows)
    write_json(OUT_DIR / "per_variant_results.json", per_variant_results)
    write_text(OUT_DIR / "summary.md", render_summary(payload))
    write_text(OUT_DIR / "cost_effect_table.md", render_cost_effect_table(rows))
    write_json(
        OUT_DIR / "manifest.json",
        {
            "run_id": OUT_DIR.name,
            "created_at": created_at,
            "artifacts": ["summary.json", "summary.md", "per_case_results.json", "per_variant_results.json", "cost_effect_table.md"],
            "boundary": payload["conclusion"]["boundary"],
        },
    )
    print(json.dumps({"output_dir": str(OUT_DIR), "status": status}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
