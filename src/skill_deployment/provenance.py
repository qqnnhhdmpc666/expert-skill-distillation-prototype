from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "skill_marginal_utility.v1"
VERIFIER_VERSION = "verify_controlled_execution.v1"


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_text_sha256(text: str) -> str:
    return _sha256_bytes(text.encode("utf-8"))


def hash_file_sha256(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def hash_json_payload_sha256(payload: Any) -> str:
    normalized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hash_text_sha256(normalized)


def hash_json_file_sha256(path: Path) -> str:
    return hash_json_payload_sha256(json.loads(path.read_text(encoding="utf-8-sig")))


def build_verifier_hash() -> str:
    return hash_text_sha256(VERIFIER_VERSION)
