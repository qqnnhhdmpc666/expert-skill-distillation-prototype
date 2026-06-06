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
    subparsers.add_parser("compare-baselines", help="Run the component baseline attribution slice.")
    subparsers.add_parser("compare-trace-policy", help="Run the risk-vs-random selective trace baseline.")
    subparsers.add_parser("trace-robustness", help="Enumerate all size-2 trace policy allocations.")
    subparsers.add_parser("analyze-summary-miss", help="Analyze direct-summary residual misses.")
    subparsers.add_parser("revision-matrix", help="Run the constrained post-execution revision matrix.")
    subparsers.add_parser("posterior-signal-audit", help="Audit posterior revision signal diagnostics.")
    subparsers.add_parser("naive-revision-ablation", help="Run naive revision strategy pressure-test ablation.")
    args = parser.parse_args(argv)

    if args.command == "check-existing":
        return run_script(["scripts/run_demo_pipeline.py", "--check-existing"])
    if args.command == "audit-claims":
        return run_script(["scripts/run_artifact_claim_audit.py"])
    if args.command == "validate-cases":
        return run_script(["scripts/validate_task_cases.py"])
    if args.command == "run-holdout":
        return run_script(["scripts/run_real_effect_eval.py"])
    if args.command == "compare-baselines":
        return run_script(["scripts/run_component_baseline_eval.py"])
    if args.command == "compare-trace-policy":
        return run_script(["scripts/run_risk_trace_policy_baseline.py"])
    if args.command == "trace-robustness":
        return run_script(["scripts/run_risk_trace_policy_robustness.py"])
    if args.command == "analyze-summary-miss":
        return run_script(["scripts/run_direct_summary_miss_analysis.py"])
    if args.command == "revision-matrix":
        return run_script(["scripts/run_revision_decision_matrix.py"])
    if args.command == "posterior-signal-audit":
        return run_script(["scripts/run_posterior_revision_signal_audit.py"])
    if args.command == "naive-revision-ablation":
        return run_script(["scripts/run_naive_revision_ablation.py"])
    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
