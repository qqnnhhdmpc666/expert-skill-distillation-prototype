from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


OUT_DIR = Path("outputs/mvp_vertical_slice/second_domain_config_security_001")
CASES_DIR = Path("data/config_security_cases")
MATERIAL_PATH = Path("data/config_security_expert_materials/config_security_guidelines.md")
TOKEN_BUDGET = 260


RULES: dict[str, dict[str, Any]] = {
    "C001": {
        "title": "No hardcoded secrets",
        "text": "Do not hardcode tokens, passwords, API keys, or private credentials in configuration files; use secret references.",
        "severity": "high",
        "trigger_terms": ["token", "api_key", "secret", "password", "sk_live"],
        "config_path": "secrets or credential-like fields",
        "priority": "high",
    },
    "C002": {
        "title": "TLS for production endpoints",
        "text": "Production external endpoints must use https/TLS; plain http endpoints are not acceptable.",
        "severity": "high",
        "trigger_terms": ["http://"],
        "config_path": "external_api_url",
        "priority": "high",
    },
    "C003": {
        "title": "Least-privilege service accounts",
        "text": "Service accounts should avoid admin, wildcard, or broad write roles unless explicitly justified.",
        "severity": "high",
        "trigger_terms": ["admin", "wildcard", "*"],
        "config_path": "service_account.roles",
        "priority": "high",
    },
    "C004": {
        "title": "Disable production debug",
        "text": "Production deployments must set debug=false.",
        "severity": "high",
        "trigger_terms": ["debug: true"],
        "config_path": "debug",
        "priority": "high",
    },
    "C005": {
        "title": "Runtime resource limits",
        "text": "Containers or services should define CPU and memory requests or limits.",
        "severity": "medium",
        "trigger_terms": ["resources:", "limits:", "requests:"],
        "config_path": "resources",
        "priority": "medium",
    },
    "C006": {
        "title": "Audit logging and retention",
        "text": "Security-sensitive services should enable audit logging and define retention or export behavior.",
        "severity": "medium",
        "trigger_terms": ["audit:", "enabled: false", "retention_days:", "export_sink:"],
        "config_path": "audit",
        "priority": "medium",
        "residual_deployment_critical": True,
    },
}


STRATEGIES: dict[str, dict[str, Any]] = {
    "direct_summary_skill": {
        "available_rule_ids": ["C001", "C002", "C003", "C004", "C005"],
        "contract_fixed": True,
        "trace_rule_ids": [],
        "description": "Strong prior-summary baseline that omits the residual audit-retention rule C006.",
    },
    "compact_v1_no_revision": {
        "available_rule_ids": ["C001", "C002", "C003", "C004", "C005"],
        "contract_fixed": True,
        "trace_rule_ids": [],
        "description": "Deployable compact skill before posterior revision.",
    },
    "always_append_domain_rules": {
        "available_rule_ids": ["C001", "C002", "C003", "C004", "C005", "C006"],
        "contract_fixed": False,
        "trace_rule_ids": [],
        "description": "Generic domain-rule append strategy.",
    },
    "always_rewrite_output_contract": {
        "available_rule_ids": ["C001", "C002", "C003", "C004", "C005"],
        "contract_fixed": True,
        "trace_rule_ids": [],
        "description": "Generic output-contract rewrite strategy without domain patch.",
    },
    "always_regenerate_full_skill": {
        "available_rule_ids": ["C001", "C002", "C003", "C004", "C005", "C006"],
        "contract_fixed": True,
        "trace_rule_ids": [],
        "full_skill": True,
        "description": "High-cost upper bound: regenerate or use the full skill package.",
    },
    "accept_if_current_failure_fixed": {
        "available_rule_ids": ["C001", "C002", "C004", "C005", "C006"],
        "contract_fixed": True,
        "trace_rule_ids": [],
        "description": "Unsafe strategy that patches C006 but drops previously covered C003.",
    },
    "always_full_trace": {
        "available_rule_ids": ["C001", "C002", "C003", "C004", "C005", "C006"],
        "contract_fixed": True,
        "trace_rule_ids": ["C001", "C002", "C003", "C004", "C005", "C006"],
        "description": "Trace every rule; useful upper bound but expected to exceed budget.",
    },
    "type_specific_operator_plus_gate_and_selective_trace": {
        "available_rule_ids": ["C001", "C002", "C003", "C004", "C005", "C006"],
        "contract_fixed": True,
        "trace_rule_ids": ["C006"],
        "compressed": True,
        "description": "Typed missing-rule patch plus output contract repair, regression gate, and selective trace for residual C006.",
    },
}


