from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STRICT_REQUIRED_FIELDS = {"capability_id", "evidence_span", "recommended_fix"}
CONTRACT_MODE_REQUIRED_FIELDS = {
    "strict": STRICT_REQUIRED_FIELDS,
    "evidence_only": {"capability_id", "evidence_span"},
}
RULE_TO_CAPABILITY = {
    "R005": "UPLOAD_TYPE_MAGIC",
    "R006": "UPLOAD_AUDIT_RETENTION",
    "R008": "UPLOAD_PATH_ISOLATION",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def read_all_texts(path: Path) -> dict[str, str]:
    if path.is_file():
        return {path.name: path.read_text(encoding="utf-8", errors="replace")}
    return {
        str(file_path.relative_to(path)): file_path.read_text(encoding="utf-8", errors="replace")
        for file_path in sorted(item for item in path.rglob("*") if item.is_file())
    }


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_capabilities(skill_dir: Path, skill_texts: dict[str, str]) -> list[str]:
    manifest = skill_dir / "manifest.json"
    if manifest.exists():
        payload = load_json(manifest)
        capabilities = payload.get("capabilities", [])
        if isinstance(capabilities, list) and capabilities:
            return [str(item) for item in capabilities]
    discovered = sorted(set(re.findall(r"\b[A-Z]+(?:_[A-Z]+){1,}\b", "\n".join(skill_texts.values()))))
    return [item for item in discovered if item.startswith(("UPLOAD_", "AUTH_", "CONFIG_", "API_", "DATA_"))]


def parse_active_capabilities(raw_value: str | None, available: list[str]) -> list[str]:
    if raw_value is None:
        return available
    requested = [item.strip() for item in raw_value.split(",") if item.strip()]
    requested_set = set(requested)
    return [capability_id for capability_id in available if capability_id in requested_set]


def render_files_block(title: str, files: dict[str, str], limit: int = 16000) -> str:
    chunks = [f"# {title}"]
    budget = limit
    for rel_path, text in files.items():
        snippet = text[:budget]
        chunks.append(f"\n## {rel_path}\n\n```text\n{snippet}\n```")
        budget -= len(snippet)
        if budget <= 0:
            chunks.append("\n[truncated]")
            break
    return "\n".join(chunks)


def build_prompt(
    *,
    skill_dir: Path,
    target_dir: Path,
    capabilities: list[str],
    task_label: str,
    contract_mode: str,
    prompt_addendum: str,
) -> tuple[str, list[dict[str, str]]]:
    skill_texts = read_all_texts(skill_dir)
    target_texts = read_all_texts(target_dir)
    required_fields = CONTRACT_MODE_REQUIRED_FIELDS.get(contract_mode, STRICT_REQUIRED_FIELDS)
    contract = {
        "findings": [
            {
                "capability_id": capabilities[0] if capabilities else "UPLOAD_PATH_ISOLATION",
                "issue": "short issue title",
                "evidence_span": "quote or tightly paraphrase the concrete target span, including file name when possible",
            }
        ]
    }
    if "recommended_fix" in required_fields:
        contract["findings"][0]["recommended_fix"] = "specific fix grounded in the target"
    contract_rule = (
        "- Each finding must include capability_id, issue, evidence_span, and recommended_fix."
        if "recommended_fix" in required_fields
        else "- Each finding must include capability_id, issue, and evidence_span. recommended_fix is optional in this exploratory run."
    )
    prompt = f"""You are a non-oracle {task_label} agent.

Read the target files and the Skill Package. Produce only a JSON object for the deterministic verifier.

Rules:
- Do not invent findings that are not grounded in the target text.
- Use only these capability_id values exposed by the Skill Package: {', '.join(capabilities) or '(none)'}.
- Treat the exposed capability_id list as a checklist: for each active capability, emit a finding only when the target contains exact supporting evidence for that capability.
- Evidence spans must be exact complete target lines or exact target substrings that can be traced to one complete line.
{contract_rule}
- If the Skill Package does not expose a capability, do not report it even if you notice it.
- If no exposed capability has exact evidence, return {{"findings": []}} instead of a speculative finding.
- Return JSON only. No markdown fences.
{prompt_addendum}

Expected JSON shape:
{json.dumps(contract, ensure_ascii=False, indent=2)}

{render_files_block("Skill Package", skill_texts)}

{render_files_block("Target Asset", target_texts)}
"""
    messages = [
        {
            "role": "system",
            "content": f"You are a {task_label} agent that returns JSON for a deterministic verifier.",
        },
        {"role": "user", "content": prompt},
    ]
    return prompt, messages


def strip_markdown_fence(text: str) -> str:
    stripped = text.strip()
    fence = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", stripped, flags=re.DOTALL | re.IGNORECASE)
    return fence.group(1).strip() if fence else stripped


def extract_first_json_object(text: str) -> str:
    text = strip_markdown_fence(text)
    start = text.find("{")
    if start < 0:
        raise ValueError("No JSON object start found in model output.")
    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
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
                return text[start : index + 1]
    raise ValueError("JSON object was not balanced in model output.")


def normalize_report(payload: Any, allowed_capabilities: list[str], *, contract_mode: str) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("security report must be a JSON object")
    findings = payload.get("findings")
    if not isinstance(findings, list):
        raise ValueError("security report must contain a findings array")
    allowed = set(allowed_capabilities)
    required_fields = CONTRACT_MODE_REQUIRED_FIELDS.get(contract_mode, STRICT_REQUIRED_FIELDS)
    normalized_findings: list[dict[str, str]] = []
    for index, item in enumerate(findings):
        if not isinstance(item, dict):
            raise ValueError(f"finding[{index}] must be an object")
        capability_id = str(item.get("capability_id") or RULE_TO_CAPABILITY.get(str(item.get("rule_id")), "")).strip()
        finding = {
            "capability_id": capability_id,
            "issue": str(item.get("issue") or item.get("title") or capability_id).strip(),
            "evidence_span": str(item.get("evidence_span") or item.get("evidence") or "").strip(),
            "recommended_fix": str(item.get("recommended_fix") or item.get("fix") or "").strip(),
        }
        missing = sorted(field for field in required_fields if not finding[field])
        if missing:
            raise ValueError(f"finding[{index}] missing required content: {', '.join(missing)}")
        if allowed and capability_id not in allowed:
            raise ValueError(f"finding[{index}] capability_id not allowed by Skill Package: {capability_id}")
        normalized_findings.append(finding)
    return {"backend_type": "live_llm_security_agent", "findings": normalized_findings}


def call_chat_completions(
    *,
    base_url: str,
    api_key: str,
    model: str,
    messages: list[dict[str, str]],
    temperature: float,
    timeout: float,
) -> dict[str, Any]:
    endpoint = base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "temperature": temperature,
    }
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"authorization": f"Bearer {api_key}", "content-type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def extract_message_content(response: dict[str, Any]) -> str:
    choices = response.get("choices")
    if not choices:
        raise ValueError("model response did not include choices")
    message = (choices[0] or {}).get("message") or {}
    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise ValueError("model response did not include non-empty message content")
    return content


