from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


OUT_DIR = Path("outputs/mvp_vertical_slice/skill_to_agent_loop_001")
CASES = {
    "case001": Path("data/harbor_api_review_tasks/api-review-001-compact-v1/case_001_openapi.md"),
    "case002": Path("data/harbor_api_review_tasks/api-review-002-compact-v1/case_002_openapi.md"),
}
CANDIDATE_C = Path("outputs/mvp_vertical_slice/validation_aware_compiler_001/candidate_skills/candidate_C_compressed_required_rules.md")
RULE_IDS = ["R001", "R002", "R003", "R004", "R005", "R006"]
RULE_LINES = {
    "R001": "Auth method, roles/scopes, and auth-failure behavior.",
    "R002": "Request fields: required/default, type, range, length, enum.",
    "R003": "Stable error codes for validation, auth, permission, not found, duplicate, server.",
    "R004": "No tokens, secrets, stack traces, identity, or unnecessary personal data.",
    "R005": "Response envelope: code, message, request_id, data.",
    "R006": "Mutation idempotency or duplicate-submission handling.",
}
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


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def strip_fence(text: str) -> str:
    stripped = text.strip()
    match = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", stripped, flags=re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else stripped


def extract_json(text: str) -> dict[str, Any]:
    stripped = strip_fence(text)
    start = stripped.find("{")
    if start < 0:
        raise ValueError("No JSON object found.")
    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(stripped)):
        char = stripped[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return json.loads(stripped[start : index + 1])
    raise ValueError("JSON object was not balanced.")


def create_skill_variants() -> dict[str, Path]:
    skill_dir = OUT_DIR / "skill_variants"
    candidate = read_text(CANDIDATE_C)
    shortcut = "\n".join(
        [
            "# Rule-ID Shortcut Skill",
            "",
            "Review the API using these rule IDs:",
            "",
            *[f"- [{rule_id}]" for rule_id in RULE_IDS],
            "",
            "Return JSON findings.",
            "",
        ]
    )
    protocol = "\n".join(
        [
            "# Protocolized Compressed Skill",
            "",
            "Use the compact rules below and expose how each rule was applied to the case.",
            "",
            "## Checklist",
            "",
            *[f"- [{rule_id}] {RULE_LINES[rule_id]}" for rule_id in RULE_IDS],
            "",
            "## Skill Invocation Protocol",
            "",
            "Return JSON only with both `rule_applications` and `findings`.",
            "Each finding must be supported by exactly one rule_application through `finding_id`.",
            "",
            "```json",
            "{",
            '  "rule_applications": [',
            "    {",
            '      "rule_id": "R005",',
            '      "applicable": true,',
            '      "trigger_condition_found": "response envelope missing request_id",',
            '      "evidence_span": "Response JSON has code, message, data",',
            '      "finding_id": "F5",',
            '      "confidence": "medium"',
            "    }",
            "  ],",
            '  "findings": [',
            "    {",
            '      "id": "F5",',
            '      "rule_id": "R005",',
            '      "issue": "...",',
            '      "severity": "high|medium|low",',
            '      "evidence": "..."',
            "    }",
            "  ]",
            "}",
            "```",
            "",
        ]
    )
    variants = {
        "candidate_C_compressed_skill": skill_dir / "candidate_C_compressed_skill.md",
        "rule_id_shortcut_skill": skill_dir / "rule_id_shortcut_skill.md",
        "protocolized_compressed_skill": skill_dir / "protocolized_compressed_skill.md",
    }
    write_text(variants["candidate_C_compressed_skill"], candidate)
    write_text(variants["rule_id_shortcut_skill"], shortcut)
    write_text(variants["protocolized_compressed_skill"], protocol)
    return variants


def run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, text=True, capture_output=True, check=False)


def verify_all(review_path: Path, case_path: Path, run_dir: Path) -> dict[str, Any]:
    semantic_path = run_dir / "semantic_verification_result.json"
    trace_path = run_dir / "trace_verification_result.json"
    local_path = run_dir / "local_verification_result.json"
    if review_path.exists():
        run_command([sys.executable, "scripts/verify_api_review_json.py", "--review", str(review_path), "--output", str(local_path)])
        run_command([sys.executable, "scripts/verify_api_review_semantic_json.py", "--review", str(review_path), "--case", str(case_path), "--output", str(semantic_path)])
        run_command([sys.executable, "scripts/verify_api_review_trace_json.py", "--review", str(review_path), "--case", str(case_path), "--output", str(trace_path)])
    local = read_json(local_path) if local_path.exists() else None
    semantic = read_json(semantic_path) if semantic_path.exists() else None
    trace = read_json(trace_path) if trace_path.exists() else None
    return {
        "local_verifier_passed": local.get("passed") if local else None,
        "semantic_verifier_passed": semantic.get("passed") if semantic else None,
        "trace_verifier_passed": trace.get("passed") if trace else None,
        "local_verification": str(local_path) if local else None,
        "semantic_verification": str(semantic_path) if semantic else None,
        "trace_verification": str(trace_path) if trace else None,
        "semantic_errors": semantic.get("semantic_errors") if semantic else [],
        "trace_errors": trace.get("trace_errors") if trace else [],
    }


