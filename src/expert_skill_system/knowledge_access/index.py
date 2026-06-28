from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from expert_skill_system.core.canonical import sha256_bytes


@dataclass(frozen=True)
class KnowledgeIndexRow:
    knowledge_id: str
    source_id: str
    source_type: str
    content: str
    evidence_type: str
    visibility: str
    allowed_to_agent: bool
    digest: str
    metadata: dict[str, Any]

    @classmethod
    def create(
        cls,
        *,
        knowledge_id: str,
        source_id: str,
        source_type: str,
        content: str,
        evidence_type: str,
        visibility: str = "agent_visible",
        allowed_to_agent: bool = True,
        metadata: dict[str, Any] | None = None,
    ) -> KnowledgeIndexRow:
        return cls(
            knowledge_id=knowledge_id,
            source_id=source_id,
            source_type=source_type,
            content=content,
            evidence_type=evidence_type,
            visibility=visibility,
            allowed_to_agent=allowed_to_agent,
            digest=sha256_bytes(content.encode("utf-8")),
            metadata=metadata or {"path": None, "line_start": None, "line_end": None},
        )

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


def write_index(path: Path, rows: list[KnowledgeIndexRow]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(row.to_json(), ensure_ascii=False, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )


def read_index(path: Path) -> list[KnowledgeIndexRow]:
    rows: list[KnowledgeIndexRow] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        rows.append(KnowledgeIndexRow(**payload))
    return rows
