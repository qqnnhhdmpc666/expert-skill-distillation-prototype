from __future__ import annotations

import argparse
import json
import urllib.request
from pathlib import Path
from typing import Any

from skill_deployment import MaterialSource, distill_material_skill_bundle


ROOT = Path(__file__).resolve().parents[1]


def fetch_text(url: str, timeout_seconds: int = 30) -> str:
    with urllib.request.urlopen(url, timeout=timeout_seconds) as response:
        return response.read().decode("utf-8")


def load_material_text(entry: dict[str, Any], *, base_dir: Path) -> tuple[str, str]:
    inline_text = str(entry.get("material_text") or "").strip()
    if inline_text:
        return inline_text, "inline_text"

    source_path = str(entry.get("source_path") or "").strip()
    if source_path:
        path = Path(source_path)
        if not path.is_absolute():
            path = (base_dir / path).resolve()
        return path.read_text(encoding="utf-8"), str(path)

    source_url = str(entry.get("source_url") or "").strip()
    if source_url:
        return fetch_text(source_url), source_url

    raise ValueError("each material entry must provide one of material_text, source_path, or source_url")


def load_material_sources(materials_path: Path) -> list[MaterialSource]:
    payload = json.loads(materials_path.read_text(encoding="utf-8"))
    raw_items = payload["materials"] if isinstance(payload, dict) else payload
    if not isinstance(raw_items, list) or not raw_items:
        raise ValueError("materials file must be a non-empty list or an object with a non-empty `materials` list")

    base_dir = materials_path.parent
    materials: list[MaterialSource] = []
    for index, raw_item in enumerate(raw_items, start=1):
        if not isinstance(raw_item, dict):
            raise ValueError(f"material item #{index} must be an object")
        source_id = str(raw_item.get("source_id") or "").strip()
        task_family = str(raw_item.get("task_family") or "").strip()
        title = str(raw_item.get("title") or "").strip()
        if not source_id or not task_family or not title:
            raise ValueError(f"material item #{index} must include source_id, task_family, and title")
        material_text, resolved_source = load_material_text(raw_item, base_dir=base_dir)
        metadata = dict(raw_item.get("metadata") or {})
        metadata.setdefault("resolved_source", resolved_source)
        materials.append(
            MaterialSource(
                source_id=source_id,
                task_family=task_family,
                title=title,
                material_text=material_text,
                source_url=str(raw_item.get("source_url") or "") or None,
                source_path=str(raw_item.get("source_path") or "") or None,
                metadata=metadata,
            )
        )
    return materials


def main() -> int:
    parser = argparse.ArgumentParser(description="Distill user/public materials into an installable Skill package.")
    parser.add_argument("--materials", required=True, help="Path to a JSON file describing material sources.")
    parser.add_argument("--skill-id", required=True)
    parser.add_argument("--version", default="v1")
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--title", default=None)
    args = parser.parse_args()

    materials_path = Path(args.materials)
    if not materials_path.is_absolute():
        materials_path = (ROOT / materials_path).resolve()
    output_dir = Path(args.output_dir).resolve() if args.output_dir else ROOT / "outputs" / "distilled_open_materials" / args.skill_id

    materials = load_material_sources(materials_path)
    summary = distill_material_skill_bundle(
        skill_id=args.skill_id,
        version=args.version,
        materials=materials,
        output_dir=output_dir,
        title=args.title,
        distillation_method="keyword_projection_from_user_or_public_materials",
        package_role="user_material_distilled_runtime",
    )
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