def mock_findings_payload(rule_ids: list[str], include_trace: bool) -> dict[str, Any]:
    findings = []
    applications = []
    for idx, rule_id in enumerate(rule_ids, start=1):
        finding_id = f"F{idx}"
        template = MOCK_FINDINGS[rule_id]
        finding = {
            "id": finding_id,
            "rule_id": rule_id,
            "issue": template["issue"],
            "severity": template["severity"],
            "evidence": template["evidence"],
        }
        findings.append(finding)
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
    payload = {"findings": findings}
    if include_trace:
        payload["rule_applications"] = applications
    return payload


def extract_rule_ids_from_skill(skill_path: Path) -> list[str]:
    return sorted(set(re.findall(r"\[(R00[1-6])\]", read_text(skill_path))))


def run_mock(case_id: str, case_path: Path, variant: str, skill_path: Path) -> dict[str, Any]:
    run_dir = OUT_DIR / f"{case_id}_mock_{variant}"
    review_path = run_dir / "review.json"
    include_trace = variant == "protocolized_compressed_skill"
    rule_ids = extract_rule_ids_from_skill(skill_path)
    write_json(review_path, mock_findings_payload(rule_ids, include_trace))
    verification = verify_all(review_path, case_path, run_dir)
    return {
        "case": case_id,
        "agent": "mock",
        "variant": variant,
        "skill": str(skill_path),
        "review": str(review_path),
        "generated_review_rule_ids": rule_ids,
        "has_rule_applications": include_trace,
        "agent_status": "ok",
        **verification,
    }


