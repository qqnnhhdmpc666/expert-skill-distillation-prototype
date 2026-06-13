from __future__ import annotations

import argparse
import json
import os
import re
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def append_jsonl(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


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


def normalize_action(payload: dict[str, Any]) -> dict[str, Any]:
    action = str(payload.get("action") or "").strip()
    note = str(payload.get("note") or "").strip()
    result = {"action": action, "note": note}
    if action == "read_file":
        result["path"] = str(payload.get("path") or "").strip()
    elif action == "finish":
        result["findings"] = payload.get("findings", [])
        result["summary"] = str(payload.get("summary") or "").strip()
    return result


def normalize_findings(domain: str, findings: Any) -> list[dict[str, str]]:
    required = ["rule_id", "issue", "severity", "evidence"]
    if domain == "config_security":
        required.append("config_path")
    normalized: list[dict[str, str]] = []
    if not isinstance(findings, list):
        return normalized
    for item in findings:
        if not isinstance(item, dict):
            continue
        normalized_item = {field: str(item.get(field) or "").strip() for field in required}
        if normalized_item["rule_id"]:
            normalized.append(normalized_item)
    return normalized


def call_chat(
    *,
    base_url: str,
    api_key: str,
    model: str,
    messages: list[dict[str, str]],
    temperature: float,
    timeout: float,
) -> tuple[str, dict[str, Any]]:
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "temperature": temperature,
        "max_tokens": 900,
    }
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
    return content, {"usage": parsed.get("usage"), "latency_ms": latency_ms, "response": parsed}


def render_skill_block(skill_text: str) -> str:
    compact = skill_text[:12000]
    return f"## Skill\n\n```text\n{compact}\n```"


def render_visible_files(case_root: Path) -> str:
    chunks = ["## Visible Case Files"]
    for path in sorted(item for item in case_root.iterdir() if item.is_file()):
        chunks.append(f"\n### {path.name}\n\n```text\n{read_text(path)[:8000]}\n```")
    return "\n".join(chunks)


def build_messages(*, domain: str, case_root: Path, skill_text: str, allowed_rule_ids: list[str]) -> list[dict[str, str]]:
    required = [
        {"rule_id": allowed_rule_ids[0] if allowed_rule_ids else "R001", "issue": "short issue", "severity": "high", "evidence": "exact visible text"}
    ]
    if domain == "config_security":
        required[0]["config_path"] = "config field path"
    action_schema = {
        "action": "list_files | read_file | finish",
        "note": "short action reason under 80 chars",
        "path": "relative file path for read_file only",
        "findings": required,
        "summary": "short final summary for finish only",
    }
    prompt = "\n\n".join(
        [
            "You are a cautious tool-using review agent.",
            "Use only visible case files. Never assume hidden labels or verifier data.",
            f"Allowed rule ids: {', '.join(allowed_rule_ids) if allowed_rule_ids else '(none)'}",
            "You may use these actions:",
            "- list_files: inspect which visible files exist",
            "- read_file: read one visible file",
            "- finish: return final findings",
            "Return one JSON action object only. No markdown fences. No extra commentary.",
            "If the case is clean, finish with findings=[].",
            render_skill_block(skill_text),
            render_visible_files(case_root),
            "Finish findings must follow this schema:",
            json.dumps(action_schema, ensure_ascii=False, indent=2),
        ]
    )
    return [
        {"role": "system", "content": f"You are a defensive {domain} review agent that acts through JSON tool calls."},
        {"role": "user", "content": prompt},
    ]


def tool_list_files(case_root: Path) -> list[str]:
    return [path.name for path in sorted(item for item in case_root.iterdir() if item.is_file())]


def tool_read_file(case_root: Path, relative_path: str) -> dict[str, Any]:
    path = (case_root / relative_path).resolve()
    if case_root.resolve() not in path.parents and path != case_root.resolve():
        return {"status": "error", "reason": "path_outside_case_root"}
    if not path.exists() or not path.is_file():
        return {"status": "error", "reason": "missing_file", "path": relative_path}
    return {"status": "ok", "path": relative_path, "content": read_text(path)}


