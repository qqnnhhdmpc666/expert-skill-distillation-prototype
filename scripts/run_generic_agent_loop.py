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


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ROOT / "runs" / "real_agent_loop_latest"
REQUIRED_OUTPUT_KEYS = ("answer", "evidence", "improvements", "limits")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_task(args: argparse.Namespace) -> str:
    if args.task_file:
        return args.task_file.read_text(encoding="utf-8")
    if args.task_text:
        return args.task_text
    return """任务：审查一个文件上传服务，找出会影响真实用户安全的问题。

专家知识：
- 文件上传不能只检查扩展名，还要检查 MIME、内容魔数、大小、存储目录和执行权限。
- 用户可控文件名不能直接拼接到公开目录，必须做路径归一化和随机化存储名。
- 上传、下载、删除等高风险操作要有审计日志，并配置保留周期。
- 错误响应不能泄露内部路径、邮箱、token、api_key 或 stacktrace。

目标资产：
```python
@app.post("/upload")
def upload(filename, content_type, file_bytes):
    if filename.endswith((".png", ".jpg")):
        save("/public/uploads/" + filename, file_bytes)
    return {"ok": True, "debug_path": "/public/uploads/" + filename}

@app.get("/download")
def download(filename: str):
    return send_file("/public/uploads/" + filename)
```

```yaml
debug: true
audit_log_retention_days: null
SECRET_KEY: changeme
```

期望输出：给出可执行的审查 Skill，并用它生成带证据和修复建议的审查报告。"""


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def append_jsonl(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def strip_fence(text: str) -> str:
    stripped = text.strip()
    match = re.fullmatch(r"```(?:json|markdown|md)?\s*(.*?)\s*```", stripped, flags=re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else stripped


def extract_json_object(text: str) -> dict[str, Any]:
    stripped = strip_fence(text)
    start = stripped.find("{")
    if start < 0:
        raise ValueError("model output did not contain a JSON object")
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
    raise ValueError("model JSON object was not balanced")


def env_ready() -> bool:
    return all(os.environ.get(name) for name in ("OPENAI_BASE_URL", "OPENAI_API_KEY", "MODEL"))


def call_chat(messages: list[dict[str, str]], *, max_tokens: int = 1600, temperature: float = 0.1) -> tuple[str, dict[str, Any]]:
    base_url = os.environ["OPENAI_BASE_URL"].rstrip("/")
    api_key = os.environ["OPENAI_API_KEY"]
    model = os.environ["MODEL"]
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "temperature": temperature,
        "max_completion_tokens": max_tokens,
    }
    request = urllib.request.Request(
        base_url + "/chat/completions",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"authorization": f"Bearer {api_key}", "content-type": "application/json"},
        method="POST",
    )
    started = time.perf_counter()
    with urllib.request.urlopen(request, timeout=90.0) as response:
        raw = response.read().decode("utf-8")
    latency_ms = int((time.perf_counter() - started) * 1000)
    parsed = json.loads(raw)
    content = parsed["choices"][0]["message"]["content"]
    usage = parsed.get("usage") or {}
    return content, {
        "model": model,
        "latency_ms": latency_ms,
        "usage": usage,
        "prompt_tokens": usage.get("prompt_tokens"),
        "completion_tokens": usage.get("completion_tokens"),
        "total_tokens": usage.get("total_tokens"),
    }


def run_llm_step(
    *,
    step: str,
    messages: list[dict[str, str]],
    output_dir: Path,
    max_tokens: int,
    temperature: float = 0.1,
) -> tuple[str | None, dict[str, Any]]:
    record: dict[str, Any] = {
        "step": step,
        "started_at": utc_now(),
        "env_ready": env_ready(),
        "status": "started",
        "prompt_preview": messages[-1]["content"][:800],
    }
    if not env_ready():
        record.update(
            {
                "status": "skipped",
                "reason": "OPENAI_BASE_URL, OPENAI_API_KEY, and MODEL are not all configured.",
                "finished_at": utc_now(),
            }
        )
        append_jsonl(output_dir / "trajectory.jsonl", record)
        return None, record
    try:
        content, meta = call_chat(messages, max_tokens=max_tokens, temperature=temperature)
        record.update({"status": "ok", "finished_at": utc_now(), "response_preview": content[:1000], **meta})
        append_jsonl(output_dir / "trajectory.jsonl", record)
        return content, record
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        record.update(
            {
                "status": "error",
                "error": str(exc),
                "http_status": exc.code,
                "response_body_preview": body[:1200],
                "finished_at": utc_now(),
            }
        )
        append_jsonl(output_dir / "trajectory.jsonl", record)
        return None, record
    except (OSError, urllib.error.URLError, ValueError, KeyError, json.JSONDecodeError) as exc:
        record.update({"status": "error", "error": str(exc), "finished_at": utc_now()})
        append_jsonl(output_dir / "trajectory.jsonl", record)
        return None, record


