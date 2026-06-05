from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


REQUIRED_FINDING_FIELDS = {"rule_id", "issue", "severity", "evidence"}
VALID_SEVERITIES = {"high", "medium", "low"}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


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


def validate_review(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("Review payload must be a JSON object.")
    findings = payload.get("findings")
    if not isinstance(findings, list):
        raise ValueError("Review payload must contain a findings array.")
    normalized_findings: list[dict[str, str]] = []
    for index, finding in enumerate(findings):
        if not isinstance(finding, dict):
            raise ValueError(f"Finding {index} must be an object.")
        missing = sorted(REQUIRED_FINDING_FIELDS - set(finding))
        if missing:
            raise ValueError(f"Finding {index} is missing fields: {', '.join(missing)}.")
        normalized = {field: str(finding[field]).strip() for field in REQUIRED_FINDING_FIELDS}
        normalized["severity"] = normalized["severity"].lower()
        if normalized["severity"] not in VALID_SEVERITIES:
            raise ValueError(f"Finding {index} has invalid severity: {normalized['severity']}.")
        if not re.fullmatch(r"R\d{3}", normalized["rule_id"]):
            raise ValueError(f"Finding {index} has invalid rule_id: {normalized['rule_id']}.")
        normalized_findings.append(
            {
                "rule_id": normalized["rule_id"],
                "issue": normalized["issue"],
                "severity": normalized["severity"],
                "evidence": normalized["evidence"],
            }
        )
    return {"findings": normalized_findings}


def parse_review_from_model_output(text: str) -> dict[str, Any]:
    json_text = extract_first_json_object(text)
    return validate_review(json.loads(json_text))


def build_prompt(skill: str, case_text: str) -> list[dict[str, str]]:
    system = (
        "You are an API review agent. Follow the provided compact skill exactly. "
        "Return only a valid JSON object. Do not include markdown fences or explanations."
    )
    user = f"""Compact skill:

{skill}

API case:

{case_text}

Return exactly this JSON shape:
{{
  "findings": [
    {{
      "rule_id": "R001",
      "issue": "...",
      "severity": "high|medium|low",
      "evidence": "..."
    }}
  ]
}}
"""
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


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
        "temperature": temperature,
        "response_format": {"type": "json_object"},
    }
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "authorization": f"Bearer {api_key}",
            "content-type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def extract_message_content(response: dict[str, Any]) -> str:
    choices = response.get("choices")
    if not choices:
        raise ValueError("Model response did not include choices.")
    message = (choices[0] or {}).get("message") or {}
    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise ValueError("Model response did not include non-empty message content.")
    return content


def main() -> int:
    parser = argparse.ArgumentParser(description="OpenAI-compatible API review agent.")
    parser.add_argument("--skill", type=Path, required=True)
    parser.add_argument("--case", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--diagnostic", type=Path, default=None)
    parser.add_argument("--base-url", default=os.environ.get("OPENAI_BASE_URL"))
    parser.add_argument("--api-key", default=os.environ.get("OPENAI_API_KEY"))
    parser.add_argument("--model", default=os.environ.get("MODEL"))
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--timeout", type=float, default=60.0)
    args = parser.parse_args()

    diagnostic_path = args.diagnostic or args.output.with_suffix(".diagnostic.json")
    messages = build_prompt(read_text(args.skill), read_text(args.case))
    diagnostic: dict[str, Any] = {
        "agent": "api_review_llm_agent",
        "skill": str(args.skill),
        "case": str(args.case),
        "output": str(args.output),
        "base_url_present": bool(args.base_url),
        "api_key_present": bool(args.api_key),
        "model": args.model,
        "status": "started",
    }
    if not args.base_url or not args.api_key or not args.model:
        diagnostic["status"] = "skipped"
        diagnostic["reason"] = "OPENAI_BASE_URL, OPENAI_API_KEY, and MODEL must be set or provided as arguments."
        write_json(diagnostic_path, diagnostic)
        print(json.dumps(diagnostic, ensure_ascii=False, indent=2))
        return 2
    try:
        response = call_chat_completions(
            base_url=args.base_url,
            api_key=args.api_key,
            model=args.model,
            messages=messages,
            temperature=args.temperature,
            timeout=args.timeout,
        )
        content = extract_message_content(response)
        review = parse_review_from_model_output(content)
        write_json(args.output, review)
        diagnostic.update(
            {
                "status": "ok",
                "finding_count": len(review["findings"]),
                "rule_ids": [finding["rule_id"] for finding in review["findings"]],
                "usage": response.get("usage"),
                "raw_content_preview": content[:500],
            }
        )
        write_json(diagnostic_path, diagnostic)
        print(json.dumps({"status": "ok", "output": str(args.output), "rule_ids": diagnostic["rule_ids"]}, ensure_ascii=False))
        return 0
    except (OSError, urllib.error.URLError, urllib.error.HTTPError, ValueError, json.JSONDecodeError) as exc:
        diagnostic.update({"status": "error", "error": str(exc)})
        write_json(diagnostic_path, diagnostic)
        print(json.dumps(diagnostic, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
