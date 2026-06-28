from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_json_config(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"config must be a JSON object: {path}")
    return payload


def load_system_config(path: Path | None = None) -> dict[str, Any]:
    root = Path(__file__).resolve().parents[3]
    return load_json_config(path or root / "configs" / "system_readiness_v0.json")
