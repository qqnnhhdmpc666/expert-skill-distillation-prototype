from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def run_script(args: list[str]) -> int:
    return subprocess.call([sys.executable, *args], cwd=ROOT)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Lightweight CLI wrapper for the skill deployment prototype.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("check-existing", help="Run the demo artifact health check.")
    subparsers.add_parser("audit-claims", help="Run artifact claim audit.")
    subparsers.add_parser("validate-cases", help="Validate API-review holdout task cases.")
    subparsers.add_parser("run-holdout", help="Run the small controlled holdout evaluation.")
    args = parser.parse_args(argv)

    if args.command == "check-existing":
        return run_script(["scripts/run_demo_pipeline.py", "--check-existing"])
    if args.command == "audit-claims":
        return run_script(["scripts/run_artifact_claim_audit.py"])
    if args.command == "validate-cases":
        return run_script(["scripts/validate_task_cases.py"])
    if args.command == "run-holdout":
        return run_script(["scripts/run_real_effect_eval.py"])
    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
