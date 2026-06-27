from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from scripts.run_teaching_utility_v02_pilot import mean, run_case_agent, write_json, write_text  # noqa: E402
from skill_deployment.teaching_utility_v02 import build_repeat_plans  # noqa: E402


OUTPUT_ROOT = ROOT / "outputs" / "teaching_utility_v02" / "sealed_hidden_eval"
SUMMARY_PATH = OUTPUT_ROOT / "sealed_hidden_eval_summary.json"
REPORT = ROOT / "reports" / "TEACHING_UTILITY_V02_SEALED_HIDDEN_STATUS.md"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def render_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Teaching Utility v0.2 Independent Sealed Hidden Evaluation",
        "",
        f"Generated at: `{payload['generated_at']}`",
        "",
        "This report is produced by the independent hidden evaluator after method Skill hashes were frozen.",
        "It should not be used to modify candidate generation or query selection.",
        "",
        "## Fresh Command",
        "",
        "```powershell",
        payload["fresh_command"],
        "```",
        "",
        "## Split Integrity",
        "",
        f"- manifest: `{payload['manifest_path']}`",
        f"- first hidden access: `{payload['first_hidden_accessed_at']}`",
        f"- repeated run allowed: `{payload['force']}`",
        f"- hidden reused outside hidden: `{payload['split_integrity'].get('hidden_reused_outside_hidden')}`",
        f"- global sealed hidden cases: `{', '.join(payload['global_sealed_hidden_cases'])}`",
        "",
        "## Method Summary",
        "",
        "| Method | Mean hidden delta | Hidden pass count | Rows |",
        "|---|---:|---:|---:|",
    ]
    for row in payload["method_summary"]:
        lines.append(
            f"| {row['method']} | {row['mean_hidden_delta']} | "
            f"{row['hidden_pass_count']} | {row['hidden_row_count']} |"
        )
    lines.extend(
        [
            "",
            "## Key Judgment",
            "",
            f"- `task_utility_vs_teaching_utility`: `{payload['task_utility_vs_teaching_utility']}`",
            f"- `active_selection_hypothesis`: `{payload['active_selection_hypothesis']}`",
            f"- `best_method_by_hidden_delta`: `{payload['best_method_by_hidden_delta']}`",
            f"- `active_hidden_delta_minus_contrast`: `{payload['active_hidden_delta_minus_contrast']}`",
            f"- `active_hidden_delta_minus_diversity`: `{payload['active_hidden_delta_minus_diversity']}`",
            f"- `interpretation`: `{payload['interpretation']}`",
            "",
            "## Boundary",
            "",
            "- This evaluator reads sealed hidden cases after frozen Skill paths and hashes already exist.",
            "- It does not regenerate methods, alter Skill text, or feed hidden results back into the pilot.",
            "- It is still a local bounded pilot, not official external benchmark evidence.",
        ]
    )
    return "\n".join(lines) + "\n"


