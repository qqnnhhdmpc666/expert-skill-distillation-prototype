from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class SkillFamilySpec:
    skill_family: str
    family_type: str
    builder_entrypoint: str
    default_state_dir: str
    default_eval: str
    binding_key: str
    claim_scope: tuple[str, ...]
    blocked_claims: tuple[str, ...]
    data_dir: str | None = None
    task_registry: str | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> SkillFamilySpec:
        required = {
            "skill_family",
            "family_type",
            "builder_entrypoint",
            "default_state_dir",
            "default_eval",
            "binding_key",
            "claim_scope",
            "blocked_claims",
        }
        missing = sorted(required - set(payload))
        if missing:
            raise ValueError(f"skill family spec missing required fields: {missing}")
        return cls(
            skill_family=str(payload["skill_family"]),
            family_type=str(payload["family_type"]),
            builder_entrypoint=str(payload["builder_entrypoint"]),
            default_state_dir=str(payload["default_state_dir"]),
            default_eval=str(payload["default_eval"]),
            binding_key=str(payload["binding_key"]),
            claim_scope=tuple(str(item) for item in payload["claim_scope"]),
            blocked_claims=tuple(str(item) for item in payload["blocked_claims"]),
            data_dir=str(payload["data_dir"]) if payload.get("data_dir") else None,
            task_registry=str(payload["task_registry"]) if payload.get("task_registry") else None,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "skill_family": self.skill_family,
            "family_type": self.family_type,
            "builder_entrypoint": self.builder_entrypoint,
            "default_state_dir": self.default_state_dir,
            "default_eval": self.default_eval,
            "data_dir": self.data_dir,
            "task_registry": self.task_registry,
            "binding_key": self.binding_key,
            "claim_scope": list(self.claim_scope),
            "blocked_claims": list(self.blocked_claims),
        }


@dataclass(frozen=True)
class SkillFamilyRegistry:
    schema_version: str
    registry_id: str
    families: tuple[SkillFamilySpec, ...]
    global_blocked_claims: tuple[str, ...]
    path: Path

    def by_family(self, requested: list[str] | tuple[str, ...]) -> tuple[SkillFamilySpec, ...]:
        by_name = {item.skill_family: item for item in self.families}
        missing = [item for item in requested if item not in by_name]
        if missing:
            raise ValueError(f"unknown skill families: {missing}")
        return tuple(by_name[item] for item in requested)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "registry_id": self.registry_id,
            "families": [item.to_dict() for item in self.families],
            "global_blocked_claims": list(self.global_blocked_claims),
            "path": str(self.path),
        }


def load_skill_family_registry(path: Path) -> SkillFamilyRegistry:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "skill_family_registry.v1":
        raise ValueError("expected schema_version skill_family_registry.v1")
    families = tuple(SkillFamilySpec.from_dict(item) for item in payload.get("families", []))
    names = [item.skill_family for item in families]
    if len(names) != len(set(names)):
        raise ValueError("duplicate skill_family entries in registry")
    if not families:
        raise ValueError("skill family registry must contain at least one family")
    return SkillFamilyRegistry(
        schema_version=payload["schema_version"],
        registry_id=str(payload.get("registry_id", "skill_family_registry")),
        families=families,
        global_blocked_claims=tuple(str(item) for item in payload.get("global_blocked_claims", [])),
        path=path,
    )