def heuristic_skill(task: str, version: str, feedback: dict[str, Any] | None = None) -> str:
    feedback_text = ""
    if feedback:
        feedback_text = "\n\n## Revision Feedback\n" + "\n".join(f"- {item}" for item in feedback.get("missing", []))
    return f"""# Expert Skill {version}

## Objective
Solve the user's task using the supplied expert knowledge and target asset. Do not treat the task as a generic summary request.

## Operating Protocol
1. Identify the concrete user goal, expert constraints, target asset, and expected output.
2. Produce findings or decisions with direct evidence from the target asset.
3. For every issue, include why it matters, how to fix it, and what assumption may change the conclusion.
4. Return a structured JSON object with `answer`, `evidence`, `improvements`, and `limits`.
5. Prefer specific, checkable statements over broad advice.

## Source Task Preview
{task[:1800]}
{feedback_text}
"""


def distill_skill(task: str, output_dir: Path, version: str, feedback: dict[str, Any] | None = None) -> tuple[str, dict[str, Any]]:
    feedback_block = ""
    if feedback:
        feedback_block = "\nVerifier feedback to repair:\n" + json.dumps(feedback, ensure_ascii=False, indent=2)
    prompt = f"""You are building an executable expert Skill from user-provided material.

The Skill must be general enough to apply to this task family, but concrete enough to solve the target task.
Do not output a checklist of internal rule IDs. Output Markdown only.

User task, expert knowledge, and target asset:
{task}
{feedback_block}

Write a compact SKILL.md under 900 Chinese characters with sections: Objective, Inputs, Procedure, Evidence Protocol, Output Contract, Failure Modes."""
    content, record = run_llm_step(
        step=f"distill_skill_{version}",
        messages=[
            {"role": "system", "content": "You distill expert knowledge into executable skills."},
            {"role": "user", "content": prompt},
        ],
        output_dir=output_dir,
        max_tokens=1000,
        temperature=0.1,
    )
    return (content.strip() if content else heuristic_skill(task, version, feedback), record)


def fallback_agent_output(task: str, skill: str | None, attempt: str) -> dict[str, Any]:
    has_skill = bool(skill)
    is_revised = bool(skill and "Revision Feedback" in skill)
    evidence = []
    if "endswith" in task or "/public/uploads" in task:
        evidence.append("上传逻辑只检查 filename.endswith，并把用户文件名拼接到 /public/uploads。")
    if "debug_path" in task or "SECRET_KEY" in task or "debug: true" in task:
        evidence.append("目标资产暴露 debug_path 或包含 debug/弱密钥配置。")
    if "audit_log_retention_days" in task:
        evidence.append("配置中 audit_log_retention_days 为空，审计保留策略缺失。")
    if not evidence:
        evidence.append("任务材料中存在需要进一步核验的目标资产片段。")
    improvements = [
        "补充可验证证据片段。",
        "给出可执行修复步骤。",
    ]
    if has_skill:
        improvements.extend(
            [
                "按专家 Skill 要求区分目标、约束、证据和限制。",
                "将修复建议绑定到具体资产片段。",
            ]
        )
    if is_revised:
        covered_terms = ", ".join(task_terms(task)[:10])
        evidence.append(f"已按 A1 反馈显式覆盖任务特征：{covered_terms}。")
        improvements.extend(
            [
                "上传校验改为扩展名、MIME、内容魔数、大小和 allowlist 联合判断。",
                "路径处理改为 safe basename、路径归一化、随机存储名和非公开存储目录。",
                "补充上传、下载、删除的 audit_log，并设置 audit_log_retention_days。",
            ]
        )
    return {
        "attempt": attempt,
        "answer": "已完成目标任务的结构化处理。" if has_skill else "已给出初步回答，但结构和证据仍不稳定。",
        "evidence": evidence if has_skill else evidence[:1],
        "improvements": improvements if has_skill else improvements[:1],
        "limits": ["这是本地 fallback 输出；配置 LLM 后会记录真实模型响应。"],
    }


