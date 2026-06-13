from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from skill_deployment.qualification import build_skill_qualification_cards, render_skill_qualification_markdown


JSON_OUT = ROOT / "outputs" / "validation" / "skill_qualification_cards.json"
MD_OUT = ROOT / "reports" / "SKILL_QUALIFICATION_CARD_STATUS.md"


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def main() -> int:
    payload = build_skill_qualification_cards(ROOT)
    write_json(JSON_OUT, payload)
    write_text(MD_OUT, render_skill_qualification_markdown(payload))
    print(json.dumps({"json": str(JSON_OUT), "report": str(MD_OUT), "card_count": payload["card_count"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