def summarize_hidden(method_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    methods = sorted({row["method"] for row in method_rows})
    summary: list[dict[str, Any]] = []
    for method in methods:
        rows = [row for row in method_rows if row["method"] == method]
        summary.append(
            {
                "method": method,
                "repeat_count": len({row["repeat_index"] for row in rows}),
                "mean_hidden_delta": mean([float(row["hidden_delta"]) for row in rows]),
                "hidden_pass_count": sum(int(row["hidden_pass_count"]) for row in rows),
                "hidden_row_count": sum(int(row["hidden_row_count"]) for row in rows),
            }
        )

    by_method = {row["method"]: row for row in summary}
    active = by_method.get("active_discriminative_evidence", {"mean_hidden_delta": 0.0})
    contrast = by_method.get("success_failure_contrast", {"mean_hidden_delta": 0.0})
    diversity = by_method.get("diversity", {"mean_hidden_delta": 0.0})
    hidden_deltas = [float(row["mean_hidden_delta"]) for row in summary]
    hidden_delta_span = round(max(hidden_deltas) - min(hidden_deltas), 4) if hidden_deltas else 0.0
    best = "tie_all_methods" if hidden_delta_span == 0.0 and summary else max(summary, key=lambda row: row["mean_hidden_delta"])["method"] if summary else "none"
    active_minus_contrast = round(float(active["mean_hidden_delta"]) - float(contrast["mean_hidden_delta"]), 4)
    active_minus_diversity = round(float(active["mean_hidden_delta"]) - float(diversity["mean_hidden_delta"]), 4)
    if active_minus_contrast > 0 and active_minus_diversity > 0:
        active_hypothesis = "supported"
    elif active_minus_contrast < 0 or active_minus_diversity < 0:
        active_hypothesis = "hypothesis_not_supported"
    else:
        active_hypothesis = "inconclusive"
    if hidden_deltas and hidden_delta_span == 0.0:
        task_vs_teaching = "flat_sealed_hidden_signal"
        interpretation = "independent sealed hidden utility is flat across frozen methods"
    elif best != "top_reward_success_only":
        task_vs_teaching = "divergent_signal_detected"
        interpretation = "the sealed-hidden-best method is not the immediate top-reward baseline"
    else:
        task_vs_teaching = "rough_alignment"
        interpretation = "sealed hidden utility is aligned with the top-reward baseline under this pilot"
    return summary, {
        "active_selection_hypothesis": active_hypothesis,
        "best_method_by_hidden_delta": best,
        "active_hidden_delta_minus_contrast": active_minus_contrast,
        "active_hidden_delta_minus_diversity": active_minus_diversity,
        "task_utility_vs_teaching_utility": task_vs_teaching,
        "interpretation": interpretation,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run independent sealed-hidden evaluation for frozen v0.2 teaching-utility skills.")
    parser.add_argument("--manifest", default=str(ROOT / "outputs" / "teaching_utility_v02" / "frozen_method_manifest.json"))
    parser.add_argument("--base-url", default=os.environ.get("OPENAI_BASE_URL") or "https://api.deepseek.com")
    parser.add_argument("--model", default=os.environ.get("MODEL") or os.environ.get("OPENAI_MODEL") or "deepseek-v4-flash")
    parser.add_argument("--timeout-seconds", type=float, default=60.0)
    parser.add_argument("--max-steps", type=int, default=4)
    parser.add_argument("--force", action="store_true", help="Allow rerunning sealed hidden evaluation and overwrite the previous summary.")
    args = parser.parse_args(argv)

    api_key = os.environ.get("OPENAI_API_KEY") or ""
    if not api_key:
        payload = {
            "generated_at": utc_now(),
            "status": "blocked_missing_openai_api_key",
            "manifest_path": args.manifest,
        }
        write_json(SUMMARY_PATH, payload)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 2

    manifest_path = Path(args.manifest)
    if not manifest_path.is_absolute():
        manifest_path = ROOT / manifest_path
    manifest = read_json(manifest_path)
    if SUMMARY_PATH.exists() and not args.force:
        existing = read_json(SUMMARY_PATH)
        payload = {
            "generated_at": utc_now(),
            "status": "blocked_existing_sealed_hidden_summary",
            "existing_summary": str(SUMMARY_PATH),
            "first_hidden_accessed_at": existing.get("first_hidden_accessed_at"),
            "reason": "sealed hidden evaluator is single-use by default; pass --force only for an explicit rerun audit",
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 3

    repeat_plans = {plan.repeat_index: plan for plan in build_repeat_plans(ROOT, repeats=int(manifest["repeat_count"]))}
    first_hidden_accessed_at = utc_now()
    baseline_scores: dict[int, float] = {}
    baseline_runs: list[dict[str, Any]] = []
    for baseline in manifest["baseline_seed_skills"]:
        repeat_index = int(baseline["repeat_index"])
        plan = repeat_plans[repeat_index]
        runs = []
        for case in plan.hidden_cases:
            runs.append(
                run_case_agent(
                    case=case,
                    skill_path=Path(baseline["skill_path"]),
                    run_dir=OUTPUT_ROOT / f"repeat_{repeat_index:02d}" / "baseline_seed" / case.case_id,
                    base_url=args.base_url,
                    model=args.model,
                    timeout_seconds=args.timeout_seconds,
                    max_steps=args.max_steps,
                    api_key=api_key,
                )
            )
        baseline_score = mean([float(item["evaluation"]["score"]) for item in runs])
        baseline_scores[repeat_index] = baseline_score
        baseline_runs.append(
            {
                "repeat_index": repeat_index,
                "skill_path": baseline["skill_path"],
                "skill_hash": baseline["skill_hash"],
                "hidden_score": baseline_score,
                "hidden_runs": runs,
            }
        )

    method_rows: list[dict[str, Any]] = []
    for method in manifest["methods"]:
        repeat_index = int(method["repeat_index"])
        plan = repeat_plans[repeat_index]
        runs = []
        for case in plan.hidden_cases:
            runs.append(
                run_case_agent(
                    case=case,
                    skill_path=Path(method["final_skill_path"]),
                    run_dir=OUTPUT_ROOT / f"repeat_{repeat_index:02d}" / method["method"] / case.case_id,
                    base_url=args.base_url,
                    model=args.model,
                    timeout_seconds=args.timeout_seconds,
                    max_steps=args.max_steps,
                    api_key=api_key,
                )
            )
        hidden_score = mean([float(item["evaluation"]["score"]) for item in runs])
        method_rows.append(
            {
                "repeat_index": repeat_index,
                "method": method["method"],
                "skill_path": method["final_skill_path"],
                "skill_hash": method["final_skill_hash"],
                "hidden_score": hidden_score,
                "hidden_delta": round(hidden_score - baseline_scores[repeat_index], 4),
                "hidden_pass_count": sum(1 for item in runs if item["evaluation"]["pass_at_1"]),
                "hidden_row_count": len(runs),
                "hidden_runs": runs,
            }
        )

    method_summary, judgment = summarize_hidden(method_rows)
    payload = {
        "generated_at": utc_now(),
        "status": "complete",
        "fresh_command": "skill-deploy teaching-utility-v02-hidden-eval --manifest outputs/teaching_utility_v02/frozen_method_manifest.json",
        "manifest_path": str(manifest_path),
        "first_hidden_accessed_at": first_hidden_accessed_at,
        "force": bool(args.force),
        "base_url": args.base_url,
        "model": args.model,
        "global_sealed_hidden_cases": manifest["global_sealed_hidden_cases"],
        "split_integrity": manifest["split_integrity"],
        "baseline_runs": baseline_runs,
        "method_rows": method_rows,
        "method_summary": method_summary,
        **judgment,
    }
    write_json(SUMMARY_PATH, payload)
    write_text(REPORT, render_report(payload))
    print(
        json.dumps(
            {
                "summary": str(SUMMARY_PATH),
                "report": str(REPORT),
                "active_selection_hypothesis": payload["active_selection_hypothesis"],
                "best_method_by_hidden_delta": payload["best_method_by_hidden_delta"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
