from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from demo.streamlit_app import SCENARIOS, build_run, package_directory_files, scenario_by_id, target_asset_files


REQUIRED_RUN_FILES = (
    "summary/front_metrics.json",
    "attempts/A0_no_skill.json",
    "attempts/A1_skill_v1.json",
    "attempts/A2_skill_v2.json",
    "verifier/A1_feedback.json",
    "verifier/A2_feedback.json",
    "reports/correction_report.md",
    "reports/final_report.md",
    "artifacts/skill_package_v2_manifest.json",
    "model_calls.json",
)

REQUIRED_PACKAGE_FILES = (
    "manifest.yaml",
    "SKILL.md",
    "contracts/output_schema.json",
    "contracts/verifier_contract.yaml",
    "trace_policy.yaml",
    "examples/positive_example.md",
    "examples/negative_example.md",
    "changelog.md",
)


def missing(root: Path, rels: tuple[str, ...]) -> list[str]:
    return [rel for rel in rels if not (root / rel).exists()]


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the result-first demo artifacts.")
    parser.add_argument("--scenario", default="upload", choices=["upload", *[item.scenario_id for item in SCENARIOS]])
    args = parser.parse_args()

    scenario = scenario_by_id(args.scenario)
    run = build_run(scenario)
    run_dir = Path(run["session_dir"])
    package_files = package_directory_files(run["pkg_v2"], scenario)
    target_files = target_asset_files(scenario)

    package_missing = [rel for rel in REQUIRED_PACKAGE_FILES if rel not in package_files]
    target_missing = [
        rel
        for rel in (
            "target_asset/task_brief.md",
            "target_asset/api.yaml",
            "target_asset/app.py",
            "target_asset/config.yaml",
        )
        if rel not in target_files
    ]
    metrics = json.loads((run_dir / "summary" / "front_metrics.json").read_text(encoding="utf-8"))
    final_report = (run_dir / "reports" / "final_report.md").read_text(encoding="utf-8")
    correction_report = (run_dir / "reports" / "correction_report.md").read_text(encoding="utf-8")

    result = {
        "scenario": scenario.scenario_id,
        "run_dir": str(run_dir),
        "status_chain": metrics["status_chain"],
        "success_rate_after": metrics["success_rate_after"],
        "missing": {
            "run": missing(run_dir, REQUIRED_RUN_FILES),
            "package": package_missing,
            "target": target_missing,
        },
        "checks": {
            "a2_passes": run["verifier2"]["status"] == "PASS",
            "improves_over_a1": metrics["success_rate_after"] > metrics["success_rate_before"],
            "final_report_has_findings": "最终发现" in final_report,
            "correction_report_has_reason": "为什么 v1 没通过" in correction_report,
            "token_cost_in_budget": metrics["token_total"] <= metrics["token_budget"],
        },
    }
    ok = all(not values for values in result["missing"].values()) and all(result["checks"].values())
    result["ok"] = ok
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
