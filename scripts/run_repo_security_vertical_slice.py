from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from expert_skill_system.evaluation.repo_security_task import run_dependency_use_triage  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the local repo-level security vertical slice.")
    parser.add_argument("--task", required=True, help="Task directory or directory containing task subdirectories.")
    parser.add_argument("--output", required=True, help="Output directory.")
    args = parser.parse_args(argv)

    task_path = Path(args.task)
    output_root = Path(args.output)
    if (task_path / "task.json").exists():
        results = [run_dependency_use_triage(task_path, output_root)]
    else:
        results = []
        for task_dir in sorted(path for path in task_path.iterdir() if (path / "task.json").exists()):
            results.append(run_dependency_use_triage(task_dir, output_root / task_dir.name))
    summary = {
        "schema_version": "repo_security_vertical_slice_run_summary.v1",
        "task_count": len(results),
        "pass_count": sum(bool(item["verifier_pass"]) for item in results),
        "results": results,
    }
    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "run_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if results and all(bool(item["verifier_pass"]) for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