def run_agent(
    *,
    skill_dir: Path,
    target_dir: Path,
    out_dir: Path,
    base_url: str | None,
    api_key: str | None,
    model: str | None,
    temperature: float,
    timeout: float,
    task_label: str,
    contract_mode: str,
    prompt_addendum: str,
    active_capabilities: str | None,
) -> int:
    start = time.perf_counter()
    skill_texts = read_all_texts(skill_dir)
    available_capabilities = read_capabilities(skill_dir, skill_texts)
    capabilities = parse_active_capabilities(active_capabilities, available_capabilities)
    prompt, messages = build_prompt(
        skill_dir=skill_dir,
        target_dir=target_dir,
        capabilities=capabilities,
        task_label=task_label,
        contract_mode=contract_mode,
        prompt_addendum=prompt_addendum,
    )
    write_text(out_dir / "prompt.md", prompt)
    metadata: dict[str, Any] = {
        "backend_type": "live_llm_security_agent",
        "oracle": False,
        "llm": True,
        "generated_by": "agents/llm_security_agent.py",
        "skill_dir": str(skill_dir),
        "target_dir": str(target_dir),
        "base_url_present": bool(base_url),
        "api_key_present": bool(api_key),
        "model": model,
        "available_capabilities": available_capabilities,
        "capabilities": capabilities,
        "active_capabilities": capabilities,
        "task_label": task_label,
        "contract_mode": contract_mode,
        "timestamp": utc_now(),
        "status": "started",
    }
    if not base_url or not api_key or not model:
        metadata.update(
            {
                "status": "skipped",
                "failure_reason": "env_missing",
                "message": "OPENAI_BASE_URL, OPENAI_API_KEY, and MODEL must be configured.",
                "latency_ms": int((time.perf_counter() - start) * 1000),
            }
        )
        write_text(out_dir / "raw_response.txt", "")
        write_json(out_dir / "security_report.json", {"backend_type": "live_llm_security_agent", "findings": []})
        write_json(out_dir / "model_calls.json", {"status": "skipped", "failure_reason": "env_missing"})
        write_json(out_dir / "backend_metadata.json", metadata)
        return 2
    try:
        response = call_chat_completions(
            base_url=base_url,
            api_key=api_key,
            model=model,
            messages=messages,
            temperature=temperature,
            timeout=timeout,
        )
        content = extract_message_content(response)
        write_text(out_dir / "raw_response.txt", content)
        payload = json.loads(extract_first_json_object(content))
        report = normalize_report(payload, capabilities, contract_mode=contract_mode)
        write_json(out_dir / "security_report.json", report)
        usage = response.get("usage")
        metadata.update(
            {
                "status": "ok",
                "finding_count": len(report["findings"]),
                "usage": usage,
                "latency_ms": int((time.perf_counter() - start) * 1000),
            }
        )
        write_json(
            out_dir / "model_calls.json",
            {
                "status": "ok",
                "endpoint": base_url.rstrip("/") + "/chat/completions",
                "model": model,
                "temperature": temperature,
                "usage": usage,
                "request": {"messages": messages},
                "response": response,
            },
        )
        write_json(out_dir / "backend_metadata.json", metadata)
        return 0
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        metadata.update(
            {
                "status": "error",
                "failure_reason": "api_error",
                "http_status": exc.code,
                "error": str(exc),
                "latency_ms": int((time.perf_counter() - start) * 1000),
            }
        )
        write_text(out_dir / "raw_response.txt", body)
        write_json(out_dir / "security_report.json", {"backend_type": "live_llm_security_agent", "findings": []})
        write_json(out_dir / "model_calls.json", {"status": "error", "failure_reason": "api_error", "http_status": exc.code, "response_body": body[:2000]})
        write_json(out_dir / "backend_metadata.json", metadata)
        return 1
    except (OSError, urllib.error.URLError, ValueError, json.JSONDecodeError) as exc:
        metadata.update(
            {
                "status": "error",
                "failure_reason": "network_or_parse_error",
                "error": str(exc),
                "latency_ms": int((time.perf_counter() - start) * 1000),
            }
        )
        if not (out_dir / "raw_response.txt").exists():
            write_text(out_dir / "raw_response.txt", "")
        write_json(out_dir / "security_report.json", {"backend_type": "live_llm_security_agent", "findings": []})
        write_json(out_dir / "model_calls.json", {"status": "error", "failure_reason": "network_or_parse_error", "error": str(exc)})
        write_json(out_dir / "backend_metadata.json", metadata)
        return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="OpenAI-compatible non-oracle security agent.")
    parser.add_argument("--skill", type=Path, required=True)
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--base-url", default=os.environ.get("OPENAI_BASE_URL"))
    parser.add_argument("--api-key", default=os.environ.get("OPENAI_API_KEY"))
    parser.add_argument("--model", default=os.environ.get("MODEL") or os.environ.get("OPENAI_MODEL"))
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--timeout", type=float, default=90.0)
    parser.add_argument("--task-label", default="review")
    parser.add_argument("--contract-mode", choices=sorted(CONTRACT_MODE_REQUIRED_FIELDS), default="strict")
    parser.add_argument("--prompt-addendum", default="")
    parser.add_argument("--active-capabilities", default=None)
    args = parser.parse_args()
    code = run_agent(
        skill_dir=args.skill,
        target_dir=args.target,
        out_dir=args.out,
        base_url=args.base_url,
        api_key=args.api_key,
        model=args.model,
        temperature=args.temperature,
        timeout=args.timeout,
        task_label=args.task_label,
        contract_mode=args.contract_mode,
        prompt_addendum=args.prompt_addendum,
        active_capabilities=args.active_capabilities,
    )
    metadata = load_json(args.out / "backend_metadata.json")
    print(json.dumps({"status": metadata.get("status"), "out": str(args.out), "failure_reason": metadata.get("failure_reason")}, ensure_ascii=False))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