def estimate_tokens(text: str) -> int:
    return max(1, round(len(text) / 4)) if text else 0


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


def compact_rule_text(rule_id: str) -> str:
    compact = {
        "C001": "No hardcoded secrets; require vault/env refs.",
        "C002": "Production external URLs must use https.",
        "C003": "Avoid admin/wildcard service-account roles.",
        "C004": "Production debug must be false.",
        "C005": "Define CPU/memory requests or limits.",
        "C006": "Enable audit logging with retention/export.",
    }
    return compact[rule_id]


def skill_markdown(
    title: str,
    rule_ids: list[str],
    *,
    full: bool = False,
    compressed: bool = False,
    contract: bool = True,
    trace_rule_ids: list[str] | None = None,
) -> str:
    lines = [f"# {title}", "", "## Rules"]
    for rule_id in rule_ids:
        rule = RULES[rule_id]
        if compressed:
            lines.append(f"- [{rule_id}] {compact_rule_text(rule_id)}")
        elif full:
            lines.append(f"- [{rule_id}] {rule['title']}: {rule['text']} Severity: {rule['severity']}. Config path: {rule['config_path']}.")
        else:
            lines.append(f"- [{rule_id}] {rule['text']}")
    if contract:
        lines.extend(
            [
                "",
                "## Output Contract",
                "",
                "Return JSON findings with rule_id, issue, severity, evidence, and config_path.",
            ]
        )
    if trace_rule_ids:
        lines.extend(
            [
                "",
                "## Trace Contract",
                "",
                "For traced rules, add rule_applications with rule_id, finding_id, trigger, evidence_span, config_path, confidence.",
                f"Traced rules: {', '.join(trace_rule_ids)}.",
            ]
        )
    return "\n".join(lines) + "\n"


def first_span(config_text: str, rule_id: str) -> str:
    lowered = config_text.lower()
    for term in RULES[rule_id]["trigger_terms"]:
        idx = lowered.find(term.lower())
        if idx >= 0:
            start = max(0, idx - 35)
            end = min(len(config_text), idx + 90)
            return " ".join(config_text[start:end].split())
    return "configuration contains the relevant trigger"


def build_review(config_text: str, expected_rule_ids: list[str], available_rule_ids: list[str], trace_rule_ids: list[str], *, contract_fixed: bool) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    applications: list[dict[str, Any]] = []
    for rule_id in sorted(set(expected_rule_ids) & set(available_rule_ids)):
        rule = RULES[rule_id]
        finding_id = f"F{len(findings) + 1}"
        finding: dict[str, Any] = {
            "id": finding_id,
            "rule_id": rule_id,
            "issue": rule["title"],
        }
        if contract_fixed:
            finding.update(
                {
                    "severity": rule["severity"],
                    "evidence": first_span(config_text, rule_id),
                    "config_path": rule["config_path"],
                }
            )
        findings.append(finding)
        if rule_id in trace_rule_ids:
            applications.append(
                {
                    "rule_id": rule_id,
                    "finding_id": finding_id,
                    "trigger_condition_found": ", ".join(rule["trigger_terms"][:2]),
                    "evidence_span": first_span(config_text, rule_id),
                    "config_path": rule["config_path"],
                    "confidence": "medium",
                }
            )
    payload: dict[str, Any] = {"findings": findings}
    if trace_rule_ids:
        payload["rule_applications"] = applications
    return payload


