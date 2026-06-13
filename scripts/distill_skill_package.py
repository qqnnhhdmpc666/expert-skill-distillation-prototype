from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from skill_deployment import distill_skill_bundle, select_controlled_task_cases  # noqa: E402


DATA_ROOT = ROOT / "data" / "task_cases"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Distill controlled expert materials into an installable Skill package.")
    parser.add_argument("--cases", required=True, help="Comma-separated controlled task case ids or aliases.")
    parser.add_argument("--skill-id", required=True)
    parser.add_argument("--version", default="v1")
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--title", default=None)
    parser.add_argument("--case-root", default=str(DATA_ROOT))
    args = parser.parse_args(argv)

    case_root = Path(args.case_root)
    cases = select_controlled_task_cases(case_root, args.cases, include_negative_controls=False)
    output_dir = Path(args.output_dir) if args.output_dir else ROOT / "outputs" / "distilled_skills" / args.skill_id
    summary = distill_skill_bundle(
        skill_id=args.skill_id,
        version=args.version,
        cases=cases,
        output_dir=output_dir,
        title=args.title,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
