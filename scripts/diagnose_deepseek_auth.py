from __future__ import annotations

import argparse
import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


def _metadata(name: str) -> dict[str, Any]:
    value = os.environ.get(name)
    if value is None:
        return {"name": name, "present": False}
    stripped = value.strip()
    return {
        "name": name,
        "present": True,
        "length": len(value),
        "prefix": value[:3],
        "suffix": value[-3:] if len(value) >= 3 else value,
        "starts_with_sk": value.startswith("sk-"),
        "leading_or_trailing_whitespace": value != stripped,
        "contains_newline": "\n" in value or "\r" in value,
        "contains_non_ascii": any(ord(char) > 127 for char in value),
    }


def diagnose(*, base_url: str, model: str, timeout: float, perform_request: bool) -> dict[str, Any]:
    deepseek = os.environ.get("DEEPSEEK_API_KEY")
    openai = os.environ.get("OPENAI_API_KEY")
    selected_name = "DEEPSEEK_API_KEY" if deepseek else None
    selected = deepseek
    endpoint = f"{base_url.rstrip('/')}/chat/completions"
    payload: dict[str, Any] = {
        "schema_version": "deepseek_auth_diagnosis.v1",
        "client_selection_order": ["DEEPSEEK_API_KEY"],
        "fallback_allowed": False,
        "variables": [_metadata("DEEPSEEK_API_KEY"), _metadata("OPENAI_API_KEY")],
        "selected_variable": selected_name,
        "base_url": base_url.rstrip("/"),
        "model": model,
        "endpoint_path": "/chat/completions",
        "endpoint": endpoint,
        "header_scheme": "Authorization: Bearer <redacted>",
        "request_attempted": False,
        "response_status": None,
        "sanitized_error_body": None,
    }
    if selected is None:
        payload["classification"] = "wrong_var" if openai else "env_missing"
        return payload
    meta = next(item for item in payload["variables"] if item["name"] == selected_name)
    malformed = (
        not meta["starts_with_sk"]
        or meta["leading_or_trailing_whitespace"]
        or meta["contains_newline"]
        or meta["contains_non_ascii"]
    )
    if not perform_request:
        payload["classification"] = "malformed_key" if malformed else "unknown_auth_failure"
        return payload
    request_payload = {
        "model": model,
        "messages": [{"role": "user", "content": "Return the single word OK."}],
        "max_tokens": 4,
        "temperature": 0,
    }
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(request_payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {selected}", "Content-Type": "application/json"},
        method="POST",
    )
    payload["request_attempted"] = True
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 - explicit diagnosis target
            payload["response_status"] = response.status
            response.read()
        payload["classification"] = "authenticated"
        return payload
    except urllib.error.HTTPError as exc:
        payload["response_status"] = exc.code
        body = exc.read().decode("utf-8", errors="replace")
        payload["sanitized_error_body"] = _sanitize(body, selected)
        if malformed:
            classification = "malformed_key"
        elif exc.code in {404, 405}:
            classification = "endpoint_mismatch"
        elif exc.code in {401, 403}:
            classification = "revoked_or_invalid_key"
        else:
            classification = "unknown_auth_failure"
        payload["classification"] = classification
        return payload
    except urllib.error.URLError as exc:
        payload["sanitized_error_body"] = _sanitize(str(exc.reason), selected)
        payload["classification"] = "unknown_auth_failure"
        return payload


def _sanitize(body: str, key: str) -> str:
    sanitized = body.replace(key, "<redacted>")
    sanitized = re.sub(r"(?i)bearer\s+[a-z0-9._-]+", "Bearer <redacted>", sanitized)
    sanitized = re.sub(r"sk-[A-Za-z0-9_-]{8,}", "sk-<redacted>", sanitized)
    return sanitized[:1000]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="https://api.deepseek.com")
    parser.add_argument("--model", default="deepseek-chat")
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--request", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args()
    result = diagnose(base_url=args.base_url, model=args.model, timeout=args.timeout, perform_request=args.request)
    serialized = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True)
    if args.output:
        Path(args.output).write_text(serialized + "\n", encoding="utf-8")
    print(serialized)
    return 0 if result["classification"] == "authenticated" else 2


if __name__ == "__main__":
    raise SystemExit(main())