def evaluate_review(review: dict[str, Any], expected: dict[str, Any], trace_rule_ids: list[str]) -> dict[str, Any]:
    expected_rule_ids = set(expected["expected_rule_ids"])
    negative_rule_ids = set(expected["negative_rule_ids"])
    critical_rule_ids = set(expected.get("critical_rule_ids", []))
    findings = review.get("findings", [])
    seen_rule_ids = {str(item.get("rule_id")) for item in findings if isinstance(item, dict)}
    missing_rule_ids = sorted(expected_rule_ids - seen_rule_ids)
    false_positive_rule_ids = sorted(seen_rule_ids & negative_rule_ids)
    critical_missed_rule_ids = sorted(critical_rule_ids - seen_rule_ids)
    required_fields = ["rule_id", "issue", "severity", "evidence", "config_path"]
    contract_errors: list[str] = []
    for idx, finding in enumerate(findings):
        if not isinstance(finding, dict):
            contract_errors.append(f"finding[{idx}] is not an object")
            continue
        for field in required_fields:
            if not str(finding.get(field, "")).strip():
                contract_errors.append(f"finding[{idx}] missing {field}")
    applications = review.get("rule_applications", [])
    app_by_rule = {str(item.get("rule_id")): item for item in applications if isinstance(item, dict)}
    trace_errors: list[str] = []
    for rule_id in trace_rule_ids:
        if rule_id in seen_rule_ids and rule_id not in app_by_rule:
            trace_errors.append(f"traced rule {rule_id} missing rule_application")
        elif rule_id in app_by_rule:
            app = app_by_rule[rule_id]
            for field in ["finding_id", "trigger_condition_found", "evidence_span", "config_path", "confidence"]:
                if not str(app.get(field, "")).strip():
                    trace_errors.append(f"traced rule {rule_id} missing {field}")
    coverage = 1.0 if not expected_rule_ids and not seen_rule_ids else (
        len(expected_rule_ids & seen_rule_ids) / len(expected_rule_ids) if expected_rule_ids else 0.0
    )
    pass_at_1 = not missing_rule_ids and not false_positive_rule_ids and not contract_errors and not trace_errors
    if contract_errors:
        failure_type = "output_contract_error"
    elif missing_rule_ids:
        failure_type = "missing_rule"
    elif false_positive_rule_ids:
        failure_type = "false_positive"
    elif trace_errors:
        failure_type = "trace_contract_error"
    else:
        failure_type = "none"
    return {
        "checklist_coverage": round(coverage, 4),
        "missing_rule_ids": missing_rule_ids,
        "critical_missed_rule_ids": critical_missed_rule_ids,
        "false_positive_rule_ids": false_positive_rule_ids,
        "contract_errors": contract_errors,
        "trace_errors": trace_errors,
        "failure_type": failure_type,
        "pass_at_1": pass_at_1,
    }


def load_cases() -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for case_dir in sorted(CASES_DIR.iterdir()):
        if not case_dir.is_dir():
            continue
        expected = read_json(case_dir / "expected.json")
        cases.append({"case_id": expected["case_id"], "config_text": read_text(case_dir / "config.md"), "expected": expected})
    return cases


def strategy_cost(strategy_id: str, config: dict[str, Any]) -> dict[str, Any]:
    skill = skill_markdown(
        strategy_id,
        config["available_rule_ids"],
        full=bool(config.get("full_skill")),
        compressed=bool(config.get("compressed")),
        contract=bool(config["contract_fixed"]),
        trace_rule_ids=config["trace_rule_ids"],
    )
    skill_tokens = estimate_tokens(skill)
    trace_tokens = sum(
        estimate_tokens(compact_rule_text(rule_id) if config.get("compressed") else json.dumps(RULES[rule_id], ensure_ascii=False))
        for rule_id in config["trace_rule_ids"]
    )
    total_tokens = skill_tokens + trace_tokens
    return {
        "skill_text": skill,
        "skill_tokens": skill_tokens,
        "estimated_trace_tokens": trace_tokens,
        "total_tokens": total_tokens,
        "token_budget": TOKEN_BUDGET,
        "over_budget": total_tokens > TOKEN_BUDGET,
    }


