from __future__ import annotations

import json
import os
import shlex
from pathlib import Path

from harbor.agents.base import BaseAgent
from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext


class ControlledSecurityLLMAgent(BaseAgent):
    """Generic OpenAI-compatible non-oracle Harbor agent for controlled tasks."""

    @staticmethod
    def name() -> str:
        return "controlled-security-llm-agent"

    def __init__(
        self,
        logs_dir: Path,
        model_name: str | None = None,
        capabilities: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        task_label: str | None = None,
        relaxed_contract: str | None = None,
        prompt_addendum: str | None = None,
        **kwargs,
    ):
        super().__init__(logs_dir=logs_dir, model_name=model_name, **kwargs)
        self.capabilities = {
            item.strip()
            for item in (capabilities or "").split(",")
            if item.strip()
        }
        self.base_url = base_url or os.environ.get("OPENAI_BASE_URL")
        self.api_key = os.environ.get("OPENAI_API_KEY")
        self.model = model or model_name or os.environ.get("MODEL") or os.environ.get("OPENAI_MODEL")
        self.task_label = task_label or "controlled security review"
        self.relaxed_contract = str(relaxed_contract or "").lower() in {"1", "true", "yes", "on"}
        self.prompt_addendum = prompt_addendum or ""

    def version(self) -> str:
        return "0.1.0"

    async def setup(self, environment: BaseEnvironment) -> None:
        return

    async def run(
        self,
        instruction: str,
        environment: BaseEnvironment,
        context: AgentContext,
    ) -> None:
        marker = self.logs_dir / "CONTROLLED_SECURITY_LLM_AGENT_RAN.txt"
        marker.write_text(
            "ControlledSecurityLLMAgent ran inside Harbor non-oracle path.\n"
            f"Task label: {self.task_label}\n"
            f"Instruction preview: {instruction[:300]}\n"
            f"Capabilities: {sorted(self.capabilities)}\n"
            f"Relaxed contract: {self.relaxed_contract}\n"
            f"Prompt addendum present: {bool(self.prompt_addendum)}\n"
            f"Base URL present: {bool(self.base_url)}\n"
            f"API key present: {bool(self.api_key)}\n"
            f"Model: {self.model}\n",
            encoding="utf-8",
        )
        env = {
            "OPENAI_BASE_URL": self.base_url or "",
            "OPENAI_API_KEY": self.api_key or "",
            "MODEL": self.model or "",
            "CAPABILITIES": json.dumps(sorted(self.capabilities), ensure_ascii=False),
            "TASK_LABEL": self.task_label,
            "RELAXED_CONTRACT": "true" if self.relaxed_contract else "false",
            "PROMPT_ADDENDUM": self.prompt_addendum,
        }
        script = r'''
import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

def write(path, text):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(text)

def write_json(path, payload):
    write(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")

def read_tree(root):
    base = Path(root)
    if not base.exists():
        return {}
    return {
        str(path.relative_to(base)): path.read_text(errors="replace")
        for path in sorted(item for item in base.rglob("*") if item.is_file())
    }

def files_block(title, files):
    chunks = ["# " + title]
    for rel, text in files.items():
        chunks.append("\n## " + rel + "\n\n```text\n" + text[:12000] + "\n```")
    return "\n".join(chunks)

def extract_json(text):
    stripped = text.strip()
    match = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", stripped, flags=re.S | re.I)
    if match:
        stripped = match.group(1).strip()
    start = stripped.find("{")
    if start < 0:
        raise ValueError("no JSON object found")
    depth = 0
    in_string = False
    escaped = False
    for idx, ch in enumerate(stripped[start:], start):
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return stripped[start:idx + 1]
    raise ValueError("unbalanced JSON object")

def normalize(payload, allowed, relaxed_contract):
    findings = payload.get("findings")
    if not isinstance(findings, list):
        raise ValueError("findings must be a list")
    output = []
    for idx, item in enumerate(findings):
        if not isinstance(item, dict):
            raise ValueError(f"finding {idx} must be an object")
        capability_id = str(item.get("capability_id", "")).strip()
        if capability_id not in allowed:
            raise ValueError(f"finding {idx} capability not allowed: {capability_id}")
        evidence_span = str(item.get("evidence_span", "")).strip()
        if not evidence_span:
            raise ValueError(f"finding {idx} missing evidence_span")
        normalized = {
            "capability_id": capability_id,
            "evidence_span": evidence_span,
        }
        if "recommended_fix" in item:
            normalized["recommended_fix"] = str(item.get("recommended_fix", "")).strip()
        elif not relaxed_contract:
            raise ValueError(f"finding {idx} missing recommended_fix")
        if "issue" in item and str(item.get("issue", "")).strip():
            normalized["issue"] = str(item.get("issue", "")).strip()
        output.append(normalized)
    return {"backend_type": "controlled_security_llm_agent", "findings": output}

start = time.perf_counter()
Path("/artifacts").mkdir(parents=True, exist_ok=True)
target_files = read_tree("/app/target")
skill_files = read_tree("/app/skill")
allowed = set(json.loads(os.environ.get("CAPABILITIES", "[]")))
base_url = os.environ.get("OPENAI_BASE_URL")
api_key = os.environ.get("OPENAI_API_KEY")
model = os.environ.get("MODEL") or os.environ.get("OPENAI_MODEL")
task_label = os.environ.get("TASK_LABEL", "controlled security review")
relaxed_contract = os.environ.get("RELAXED_CONTRACT", "").lower() in {"1", "true", "yes", "on"}
prompt_addendum = os.environ.get("PROMPT_ADDENDUM", "").strip()

contract_note = (
    "Each finding must include capability_id and evidence_span. recommended_fix is optional in this exploratory v1 run."
    if relaxed_contract
    else "Each finding must include capability_id, evidence_span, and recommended_fix."
)
example = {
    "findings": [
        {
            "capability_id": sorted(allowed)[0] if allowed else "CAPABILITY_ID",
            "evidence_span": "concrete target-grounded evidence span",
        }
    ]
}
if not relaxed_contract:
    example["findings"][0]["recommended_fix"] = "concrete fix"

prompt = f"""You are a non-oracle {task_label} agent running in a Harbor container.

Read /app/target and /app/skill. Return only JSON for the deterministic verifier.

Rules:
- Use only these capability_id values from /app/skill: {', '.join(sorted(allowed))}
- {contract_note}
- Evidence must be grounded in /app/target files.
- Do not include markdown fences.
{prompt_addendum if prompt_addendum else ""}

Expected JSON:
{json.dumps(example, ensure_ascii=False, indent=2)}

{files_block("Skill Package", skill_files)}

{files_block("Target Asset", target_files)}
"""
write("/artifacts/prompt.md", prompt)
write_json("/artifacts/target_reads.json", {
    "read_files": ["/app/target/" + rel for rel in target_files],
    "skill_files": ["/app/skill/" + rel for rel in skill_files],
    "enabled_capabilities": sorted(allowed),
    "relaxed_contract": relaxed_contract,
})

metadata = {
    "backend_type": "controlled_security_llm_agent",
    "oracle": False,
    "llm": True,
    "task_label": task_label,
    "relaxed_contract": relaxed_contract,
    "base_url_present": bool(base_url),
    "api_key_present": bool(api_key),
    "model": model,
    "status": "started",
}

if not base_url or not api_key or not model:
    report = {"backend_type": "controlled_security_llm_agent", "findings": []}
    write_json("/app/security_report.json", report)
    write_json("/artifacts/security_report.json", report)
    metadata.update({"status": "skipped", "failure_reason": "env_missing"})
    write_json("/artifacts/backend_metadata.json", metadata)
    raise SystemExit(2)

try:
    request_payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Return strict JSON only for a deterministic verifier."},
            {"role": "user", "content": prompt},
        ],
        "stream": False,
        "temperature": 0.0,
    }
    req = urllib.request.Request(
        base_url.rstrip("/") + "/chat/completions",
        data=json.dumps(request_payload).encode("utf-8"),
        headers={"authorization": "Bearer " + api_key, "content-type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=90) as resp:
        response = json.loads(resp.read().decode("utf-8"))
    content = response["choices"][0]["message"]["content"]
    write("/artifacts/raw_response.txt", content)
    parsed = json.loads(extract_json(content))
    report = normalize(parsed, allowed, relaxed_contract)
    write_json("/app/security_report.json", report)
    write_json("/artifacts/security_report.json", report)
    metadata.update({
        "status": "ok",
        "finding_count": len(report["findings"]),
        "usage": response.get("usage"),
        "latency_ms": int((time.perf_counter() - start) * 1000),
    })
    write_json("/artifacts/backend_metadata.json", metadata)
    write_json("/artifacts/model_calls.json", {
        "status": "ok",
        "endpoint": base_url.rstrip("/") + "/chat/completions",
        "model": model,
        "usage": response.get("usage"),
        "response": response,
    })
except urllib.error.HTTPError as exc:
    body = exc.read().decode("utf-8", errors="replace")
    report = {"backend_type": "controlled_security_llm_agent", "findings": []}
    write_json("/app/security_report.json", report)
    write_json("/artifacts/security_report.json", report)
    write("/artifacts/raw_response.txt", body)
    metadata.update({"status": "error", "failure_reason": "api_error", "http_status": exc.code, "error": str(exc)})
    write_json("/artifacts/backend_metadata.json", metadata)
    raise
except Exception as exc:
    report = {"backend_type": "controlled_security_llm_agent", "findings": []}
    write_json("/app/security_report.json", report)
    write_json("/artifacts/security_report.json", report)
    metadata.update({"status": "error", "failure_reason": "network_or_parse_error", "error": str(exc)})
    write_json("/artifacts/backend_metadata.json", metadata)
    raise
'''
        result = await environment.exec(command="python3 -c " + shlex.quote(script), env=env, timeout_sec=120)
        (self.logs_dir / "stdout.log").write_text(str(getattr(result, "stdout", "")), encoding="utf-8")
        (self.logs_dir / "stderr.log").write_text(str(getattr(result, "stderr", "")), encoding="utf-8")
        (self.logs_dir / "return_code.txt").write_text(str(result.return_code), encoding="utf-8")
