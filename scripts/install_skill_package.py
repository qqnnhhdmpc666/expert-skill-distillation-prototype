from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from skill_deployment import install_skill_package  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Install a deployable Skill package into the runtime registry.")
    parser.add_argument("--skill", required=True)
    parser.add_argument("--version", default=None)
    args = parser.parse_args(argv)
    result = install_skill_package(ROOT, Path(args.skill), requested_version=args.version)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