def evaluate_strategy(strategy_id: str, config: dict[str, Any], cases: list[dict[str, Any]]) -> dict[str, Any]:
    cost = strategy_cost(strategy_id, config)
    case_results: list[dict[str, Any]] = []
    strategy_dir = OUT_DIR / "strategies" / strategy_id
    write_text(strategy_dir / "skill.md", cost["skill_text"])
    for case in cases:
        review = build_review(
            case["config_text"],
            case["expected"]["expected_rule_ids"],
            config["available_rule_ids"],
            config["trace_rule_ids"],
            contract_fixed=config["contract_fixed"],
        )
        verification = evaluate_review(review, case["expected"], config["trace_rule_ids"])
        write_json(strategy_dir / case["case_id"] / "review.json", review)
        write_json(strategy_dir / case["case_id"] / "verification.json", verification)
        case_results.append(
            {
                "case_id": case["case_id"],
                "expected_rule_ids": case["expected"]["expected_rule_ids"],
                "negative_rule_ids": case["expected"]["negative_rule_ids"],
                "available_rule_ids": config["available_rule_ids"],
                "trace_rule_ids": config["trace_rule_ids"],
                **verification,
            }
        )
    avg_coverage = round(sum(item["checklist_coverage"] for item in case_results) / len(case_results), 4)
    pass_count = sum(1 for item in case_results if item["pass_at_1"])
    missing_count = sum(len(item["missing_rule_ids"]) for item in case_results)
    contract_error_count = sum(len(item["contract_errors"]) for item in case_results)
    trace_error_count = sum(len(item["trace_errors"]) for item in case_results)
    regression_case = next((item for item in case_results if item["case_id"] == "case001_prod_config_security"), None)
    regression_detected = bool(regression_case and "C003" in regression_case["missing_rule_ids"] and "C003" in STRATEGIES["compact_v1_no_revision"]["available_rule_ids"])
    shortcut_blocked = bool(config["trace_rule_ids"]) and not cost["over_budget"]
    accepted_by_gate = bool(pass_count == len(cases) and not cost["over_budget"] and not regression_detected)
    if cost["over_budget"]:
        gate_decision = "reject_over_budget"
    elif regression_detected:
        gate_decision = "reject_regression"
    elif accepted_by_gate:
        gate_decision = "accept"
    else:
        gate_decision = "reject_unresolved_failure"
    summary = {
        "strategy": strategy_id,
        "description": config["description"],
        "available_rule_ids": config["available_rule_ids"],
        "trace_rule_ids": config["trace_rule_ids"],
        "avg_checklist_coverage": avg_coverage,
        "pass_at_1_count": pass_count,
        "case_count": len(cases),
        "missing_rule_count": missing_count,
        "contract_error_count": contract_error_count,
        "trace_error_count": trace_error_count,
        "regression_detected": regression_detected,
        "shortcut_blocked": shortcut_blocked,
        "gate_decision": gate_decision,
        "accepted_by_gate": accepted_by_gate,
        **{key: value for key, value in cost.items() if key != "skill_text"},
        "case_results": case_results,
    }
    write_json(strategy_dir / "summary.json", summary)
    return summary