def run_agent(
    *,
    domain: str,
    case_root: Path,
    skill_path: Path,
    out_dir: Path,
    allowed_rule_ids: list[str],
    base_url: str,
    api_key: str,
    model: str,
    timeout_seconds: float,
    max_steps: int,
) -> dict[str, Any]:
    skill_text = read_text(skill_path)
    messages = build_messages(domain=domain, case_root=case_root, skill_text=skill_text, allowed_rule_ids=allowed_rule_ids)
    reviewed_files: list[str] = []
    final_review = {"findings": [], "summary": "", "status": "incomplete"}
    model_calls: list[dict[str, Any]] = []
    append_jsonl(out_dir / "trajectory.jsonl", {"event": "start", "timestamp": utc_now(), "domain": domain, "model": model})

    for step_index in range(1, max_steps + 1):
        try:
            content, meta = call_chat(
                base_url=base_url,
                api_key=api_key,
                model=model,
                messages=messages,
                temperature=0.0,
                timeout=timeout_seconds,
            )
            write_text(out_dir / f"raw_step_{step_index}.txt", content)
            try:
                action = normalize_action(extract_first_json_object(content))
            except (ValueError, json.JSONDecodeError) as exc:
                append_jsonl(
                    out_dir / "trajectory.jsonl",
                    {
                        "event": "parse_repair",
                        "step_index": step_index,
                        "timestamp": utc_now(),
                        "error": str(exc),
                        "raw_preview": content[:600],
                    },
                )
                messages.append({"role": "assistant", "content": content[:2000]})
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            "Protocol repair: your previous reply was not a valid JSON action object. "
                            "Reply again with exactly one JSON object using only list_files, read_file, or finish."
                        ),
                    }
                )
                continue
            model_calls.append({"step_index": step_index, "raw_preview": content[:1000], "usage": meta.get("usage"), "latency_ms": meta.get("latency_ms")})
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            append_jsonl(
                out_dir / "trajectory.jsonl",
                {"event": "http_error", "step_index": step_index, "timestamp": utc_now(), "code": exc.code, "body_preview": body[:1200]},
            )
            final_review = {"findings": [], "summary": "api_blocked", "status": "blocked_http_error"}
            break
        except (OSError, urllib.error.URLError, KeyError, json.JSONDecodeError) as exc:
            append_jsonl(
                out_dir / "trajectory.jsonl",
                {"event": "model_error", "step_index": step_index, "timestamp": utc_now(), "error": str(exc)},
            )
            final_review = {"findings": [], "summary": "api_blocked", "status": f"blocked:{type(exc).__name__}"}
            break

        append_jsonl(
            out_dir / "trajectory.jsonl",
            {"event": "model_action", "step_index": step_index, "timestamp": utc_now(), "action": action},
        )

        if action["action"] == "list_files":
            files = tool_list_files(case_root)
            messages.append({"role": "assistant", "content": json.dumps(action, ensure_ascii=False)})
            messages.append({"role": "user", "content": f"Tool result: visible files = {json.dumps(files, ensure_ascii=False)}"})
            append_jsonl(out_dir / "trajectory.jsonl", {"event": "tool_result", "step_index": step_index, "tool": "list_files", "files": files})
            continue

        if action["action"] == "read_file":
            path = str(action.get("path") or "")
            result = tool_read_file(case_root, path)
            if result.get("status") == "ok":
                reviewed_files.append(path)
            messages.append({"role": "assistant", "content": json.dumps(action, ensure_ascii=False)})
            messages.append({"role": "user", "content": f"Tool result: {json.dumps(result, ensure_ascii=False)}"})
            append_jsonl(out_dir / "trajectory.jsonl", {"event": "tool_result", "step_index": step_index, "tool": "read_file", "result": result})
            continue

        if action["action"] == "finish":
            final_review = {
                "findings": normalize_findings(domain, action.get("findings")),
                "summary": str(action.get("summary") or ""),
                "status": "completed",
            }
            break

        messages.append({"role": "assistant", "content": json.dumps(action, ensure_ascii=False)})
        messages.append({"role": "user", "content": "Tool error: unknown action. Use list_files, read_file, or finish only."})

    write_json(out_dir / "review.json", final_review)
    write_json(
        out_dir / "agent_metadata.json",
        {
            "generated_at": utc_now(),
            "domain": domain,
            "case_root": str(case_root),
            "skill_path": str(skill_path),
            "allowed_rule_ids": allowed_rule_ids,
            "reviewed_files": reviewed_files,
            "model": model,
            "base_url_present": bool(base_url),
            "api_key_present": bool(api_key),
            "status": final_review["status"],
        },
    )
    write_json(out_dir / "model_calls.json", model_calls)
    return final_review


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a small live tool-using review agent on one visible case workspace.")
    parser.add_argument("--domain", required=True, choices=["api_review", "config_security"])
    parser.add_argument("--case-root", required=True)
    parser.add_argument("--skill", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--allowed-rule-ids", default="")
    parser.add_argument("--base-url", default=os.environ.get("OPENAI_BASE_URL") or "https://api.deepseek.com")
    parser.add_argument("--api-key", default=os.environ.get("OPENAI_API_KEY") or "")
    parser.add_argument("--model", default=os.environ.get("MODEL") or os.environ.get("OPENAI_MODEL") or "deepseek-v4-flash")
    parser.add_argument("--timeout-seconds", type=float, default=60.0)
    parser.add_argument("--max-steps", type=int, default=4)
    args = parser.parse_args(argv)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    if not args.api_key:
        write_json(out_dir / "review.json", {"findings": [], "summary": "missing_api_key", "status": "blocked_missing_api_key"})
        write_json(
            out_dir / "agent_metadata.json",
            {
                "generated_at": utc_now(),
                "status": "blocked_missing_api_key",
                "api_key_present": False,
                "base_url_present": bool(args.base_url),
                "model": args.model,
            },
        )
        return 2

    run_agent(
        domain=args.domain,
        case_root=Path(args.case_root),
        skill_path=Path(args.skill),
        out_dir=out_dir,
        allowed_rule_ids=[item.strip() for item in args.allowed_rule_ids.split(",") if item.strip()],
        base_url=args.base_url,
        api_key=args.api_key,
        model=args.model,
        timeout_seconds=args.timeout_seconds,
        max_steps=args.max_steps,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
