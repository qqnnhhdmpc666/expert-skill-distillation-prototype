from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from skill_deployment import rollback_installed_skill  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Rollback an installed Skill package to a previous version.")
    parser.add_argument("--installed", required=True)
    parser.add_argument("--to-version", required=True)
    args = parser.parse_args(argv)
    result = rollback_installed_skill(ROOT, args.installed, args.to_version)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
