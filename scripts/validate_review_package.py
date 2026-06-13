from __future__ import annotations

import json
import re
import zipfile
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "review_package"
ZIP_PATH = ROOT / "review_package.zip"
SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"OPENAI_API_KEY\s*[:=]\s*['\"]sk-[A-Za-z0-9]{20,}['\"]", re.I),
    re.compile(r"RIGHTCODE.*sk-[A-Za-z0-9]{20,}", re.I),
]


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        for key, value in attrs:
            if key == "href" and value:
                self.links.append(value)


def scan_secrets(path: Path) -> list[str]:
    hits = []
    for file_path in path.rglob("*"):
        if not file_path.is_file() or file_path.suffix.lower() in {".png", ".jpg", ".jpeg", ".zip"}:
            continue
        try:
            text = file_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                hits.append(str(file_path.relative_to(path)))
                break
    return hits


def validate_json_references(root: Path, filename: str) -> list[str]:
    missing = []
    for file_path in root.rglob(filename):
        try:
            payload = json.loads(file_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            missing.append(f"{file_path.relative_to(root)} invalid json")
            continue
        rows = payload if isinstance(payload, list) else payload.get("artifacts", []) if isinstance(payload, dict) else []
        if not isinstance(rows, list):
            continue
        for row in rows:
            rel = None
            if isinstance(row, str):
                rel = row
            elif isinstance(row, dict):
                rel = row.get("rule_file") or row.get("destination") or row.get("path")
            if rel and "*" not in rel and not rel.endswith("/"):
                candidate = file_path.parent / rel
                if not candidate.exists() and not (root / rel).exists():
                    missing.append(f"{file_path.relative_to(root)} -> {rel}")
    return missing


def main() -> int:
    errors: list[str] = []
    for rel in ("index.html", "README_DEMO.md"):
        if not (PACKAGE / rel).exists():
            errors.append(f"missing {rel}")
    screenshots = PACKAGE / "screenshots"
    if not screenshots.exists() or not any(screenshots.glob("*.png")):
        errors.append("missing screenshots/*.png")
    index = PACKAGE / "index.html"
    if index.exists():
        parser = LinkParser()
        parser.feed(index.read_text(encoding="utf-8", errors="ignore"))
        for href in parser.links:
            if href.startswith(("http://", "https://", "#")):
                continue
            if not (PACKAGE / href).exists():
                errors.append(f"broken index link: {href}")
    if not ZIP_PATH.exists():
        errors.append("missing review_package.zip")
    else:
        with zipfile.ZipFile(ZIP_PATH) as zf:
            for name in zf.namelist():
                if "\\" in name:
                    errors.append(f"zip path uses backslash: {name}")
    errors.extend(f"secret-like token in {hit}" for hit in scan_secrets(PACKAGE))
    errors.extend(f"missing mapping reference {item}" for item in validate_json_references(PACKAGE, "source_to_skill_mapping.json"))
    errors.extend(f"missing manifest reference {item}" for item in validate_json_references(PACKAGE, "file_manifest.json"))
    payload = {"status": "ok" if not errors else "failed", "error_count": len(errors), "errors": errors}
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
