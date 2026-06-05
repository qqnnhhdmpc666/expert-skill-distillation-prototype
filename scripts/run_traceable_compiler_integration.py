from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from run_mvp_vertical_slice import estimate_tokens


OUT_DIR = Path("outputs/mvp_vertical_slice/traceable_compiler_integration_001")
CASE_PATH = Path("data/harbor_api_review_tasks/api-review-001-compact-v1/case_001_openapi.md")
TOKEN_BUDGET = 237
RULE_IDS = ["R001", "R002", "R003", "R004", "R005", "R006"]
PLAIN_SKILL = Path("outputs/mvp_vertical_slice/baseline_001/compact_skill_v1.md")
COMPRESSED_SKILL = Path("outputs/mvp_vertical_slice/validation_aware_compiler_001/candidate_skills/candidate_C_compressed_required_rules.md")
PROTOCOLIZED_SKILL = Path("outputs/mvp_vertical_slice/skill_to_agent_loop_001/skill_variants/protocolized_compressed_skill.md")
MOCK_FINDINGS = {
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


def extract_rule_ids(skill_text: str) -> list[str]:
    return sorted(set(re.findall(r"\[(R00[1-6])\]", skill_text)))


def split_protocol(skill_text: str) -> tuple[str, str]:
    marker = "## Skill Invocation Protocol"
    if marker not in skill_text:
        return skill_text, ""
    before, after = skill_text.split(marker, 1)
    return before.rstrip() + "\n", marker + after


def build_review(rule_ids: list[str], include_trace: bool) -> dict[str, Any]:
    findings = []
    applications = []
    for idx, rule_id in enumerate(rule_ids, start=1):
        finding_id = f"F{idx}"
        template = MOCK_FINDINGS[rule_id]
        findings.append(
            {
                "id": finding_id,
                "rule_id": rule_id,
                "issue": template["issue"],
                "severity": template["severity"],
                "evidence": template["evidence"],
            }
        )
        if include_trace:
            applications.append(
                {
                    "rule_id": rule_id,
                    "applicable": True,
                    "trigger_condition_found": template["trigger"],
                    "evidence_span": template["span"],
                    "finding_id": finding_id,
                    "confidence": "medium",
                }
            )
    payload: dict[str, Any] = {"findings": findings}
    if include_trace:
        payload["rule_applications"] = applications
    return payload


def run_command(command: list[str]) -> None:
    subprocess.run(command, text=True, capture_output=True, check=False)


def verify(review_path: Path, run_dir: Path) -> dict[str, Any]:
    simple_path = run_dir / "simple_verification.json"
    semantic_path = run_dir / "semantic_verification.json"
    trace_path = run_dir / "trace_verification.json"
    run_command([sys.executable, "scripts/verify_api_review_json.py", "--review", str(review_path), "--output", str(simple_path)])
    run_command([sys.executable, "scripts/verify_api_review_semantic_json.py", "--review", str(review_path), "--case", str(CASE_PATH), "--output", str(semantic_path)])
    run_command([sys.executable, "scripts/verify_api_review_trace_json.py", "--review", str(review_path), "--case", str(CASE_PATH), "--output", str(trace_path)])
    simple = read_json(simple_path)
    semantic = read_json(semantic_path)
    trace = read_json(trace_path)
    return {
        "simple_verifier_result": simple,
        "semantic_verifier_result": semantic,
        "trace_verifier_result": trace,
        "simple_verifier_passed": simple["passed"],
        "semantic_verifier_passed": semantic["passed"],
        "trace_verifier_passed": trace["passed"],
    }


def gate_decision(
    *,
    variant_id: str,
    rule_ids: list[str],
    skill_tokens: int,
    protocol_tokens: int,
    trace_passed: bool,
    regression_detected: bool,
    include_gate: bool,
) -> dict[str, Any]:
    over_budget = skill_tokens + protocol_tokens > TOKEN_BUDGET
    missing_required = [rule_id for rule_id in RULE_IDS if rule_id not in rule_ids]
    if not include_gate:
        return {
            "gate_enabled": False,
            "accepted_by_gate": None,
            "regression_detected": regression_detected,
            "over_budget": over_budget,
            "decision": "not_gated",
            "reason": "Validation gate is not enabled for this variant.",
        }
    accepted = not missing_required and not regression_detected and not over_budget and trace_passed
    if accepted:
        decision = "accept"
        reason = "All required rules are present, trace verification passes, no regression is detected, and token budget is respected."
    elif over_budget:
        decision = "reject_over_budget"
        reason = "Candidate exceeds fixed token budget."
    elif regression_detected:
        decision = "reject_regression"
        reason = "Candidate misses rules that should be preserved."
    elif not trace_passed:
        decision = "reject_trace_failure"
        reason = "Candidate output is not supported by valid rule-application traces."
    else:
        decision = "reject_missing_required_rules"
        reason = f"Candidate misses required rules: {', '.join(missing_required)}."
    return {
        "gate_enabled": True,
        "accepted_by_gate": accepted,
        "regression_detected": regression_detected,
        "over_budget": over_budget,
        "decision": decision,
        "reason": reason,
    }


def make_variant(variant_id: str, skill_path: Path, include_protocol: bool, include_gate: bool) -> dict[str, Any]:
    skill_text = read_text(skill_path)
    rules_text, protocol_text = split_protocol(skill_text)
    if not include_protocol:
        protocol_text = ""
    rule_ids = extract_rule_ids(skill_text)
    skill_tokens = estimate_tokens(rules_text)
    protocol_tokens = estimate_tokens(protocol_text) if protocol_text else 0
    run_dir = OUT_DIR / variant_id
    review = build_review(rule_ids, include_trace=include_protocol)
    review_path = run_dir / "review.json"
    write_json(review_path, review)
    verification = verify(review_path, run_dir)
    regression_detected = any(rule_id not in rule_ids for rule_id in RULE_IDS)
    gate = gate_decision(
        variant_id=variant_id,
        rule_ids=rule_ids,
        skill_tokens=skill_tokens,
        protocol_tokens=protocol_tokens,
        trace_passed=bool(verification["trace_verifier_passed"]),
        regression_detected=regression_detected,
        include_gate=include_gate,
    )
    payload = {
        "variant_id": variant_id,
        "skill_path": str(skill_path),
        "rule_ids": rule_ids,
        "token_budget": TOKEN_BUDGET,
        "skill_tokens": skill_tokens,
        "protocol_tokens": protocol_tokens,
        "total_tokens": skill_tokens + protocol_tokens,
        "protocol_overhead_tokens": protocol_tokens,
        "protocol_overhead_ratio": round(protocol_tokens / skill_tokens, 4) if skill_tokens else 0,
        "include_protocol": include_protocol,
        "include_gate": include_gate,
        "generated_findings": review["findings"],
        "generated_rule_applications": review.get("rule_applications", []),
        "regression_detected": regression_detected,
        **verification,
        **gate,
    }
    write_json(run_dir / "variant_summary.json", payload)
    return payload


def render_summary(payload: dict[str, Any]) -> str:
    lines = [
        "# Traceable Compiler Integration 001",
        "",
        "## Positioning",
        "",
        "This integration slice combines fixed-budget compact rules, validation gate checks, and skill-to-agent trace protocol.",
        "",
        "| Variant | Tokens | Protocol Tokens | Simple | Semantic | Trace | Regression | Gate |",
        "|---|---:|---:|---|---|---|---|---|",
    ]
    for row in payload["variants"]:
        gate = row["decision"] if row["gate_enabled"] else "not gated"
        lines.append(
            f"| {row['variant_id']} | {row['total_tokens']} / {row['token_budget']} | {row['protocol_tokens']} | "
            f"{row['simple_verifier_passed']} | {row['semantic_verifier_passed']} | {row['trace_verifier_passed']} | "
            f"{row['regression_detected']} | {gate} |"
        )
    lines.extend(
        [
            "",
            "## Questions",
            "",
            f"- Protocol overhead acceptable: {payload['questions']['protocol_overhead_acceptable']}",
            f"- Trace verifier blocks shallow output: {payload['questions']['trace_verifier_blocks_shallow_output']}",
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
        make_variant("A_plain_compact_skill", PLAIN_SKILL, include_protocol=False, include_gate=False),
        make_variant("B_compressed_compact_skill", COMPRESSED_SKILL, include_protocol=False, include_gate=False),
        make_variant("C_compressed_plus_protocol", PROTOCOLIZED_SKILL, include_protocol=True, include_gate=False),
        make_variant("D_compressed_plus_protocol_plus_gate", PROTOCOLIZED_SKILL, include_protocol=True, include_gate=True),
    ]
    protocolized = next(row for row in variants if row["variant_id"] == "D_compressed_plus_protocol_plus_gate")
    shallow = [row for row in variants if row["variant_id"] in {"A_plain_compact_skill", "B_compressed_compact_skill"}]
    protocol_overhead_acceptable = protocolized["total_tokens"] <= TOKEN_BUDGET
    trace_blocks_shallow = all(not row["trace_verifier_passed"] for row in shallow) and protocolized["trace_verifier_passed"]
    if protocolized["trace_verifier_passed"] and protocolized["total_tokens"] > TOKEN_BUDGET:
        status = "partially_supported_with_protocol_overhead"
        finding = "Protocolized variant passes trace verification but exceeds the fixed token budget."
    elif protocolized["trace_verifier_passed"] and protocolized["total_tokens"] <= TOKEN_BUDGET:
        status = "partially_supported"
        finding = "Traceable compact compilation is feasible in this toy slice."
    else:
        status = "inconclusive"
        finding = "Protocolized variant does not satisfy trace verification and budget constraints."
    payload = {
        "run_id": OUT_DIR.name,
        "created_at": created_at,
        "definition": "Validation-aware, traceable compact skill compiler",
        "token_budget": TOKEN_BUDGET,
        "variants": variants,
        "questions": {
            "protocol_overhead_acceptable": protocol_overhead_acceptable,
            "protocol_overhead_tokens": protocolized["protocol_tokens"],
            "protocol_total_tokens": protocolized["total_tokens"],
            "trace_verifier_blocks_shallow_output": trace_blocks_shallow,
        },
        "conclusion": {
            "status": status,
            "finding": finding,
            "boundary": "Toy integration slice only. It does not prove general correctness or a universal compiler.",
        },
    }
    write_json(OUT_DIR / "summary.json", payload)
    write_json(OUT_DIR / "variant_results.json", variants)
    write_json(
        OUT_DIR / "compiler_contract.json",
        {
            "deployment_artifact_parts": ["compact skill rules", "invocation protocol", "trace verifier contract"],
            "m2_role": "fixed-budget rule selection / compression",
            "m3_role": "patch accept / reject / rollback",
            "m5_role": "agent rule-application trace verification",
        },
    )
    write_text(OUT_DIR / "summary.md", render_summary(payload))
    write_json(
        OUT_DIR / "manifest.json",
        {
            "run_id": OUT_DIR.name,
            "created_at": created_at,
            "artifacts": ["summary.json", "summary.md", "variant_results.json", "compiler_contract.json", "*/variant_summary.json"],
            "boundary": payload["conclusion"]["boundary"],
        },
    )
    print(json.dumps({"output_dir": str(OUT_DIR), "status": status}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
