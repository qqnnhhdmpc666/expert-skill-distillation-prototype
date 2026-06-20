from __future__ import annotations

import json
import time
import urllib.request
from dataclasses import dataclass
from typing import Any, Protocol

from ..core.canonical import sha256_json
from .models import KnowledgeIR, SkillIR


@dataclass(frozen=True)
class JudgeResult:
    status: str
    findings: tuple[dict[str, Any], ...]
    provenance: dict[str, Any]


class IndependentJudge(Protocol):
    def evaluate(self, knowledge_ir: KnowledgeIR, skill_ir: SkillIR) -> JudgeResult: ...


class OpenAICompatibleJudge:
    """Blind source-grounding judge for OpenAI-compatible APIs, including DeepSeek's official API."""

    contract_version = "independent_source_grounding_judge.v1"

    def __init__(self, *, base_url: str, model: str, api_key: str, timeout_seconds: float = 90.0) -> None:
        if not base_url or not model or not api_key:
            raise ValueError("base_url, model and api_key are required")
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds
        self.last_blind_payload: dict[str, Any] | None = None

    def evaluate(self, knowledge_ir: KnowledgeIR, skill_ir: SkillIR) -> JudgeResult:
        blind_payload = {
            "contract_version": self.contract_version,
            "nodes": [
                {
                    "opaque_node_id": node.node_id,
                    "statement": node.statement,
                    "modality": node.modality,
                    "support_spans": list(node.quoted_support_spans),
                    "scope_claim": node.scope_claim,
                    "validation_status": node.validation_status,
                }
                for node in knowledge_ir.nodes
            ],
            "skill_ir": skill_ir.to_dict(),
            "checks": [
                "entailment",
                "unsupported_claim",
                "scope_overreach",
                "modality_mismatch",
                "missing_exception",
            ],
        }
        self.last_blind_payload = blind_payload
        prompt = (
            "You are an independent automated source-grounding judge, not a human expert. "
            "Review only the supplied support spans. Return strict JSON with keys status and findings. "
            "status must be pass or fail. Each finding must contain category, severity, opaque_node_id, and explanation. "
            "Use fail for any critical unsupported claim, scope overreach, modality reversal, or missing safety exception.\n"
            + json.dumps(blind_payload, ensure_ascii=False, sort_keys=True)
        )
        request_payload = {
            "model": self.model,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [{"role": "user", "content": prompt}],
        }
        started = time.perf_counter()
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(request_payload).encode("utf-8"),
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:  # noqa: S310 - explicit configured API
            raw = response.read()
        elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
        response_payload = json.loads(raw.decode("utf-8"))
        content = response_payload["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        status = parsed.get("status")
        findings = parsed.get("findings")
        if status not in {"pass", "fail"} or not isinstance(findings, list):
            raise ValueError("judge response violates independent_source_grounding_judge.v1")
        usage = response_payload.get("usage", {})
        return JudgeResult(
            status=status,
            findings=tuple(findings),
            provenance={
                "contract_version": self.contract_version,
                "provider_kind": "openai_compatible",
                "base_url": self.base_url,
                "model": self.model,
                "prompt_digest": sha256_json(prompt),
                "blind_input_digest": sha256_json(blind_payload),
                "raw_response_digest": sha256_json(response_payload),
                "elapsed_ms": elapsed_ms,
                "prompt_tokens": usage.get("prompt_tokens"),
                "completion_tokens": usage.get("completion_tokens"),
                "api_key_present": True,
            },
        )
