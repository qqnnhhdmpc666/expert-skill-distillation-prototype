from __future__ import annotations

from pathlib import Path
from typing import Any

from .system_config import load_json_config


def load_benchmark_config(path: Path | None = None) -> dict[str, Any]:
    root = Path(__file__).resolve().parents[3]
    payload = load_json_config(path or root / "configs" / "benchmark_lanes_v0.json")
    lanes = payload.get("benchmark_lanes")
    if not isinstance(lanes, dict) or not lanes:
        raise ValueError("benchmark config must contain non-empty benchmark_lanes")
    return payload