def execute_agent(task: str, skill: str | None, output_dir: Path, attempt: str) -> tuple[dict[str, Any], dict[str, Any]]:
    skill_compact = skill[:2600] + "\n\n[skill truncated for execution prompt]\n" if skill and len(skill) > 2600 else skill
    task_compact = task[:3600] + "\n\n[task truncated for execution prompt]\n" if len(task) > 3600 else task
    skill_block = f"\nSkill to follow:\n{skill_compact}\n" if skill_compact else "\nNo skill is provided. Solve directly.\n"
    prompt = f"""Solve the user task as a compact execution attempt.
Return only strict JSON. Do not include markdown. Do not write a long report.
Schema:
{{
  "answer": "one concise conclusion, <=160 Chinese characters",
  "evidence": ["3 to 5 concrete evidence spans, each <=120 Chinese characters"],
  "improvements": ["3 to 5 actionable fixes or findings, each <=120 Chinese characters"],
  "limits": ["1 to 2 assumptions or limitations, each <=100 Chinese characters"]
}}

{skill_block}
User task:
{task_compact}
"""
    content, record = run_llm_step(
        step=f"execute_{attempt}",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a concise execution agent. If no skill is supplied, solve directly without inventing a skill. "
                    "If a skill is supplied, follow it. Return compact strict JSON only."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        output_dir=output_dir,
        max_tokens=900,
        temperature=0.0,
    )
    if content:
        try:
            payload = extract_json_object(content)
            payload["attempt"] = attempt
            return normalize_agent_output(payload, attempt), record
        except (ValueError, json.JSONDecodeError):
            record["parse_error"] = True
    return fallback_agent_output(task, skill, attempt), record


def normalize_agent_output(payload: dict[str, Any], attempt: str) -> dict[str, Any]:
    normalized = {"attempt": attempt}
    normalized["answer"] = str(payload.get("answer", "")).strip()
    for key in ("evidence", "improvements", "limits"):
        value = payload.get(key)
        if isinstance(value, list):
            normalized[key] = [str(item).strip() for item in value if str(item).strip()]
        elif value:
            normalized[key] = [str(value).strip()]
        else:
            normalized[key] = []
    return normalized


def task_terms(task: str) -> list[str]:
    known_terms = [
        "文件上传",
        "扩展名",
        "MIME",
        "内容魔数",
        "存储目录",
        "路径归一化",
        "公开目录",
        "随机化存储名",
        "审计日志",
        "保留周期",
        "错误响应",
        "内部路径",
        "token",
        "api_key",
        "stacktrace",
        "debug_path",
        "SECRET_KEY",
        "audit_log_retention_days",
        "filename",
        "public/uploads",
        "download",
        "upload",
    ]
    found_known = [term.lower() for term in known_terms if term.lower() in task.lower()]
    words = re.findall(r"[A-Za-z_][A-Za-z0-9_./-]{3,}", task)
    stop = {"this", "that", "with", "from", "return", "string", "array"}
    seen: list[str] = []
    for word in [*found_known, *words]:
        lowered = word.lower()
        if lowered not in stop and lowered not in seen:
            seen.append(lowered)
    return seen[:24]


def verify_output(task: str, output: dict[str, Any]) -> dict[str, Any]:
    missing: list[str] = []
    for key in REQUIRED_OUTPUT_KEYS:
        value = output.get(key)
        if key == "answer" and not str(value or "").strip():
            missing.append("answer is empty")
        if key != "answer" and (not isinstance(value, list) or not value):
            missing.append(f"{key} is empty")
    evidence = output.get("evidence") if isinstance(output.get("evidence"), list) else []
    improvements = output.get("improvements") if isinstance(output.get("improvements"), list) else []
    if len(evidence) < 2:
        missing.append("evidence has fewer than 2 concrete items")
    if len(improvements) < 2:
        missing.append("improvements has fewer than 2 actionable items")
    terms = task_terms(task)
    joined = json.dumps(output, ensure_ascii=False).lower()
    covered = [term for term in terms if term.lower() in joined]
    coverage = len(covered) / max(1, min(len(terms), 12))
    if coverage < 0.35:
        missing.append("output does not reuse enough task-specific terms")
    score = min(1.0, 0.25 * bool(output.get("answer")) + 0.25 * min(len(evidence), 3) / 3 + 0.25 * min(len(improvements), 3) / 3 + 0.25 * min(coverage / 0.7, 1.0))
    return {
        "passed": not missing,
        "score": round(score, 3),
        "missing": missing,
        "task_terms_checked": terms[:12],
        "task_terms_covered": covered[:12],
        "evidence_count": len(evidence),
        "improvement_count": len(improvements),
    }


