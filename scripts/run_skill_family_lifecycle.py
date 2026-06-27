from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from expert_skill_system.lifecycle import run_skill_family_lifecycle  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run unified multi-skill-family lifecycle orchestration.")
    parser.add_argument("--family-registry", required=True)
    parser.add_argument("--families", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    families = [item.strip() for item in args.families.split(",") if item.strip()]
    result = run_skill_family_lifecycle(
        family_registry=Path(args.family_registry),
        families=families,
        output_dir=Path(args.output),
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["multi_skill_family_lifecycle"] in {"pass", "partial"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