def call_llm_protocol(skill_text: str, case_text: str) -> dict[str, Any]:
    base_url = os.environ.get("OPENAI_BASE_URL")
    api_key = os.environ.get("OPENAI_API_KEY")
    model = os.environ.get("MODEL")
    if not base_url or not api_key or not model:
        raise RuntimeError("OPENAI_BASE_URL, OPENAI_API_KEY, and MODEL must be set.")
    messages = [
        {
            "role": "system",
            "content": "You are an API review agent. Follow the skill invocation protocol exactly. Return only valid JSON.",
        },
        {
            "role": "user",
            "content": f"""Compact skill:

{skill_text}

API case:

{case_text}

Return JSON with both rule_applications and findings. Do not use markdown fences.""",
        },
    ]
    request_payload = json.dumps({"model": model, "messages": messages, "stream": False, "temperature": 0.0}).encode("utf-8")
    last_error: Exception | None = None
    payload: dict[str, Any] | None = None
    for _ in range(3):
        request = urllib.request.Request(
            base_url.rstrip("/") + "/chat/completions",
            data=request_payload,
            headers={"authorization": f"Bearer {api_key}", "content-type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=60.0) as response:
                payload = json.loads(response.read().decode("utf-8"))
            break
        except urllib.error.URLError as exc:
            last_error = exc
    if payload is None:
        raise last_error or RuntimeError("LLM protocol call failed without a captured error.")
    content = payload["choices"][0]["message"]["content"]
    parsed = extract_json(content)
    return {"parsed": parsed, "usage": payload.get("usage"), "raw_content_preview": content[:500]}


def run_llm(case_id: str, case_path: Path, variant: str, skill_path: Path) -> dict[str, Any]:
    run_dir = OUT_DIR / f"{case_id}_rightcode_gpt_{variant}"
    review_path = run_dir / "review.json"
    diagnostic_path = run_dir / "llm_agent_diagnostic.json"
    env_ready = all(os.environ.get(name) for name in ("OPENAI_BASE_URL", "OPENAI_API_KEY", "MODEL"))
    if not env_ready:
        write_json(diagnostic_path, {"status": "skipped", "reason": "OPENAI_BASE_URL, OPENAI_API_KEY, and MODEL must be set."})
        return {
            "case": case_id,
            "agent": "rightcode_gpt",
            "variant": variant,
            "skill": str(skill_path),
            "review": None,
            "generated_review_rule_ids": [],
            "has_rule_applications": None,
            "agent_status": "skipped",
            "diagnostic": str(diagnostic_path),
            "local_verifier_passed": None,
            "semantic_verifier_passed": None,
            "trace_verifier_passed": None,
            "semantic_errors": [],
            "trace_errors": [],
        }
    try:
        result = call_llm_protocol(read_text(skill_path), read_text(case_path))
        write_json(review_path, result["parsed"])
        diagnostic = {
            "status": "ok",
            "model": os.environ.get("MODEL"),
            "usage": result.get("usage"),
            "raw_content_preview": result.get("raw_content_preview"),
        }
        write_json(diagnostic_path, diagnostic)
    except (OSError, urllib.error.URLError, urllib.error.HTTPError, ValueError, json.JSONDecodeError, KeyError) as exc:
        write_json(diagnostic_path, {"status": "error", "error": str(exc)})
        return {
            "case": case_id,
            "agent": "rightcode_gpt",
            "variant": variant,
            "skill": str(skill_path),
            "review": None,
            "generated_review_rule_ids": [],
            "has_rule_applications": None,
            "agent_status": "error",
            "diagnostic": str(diagnostic_path),
            "local_verifier_passed": None,
            "semantic_verifier_passed": None,
            "trace_verifier_passed": None,
            "semantic_errors": [],
            "trace_errors": [str(exc)],
        }
    verification = verify_all(review_path, case_path, run_dir)
    parsed = read_json(review_path)
    findings = parsed.get("findings") if isinstance(parsed, dict) else []
    applications = parsed.get("rule_applications") if isinstance(parsed, dict) else []
    rule_ids = sorted({str(finding.get("rule_id")) for finding in findings if isinstance(finding, dict) and finding.get("rule_id")})
    return {
        "case": case_id,
        "agent": "rightcode_gpt",
        "variant": variant,
        "skill": str(skill_path),
        "review": str(review_path),
        "generated_review_rule_ids": rule_ids,
        "has_rule_applications": isinstance(applications, list),
        "agent_status": "ok",
        "diagnostic": str(diagnostic_path),
        **verification,
    }


def render_summary(summary: dict[str, Any]) -> str:
    lines = [
        "# Skill-to-Agent Loop 001",
        "",
        "## Positioning",
        "",
        "This is an M5 probe: compact skill should not only enter the prompt; the agent should expose rule-application traces that a verifier can inspect.",
        "",
        "| Case | Agent | Variant | Rule IDs | Has Trace | Local | Semantic | Trace |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for run in summary["runs"]:
        lines.append(
            f"| {run['case']} | {run['agent']} | {run['variant']} | {', '.join(run['generated_review_rule_ids']) or 'none'} | "
            f"{run['has_rule_applications']} | {run['local_verifier_passed']} | {run['semantic_verifier_passed']} | {run['trace_verifier_passed']} |"
        )
    lines.extend(
        [
            "",
            "## Conservative Conclusion",
            "",
            f"- Status: {summary['conclusion_status']}",
            f"- Finding: {summary['finding']}",
            f"- Boundary: {summary['boundary']}",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    created_at = datetime.now(timezone.utc).isoformat()
    variants = create_skill_variants()
    runs: list[dict[str, Any]] = []
    for case_id, case_path in CASES.items():
        for variant, skill_path in variants.items():
            runs.append(run_mock(case_id, case_path, variant, skill_path))
    for case_id, case_path in CASES.items():
        for variant, skill_path in variants.items():
            runs.append(run_llm(case_id, case_path, variant, skill_path))
    protocol_runs = [run for run in runs if run["variant"] == "protocolized_compressed_skill"]
    shortcut_runs = [run for run in runs if run["variant"] == "rule_id_shortcut_skill"]
    protocol_trace_passes = [run for run in protocol_runs if run["trace_verifier_passed"] is True]
    shortcut_trace_passes = [run for run in shortcut_runs if run["trace_verifier_passed"] is True]
    attempted_protocol = [run for run in protocol_runs if run["agent_status"] != "skipped"]
    if attempted_protocol and protocol_trace_passes and not shortcut_trace_passes:
        conclusion_status = "partially_supported"
        finding = "Structured protocol helps distinguish rule-application traces from rule-id shortcut in this toy case."
    elif not attempted_protocol:
        conclusion_status = "inconclusive"
        finding = "No protocol run was attempted."
    else:
        conclusion_status = "inconclusive"
        finding = "Protocol did not clearly separate semantic rule use from shortcut behavior."
    summary = {
        "run_id": OUT_DIR.name,
        "created_at": created_at,
        "method_candidate": "M5 Skill-to-Agent Execution Protocol",
        "env_ready": all(os.environ.get(name) for name in ("OPENAI_BASE_URL", "OPENAI_API_KEY", "MODEL")),
        "model": os.environ.get("MODEL"),
        "variants": {name: str(path) for name, path in variants.items()},
        "runs": runs,
        "conclusion_status": conclusion_status,
        "finding": finding,
        "boundary": "Toy protocol probe only. It does not prove real complex-task correctness or a general agent protocol.",
    }
    write_json(OUT_DIR / "summary.json", summary)
    write_json(OUT_DIR / "protocol_results.json", runs)
    write_json(
        OUT_DIR / "semantic_verifier_results.json",
        [
            {
                "case": run["case"],
                "agent": run["agent"],
                "variant": run["variant"],
                "semantic_verifier_passed": run["semantic_verifier_passed"],
                "trace_verifier_passed": run["trace_verifier_passed"],
                "semantic_errors": run["semantic_errors"],
                "trace_errors": run["trace_errors"],
            }
            for run in runs
        ],
    )
    write_text(OUT_DIR / "summary.md", render_summary(summary))
    write_json(
        OUT_DIR / "manifest.json",
        {
            "run_id": OUT_DIR.name,
            "created_at": created_at,
            "artifacts": [
                "summary.json",
                "summary.md",
                "protocol_results.json",
                "semantic_verifier_results.json",
                "skill_variants/",
            ],
            "boundary": summary["boundary"],
        },
    )
    print(json.dumps({"output_dir": str(OUT_DIR), "conclusion_status": conclusion_status, "env_ready": summary["env_ready"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