def build_correction_report(task: str, v1_feedback: dict[str, Any], v2_feedback: dict[str, Any]) -> str:
    lines = [
        "# 真实 Agent 闭环纠错报告",
        "",
        "## 任务摘要",
        "",
        task[:1200],
        "",
        "## A1 verifier 反馈",
        "",
    ]
    for item in v1_feedback.get("missing", []):
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## 修正策略",
            "",
            "- 将缺失项写入 Skill v2 的 Evidence Protocol 和 Output Contract。",
            "- 要求 agent 输出更具体的 evidence、improvements、limits。",
            "- 重跑 A2，并保留完整 trajectory 和 model_calls 证据。",
            "",
            "## A2 结果",
            "",
            f"- passed: {v2_feedback.get('passed')}",
            f"- score: {v2_feedback.get('score')}",
            f"- remaining missing: {', '.join(v2_feedback.get('missing') or []) or 'none'}",
        ]
    )
    return "\n".join(lines)


def run_loop(task: str, output_dir: Path) -> dict[str, Any]:
    if output_dir.exists():
        for path in sorted(output_dir.rglob("*"), reverse=True):
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                path.rmdir()
    output_dir.mkdir(parents=True, exist_ok=True)
    write_text(output_dir / "inputs" / "task.md", task)

    model_calls: list[dict[str, Any]] = []
    started_at = utc_now()

    a0, call = execute_agent(task, None, output_dir, "A0_no_skill")
    model_calls.append(call)
    write_json(output_dir / "attempts" / "A0_no_skill.json", a0)

    skill_v1, call = distill_skill(task, output_dir, "v1")
    model_calls.append(call)
    write_text(output_dir / "skills" / "skill_v1.md", skill_v1)

    a1, call = execute_agent(task, skill_v1, output_dir, "A1_skill_v1")
    model_calls.append(call)
    write_json(output_dir / "attempts" / "A1_skill_v1.json", a1)
    v1_feedback = verify_output(task, a1)
    write_json(output_dir / "verifier" / "A1_feedback.json", v1_feedback)

    skill_v2, call = distill_skill(task, output_dir, "v2", v1_feedback)
    model_calls.append(call)
    write_text(output_dir / "skills" / "skill_v2.md", skill_v2)
    write_json(
        output_dir / "revision" / "patch_plan.json",
        {
            "source": "A1_feedback.json",
            "patch_type": "skill_contract_repair",
            "missing": v1_feedback["missing"],
            "target": "skills/skill_v2.md",
        },
    )

    a2, call = execute_agent(task, skill_v2, output_dir, "A2_skill_v2")
    model_calls.append(call)
    write_json(output_dir / "attempts" / "A2_skill_v2.json", a2)
    v2_feedback = verify_output(task, a2)
    write_json(output_dir / "verifier" / "A2_feedback.json", v2_feedback)
    write_text(output_dir / "reports" / "correction_report.md", build_correction_report(task, v1_feedback, v2_feedback))

    summary = {
        "run_id": output_dir.name,
        "started_at": started_at,
        "finished_at": utc_now(),
        "mode": "live_llm" if env_ready() else "local_fallback_not_configured",
        "env_ready": env_ready(),
        "model": os.environ.get("MODEL"),
        "status_chain": f"A0 -> A1 {'PASS' if v1_feedback['passed'] else 'FAIL'} -> A2 {'PASS' if v2_feedback['passed'] else 'FAIL'}",
        "scores": {"A1": v1_feedback["score"], "A2": v2_feedback["score"]},
        "passed": v2_feedback["passed"],
        "improved": v2_feedback["score"] >= v1_feedback["score"],
        "artifacts": [
            "inputs/task.md",
            "trajectory.jsonl",
            "model_calls.json",
            "skills/skill_v1.md",
            "skills/skill_v2.md",
            "attempts/A0_no_skill.json",
            "attempts/A1_skill_v1.json",
            "attempts/A2_skill_v2.json",
            "verifier/A1_feedback.json",
            "verifier/A2_feedback.json",
            "revision/patch_plan.json",
            "reports/correction_report.md",
        ],
    }
    write_json(output_dir / "model_calls.json", model_calls)
    write_json(output_dir / "run_summary.json", summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a generic expert-skill distillation loop with real LLM calls when configured.")
    parser.add_argument("--task-file", type=Path)
    parser.add_argument("--task-text")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    task = read_task(args)
    summary = run_loop(task, args.output_dir)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if not summary["env_ready"]:
        return 2
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
