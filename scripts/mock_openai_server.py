"""Tiny OpenAI-compatible mock server for local pipeline smoke tests.

It implements just enough of `/v1/chat/completions` for litellm/openai-style
clients to receive a deterministic assistant response. Do not use it for real
evaluation; it is only for dependency and pipeline wiring checks.
"""

from __future__ import annotations

import argparse
import json
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


MOCK_SKILL = """# Smoke Skill

## Purpose

Solve the local Harbor smoke task by creating `/app/answer.txt`.

## Procedure

1. Write exactly `spark-ok` into `/app/answer.txt`.
2. Do not add extra whitespace or extra lines if the verifier requires exact text.

## Verification

The verifier passes when `/app/answer.txt` exists and its content is exactly `spark-ok`.
"""


class Handler(BaseHTTPRequestHandler):
    server_version = "MockOpenAI/0.1"

    def do_GET(self) -> None:  # noqa: N802
        if self.path.rstrip("/") in {"", "/v1", "/v1/models"}:
            self._send_json({"object": "list", "data": [{"id": "mock-model", "object": "model"}]})
            return
        self._send_json({"error": {"message": "not found"}}, status=404)

    def do_POST(self) -> None:  # noqa: N802
        if self.path.rstrip("/") != "/v1/chat/completions":
            self._send_json({"error": {"message": "not found"}}, status=404)
            return

        length = int(self.headers.get("content-length", "0") or "0")
        if length:
            self.rfile.read(length)

        response = {
            "id": "chatcmpl-mock",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": "mock-model",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": MOCK_SKILL},
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 80,
                "total_tokens": 180,
            },
        }
        self._send_json(response)

    def log_message(self, format: str, *args: object) -> None:
        return

    def _send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a minimal mock OpenAI-compatible server.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8099)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"mock OpenAI server listening on http://{args.host}:{args.port}/v1", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
