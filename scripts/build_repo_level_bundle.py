from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from expert_skill_system.compiler.repo_level_bundle_builder import (  # noqa: E402
    REPO_LEVEL_SKILL_ID,
    RepoLevelBundleBuilder,
)
from expert_skill_system.registry.workspace import Workspace  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build and optionally promote the repo-level dependency-use triage ReleaseBundle.")
    parser.add_argument("--state-dir", required=True)
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--skill-family", default=REPO_LEVEL_SKILL_ID)
    parser.add_argument("--promote", action="store_true")
    args = parser.parse_args(argv)
    workspace = Workspace.open(Path(args.state_dir))
    result = RepoLevelBundleBuilder(workspace).build(
        data_dir=Path(args.data_dir),
        skill_family=args.skill_family,
        promote=args.promote,
    )
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result.status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
