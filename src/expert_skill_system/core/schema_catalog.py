from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCHEMAS: dict[str, dict[str, Any]] = {
    "artifact_ref.v1": {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "artifact_ref.v1",
        "type": "object",
        "additionalProperties": False,
        "required": ["schema_version", "artifact_id", "digest", "media_type", "artifact_schema_version", "size_bytes"],
        "properties": {
            "schema_version": {"const": "artifact_ref.v1"},
            "artifact_id": {"type": "string", "minLength": 1},
            "digest": {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"},
            "media_type": {"type": "string", "minLength": 1},
            "artifact_schema_version": {"type": "string", "minLength": 1},
            "size_bytes": {"type": "integer", "minimum": 0},
        },
    },
    "active_binding.v1": {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "active_binding.v1",
        "type": "object",
        "additionalProperties": False,
        "required": ["schema_version", "binding_key", "bundle_digest", "generation", "updated_at"],
        "properties": {
            "schema_version": {"const": "active_binding.v1"},
            "binding_key": {"type": "string", "minLength": 1},
            "bundle_digest": {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"},
            "generation": {"type": "integer", "minimum": 1},
            "updated_at": {"type": "string", "minLength": 1},
        },
    },
    "execution_envelope.v1": {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "execution_envelope.v1",
        "type": "object",
        "additionalProperties": False,
        "required": ["schema_version", "execution_status", "domain_outcome", "failure", "session_id", "bundle_digest"],
        "properties": {
            "schema_version": {"const": "execution_envelope.v1"},
            "execution_status": {"enum": ["completed", "blocked", "runtime_failure"]},
            "domain_outcome": {"type": ["object", "null"]},
            "failure": {"type": ["object", "null"]},
            "session_id": {"type": "string", "minLength": 1},
            "bundle_digest": {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"},
        },
    },
    "compiler_stage_result.v1": {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "compiler_stage_result.v1",
        "type": "object",
        "additionalProperties": False,
        "required": [
            "schema_version",
            "build_id",
            "stage_id",
            "status",
            "input_refs",
            "output_refs",
            "issue_refs",
            "evidence_request_refs",
            "quarantined_item_refs",
            "model_call_refs",
            "deterministic_tool_refs",
            "metrics",
            "next_action",
        ],
        "properties": {
            "schema_version": {"const": "compiler_stage_result.v1"},
            "build_id": {"type": "string"},
            "stage_id": {"type": "string"},
            "status": {"enum": ["complete", "partial", "blocked", "rejected"]},
            "input_refs": {"type": "array", "items": {"type": "object"}},
            "output_refs": {"type": "array", "items": {"type": "object"}},
            "issue_refs": {"type": "array", "items": {"type": "object"}},
            "evidence_request_refs": {"type": "array", "items": {"type": "object"}},
            "quarantined_item_refs": {"type": "array", "items": {"type": "object"}},
            "model_call_refs": {"type": "array", "items": {"type": "object"}},
            "deterministic_tool_refs": {"type": "array", "items": {"type": "object"}},
            "metrics": {"type": "object"},
            "next_action": {"enum": ["continue", "acquire_evidence", "rebuild", "stop"]},
        },
    },
}


def export_schemas(output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for schema_id, payload in sorted(SCHEMAS.items()):
        path = output_dir / f"{schema_id}.schema.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        paths.append(path)
    return paths