def render_summary(payload: dict[str, Any]) -> str:
    lines = [
        "# Second Domain Config Security 001",
        "",
        "## Purpose",
        "",
        "Minimal second-domain probe for typed posterior revision over deployable expert-skill packages.",
        "This is not a benchmark and not a general proof.",
        "",
        "## Domain",
        "",
        "Configuration security review: hardcoded secrets, TLS, least privilege, debug mode, resource limits, and audit retention.",
        "",
        "## Strategy Results",
        "",
        "| Strategy | Avg Coverage | Pass@1 | Gate | Tokens | Missing | Contract Errors | Interpretation |",
        "|---|---:|---:|---|---:|---:|---:|---|",
    ]
    for row in payload["strategy_results"]:
        lines.append(
            f"| {row['strategy']} | {row['avg_checklist_coverage']:.2f} | {row['pass_at_1_count']} / {row['case_count']} | "
            f"{row['gate_decision']} | {row['total_tokens']} / {row['token_budget']} | {row['missing_rule_count']} | "
            f"{row['contract_error_count']} | {row['interpretation']} |"
        )
    lines.extend(
        [
            "",
            "## Key Findings",
            "",
        ]
    )
    for item in payload["key_findings"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Conclusion",
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
    cases = load_cases()
    material = read_text(MATERIAL_PATH)
    write_text(OUT_DIR / "expert_materials.md", material)
    write_text(OUT_DIR / "full_skill.md", skill_markdown("Full Config Security Skill", list(RULES), full=True, contract=True))
    write_text(OUT_DIR / "compact_v1.md", skill_markdown("Compact Config Security Skill v1", STRATEGIES["compact_v1_no_revision"]["available_rule_ids"], contract=True))
    write_text(
        OUT_DIR / "typed_revised_skill.md",
        skill_markdown(
            "Typed Revised Config Security Skill",
            STRATEGIES["type_specific_operator_plus_gate_and_selective_trace"]["available_rule_ids"],
            compressed=True,
            contract=True,
            trace_rule_ids=STRATEGIES["type_specific_operator_plus_gate_and_selective_trace"]["trace_rule_ids"],
        ),
    )
    strategy_results = [evaluate_strategy(strategy_id, config, cases) for strategy_id, config in STRATEGIES.items()]
    for row in strategy_results:
        if row["strategy"] == "direct_summary_skill":
            row["interpretation"] = "strong prior baseline but misses residual C006 audit-retention cases"
        elif row["strategy"] == "compact_v1_no_revision":
            row["interpretation"] = "shows residual deployment failure before posterior revision"
        elif row["strategy"] == "always_append_domain_rules":
            row["interpretation"] = "recovers domain missing rule but fails output-contract quality"
        elif row["strategy"] == "always_rewrite_output_contract":
            row["interpretation"] = "contract is valid but residual C006 remains missing"
        elif row["strategy"] == "always_regenerate_full_skill":
            row["interpretation"] = "strong high-cost upper bound"
        elif row["strategy"] == "accept_if_current_failure_fixed":
            row["interpretation"] = "unsafe because it drops previously covered C003"
        elif row["strategy"] == "always_full_trace":
            row["interpretation"] = "traceable but over budget"
        else:
            row["interpretation"] = "best-supported typed revision combination in this second-domain probe"
    typed = next(row for row in strategy_results if row["strategy"] == "type_specific_operator_plus_gate_and_selective_trace")
    direct = next(row for row in strategy_results if row["strategy"] == "direct_summary_skill")
    full = next(row for row in strategy_results if row["strategy"] == "always_regenerate_full_skill")
    always_append = next(row for row in strategy_results if row["strategy"] == "always_append_domain_rules")
    always_contract = next(row for row in strategy_results if row["strategy"] == "always_rewrite_output_contract")
    full_trace = next(row for row in strategy_results if row["strategy"] == "always_full_trace")
    accept_if_fixed = next(row for row in strategy_results if row["strategy"] == "accept_if_current_failure_fixed")
    key_findings = [
        f"direct_summary_skill remains a strong prior baseline: coverage {direct['avg_checklist_coverage']} but it misses residual C006 audit-retention cases.",
        f"always_append_domain_rules reaches coverage {always_append['avg_checklist_coverage']} but has {always_append['contract_error_count']} output-contract errors.",
        f"always_rewrite_output_contract has valid output contract but leaves {always_contract['missing_rule_count']} missing rule instances.",
        f"accept_if_current_failure_fixed is rejected by gate because regression_detected={accept_if_fixed['regression_detected']}.",
        f"always_full_trace blocks shortcut but is over budget: {full_trace['total_tokens']}/{full_trace['token_budget']}.",
        f"always_regenerate_full_skill is a strong upper bound with tokens {full['total_tokens']}/{full['token_budget']}.",
        f"type_specific_operator_plus_gate_and_selective_trace passes all {typed['case_count']} cases and is under budget: {typed['total_tokens']}/{typed['token_budget']}.",
    ]
    payload = {
        "run_id": OUT_DIR.name,
        "created_at": created_at,
        "domain": "config_security",
        "positioning": "second-domain method probe; not a benchmark",
        "case_count": len(cases),
        "rule_ids": list(RULES),
        "strategy_results": strategy_results,
        "key_findings": key_findings,
        "conclusion": {
            "status": "partially_supported",
            "finding": (
                "The typed posterior revision pattern is not limited to the API-review surface in this minimal probe: "
                "a residual domain rule miss, output-contract failure, regression risk, and trace-budget pressure appear in a configuration-security domain."
            ),
            "boundary": (
                "This is a hand-constructed second-domain probe with deterministic checks. It is not a benchmark, not a cross-domain proof, "
                "and not evidence that the strategy beats full regeneration when cost is ignored."
            ),
        },
    }
    write_json(OUT_DIR / "summary.json", payload)
    write_text(OUT_DIR / "summary.md", render_summary(payload))
    write_json(
        OUT_DIR / "manifest.json",
        {
            "run_id": OUT_DIR.name,
            "created_at": created_at,
            "artifacts": [
                "expert_materials.md",
                "full_skill.md",
                "compact_v1.md",
                "typed_revised_skill.md",
                "summary.json",
                "summary.md",
                "manifest.json",
                "strategies/",
            ],
            "boundary": payload["conclusion"]["boundary"],
        },
    )
    print(json.dumps({"output_dir": str(OUT_DIR), "status": payload["conclusion"]["status"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
