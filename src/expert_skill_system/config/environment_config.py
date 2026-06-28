from __future__ import annotations

from pathlib import Path
from typing import Any

from .system_config import load_json_config


def load_environment_config(path: Path | None = None) -> dict[str, Any]:
    root = Path(__file__).resolve().parents[3]
    payload = load_json_config(path or root / "configs" / "system_readiness_v0.json")
    if payload.get("schema_version") != "system_readiness_config.v0":
        raise ValueError("unsupported system readiness config schema")
    return payload
