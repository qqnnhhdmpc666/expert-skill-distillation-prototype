from __future__ import annotations

import json
import re
import time
import urllib.request
from typing import Any


def strip_markdown_fence(text: str) -> str:
    stripped = text.strip()
    match = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", stripped, flags=re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else stripped


def extract_first_json_object(text: str) -> dict[str, Any]:
    stripped = strip_markdown_fence(text)
    start = stripped.find("{")
    if start < 0:
        raise ValueError("No JSON object start found in model output.")
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
    raise ValueError("Model output did not contain a balanced JSON object.")


def call_chat_completion(
    *,
    base_url: str,
    api_key: str,
    model: str,
    messages: list[dict[str, str]],
    temperature: float = 0.0,
    max_tokens: int = 1600,
    timeout: float = 60.0,
    json_mode: bool = True,
) -> tuple[str, dict[str, Any]]:
    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "stream": False,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    request = urllib.request.Request(
        base_url.rstrip("/") + "/chat/completions",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"authorization": f"Bearer {api_key}", "content-type": "application/json"},
        method="POST",
    )
    started = time.perf_counter()
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read().decode("utf-8")
    latency_ms = int((time.perf_counter() - started) * 1000)
    parsed = json.loads(raw)
    content = parsed["choices"][0]["message"]["content"]
    metadata = {
        "usage": parsed.get("usage"),
        "latency_ms": latency_ms,
        "model": parsed.get("model") or model,
    }
    return content, metadata


def call_chat_completion_json(
    *,
    base_url: str,
    api_key: str,
    model: str,
    messages: list[dict[str, str]],
    temperature: float = 0.0,
    max_tokens: int = 1600,
    timeout: float = 60.0,
) -> tuple[dict[str, Any], dict[str, Any]]:
    content, metadata = call_chat_completion(
        base_url=base_url,
        api_key=api_key,
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
        json_mode=True,
    )
    parsed = extract_first_json_object(content)
    return parsed, {**metadata, "raw_content": content}
