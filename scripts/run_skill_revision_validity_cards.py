from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from skill_deployment.validity import build_skill_revision_validity_cards, render_single_validity_card_markdown, render_skill_revision_validity_markdown


JSON_OUT = ROOT / "outputs" / "validation" / "skill_revision_validity_cards.json"
MD_OUT = ROOT / "reports" / "SKILL_REVISION_VALIDITY_CARD_STATUS.md"


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def main() -> int:
    payload = build_skill_revision_validity_cards(ROOT)
    write_json(JSON_OUT, payload)
    write_text(MD_OUT, render_skill_revision_validity_markdown(payload))
    per_loop_targets = {
        "harbor_llm_upload_repair_loop": ROOT / "outputs" / "harbor_llm_repair_loop_upload_001",
        "harbor_llm_config_repair_loop": ROOT / "outputs" / "harbor_llm_repair_loop_config_001",
    }
    for card in payload["cards"]:
        target_dir = per_loop_targets.get(card["card_id"])
        if target_dir is None:
            continue
        write_json(target_dir / "validity_card.json", card)
        write_text(target_dir / "validity_card.md", render_single_validity_card_markdown(card))
    print(json.dumps({"json": str(JSON_OUT), "report": str(MD_OUT), "card_count": payload["card_count"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
