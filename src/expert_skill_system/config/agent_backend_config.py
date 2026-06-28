from __future__ import annotations

from pathlib import Path
from typing import Any

from .system_config import load_json_config


def load_agent_backend_config(path: Path | None = None) -> dict[str, Any]:
    root = Path(__file__).resolve().parents[3]
    payload = load_json_config(path or root / "configs" / "agent_backends_v0.json")
    backends = payload.get("agent_backends")
    if not isinstance(backends, dict) or not backends:
        raise ValueError("agent backend config must contain non-empty agent_backends")
    for backend_id, spec in backends.items():
        if "enabled" not in spec or "type" not in spec:
            raise ValueError(f"agent backend {backend_id!r} is missing enabled/type")
        if backend_id == "mini_swe_agent_real_llm" and spec.get("enabled") is not False:
            raise ValueError("mini_swe_agent_real_llm must default to disabled in v0")
    return payload
