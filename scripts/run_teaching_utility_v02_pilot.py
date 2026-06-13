from __future__ import annotations

import argparse
import json
import os
import subprocess
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

from skill_deployment.teaching_utility_v02 import (  # noqa: E402
    PilotCase,
    build_repeat_plans,
    evaluate_review,
    extract_rule_ids,
    render_cross_domain_base_skill,
    render_distilled_skill,
    select_query_case,
    trajectory_lesson_from_run,
)


OUTPUT_ROOT = ROOT / "outputs" / "teaching_utility_v02"
REPORT = ROOT / "reports" / "TEACHING_UTILITY_V02_STATUS.md"
SUMMARY_PATH = OUTPUT_ROOT / "teaching_utility_v02_summary.json"
METHODS = (
    "random",
    "top_reward_success_only",
    "success_failure_contrast",
    "diversity",
    "active_discriminative_evidence",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def mean(values: list[float]) -> float:
    return round(sum(values) / len(values), 4) if values else 0.0


def materialize_visible_case(case: PilotCase, workspace: Path) -> None:
    workspace.mkdir(parents=True, exist_ok=True)
    for name, text in case.visible_files:
        write_text(workspace / name, text)
    write_json(
        workspace / "agent_visible_manifest.json",
        {
            "case_id": case.case_id,
            "domain": case.domain,
            "visible_files": [name for name, _text in case.visible_files],
            "boundary": "No verifier-only oracle fields are present in this workspace.",
        },
    )


def run_case_agent(
    *,
    case: PilotCase,
    skill_path: Path,
    run_dir: Path,
    base_url: str,
    model: str,
    timeout_seconds: float,
    max_steps: int,
    api_key: str,
) -> dict[str, Any]:
    workspace = run_dir / "visible_case"
    materialize_visible_case(case, workspace)
    agent_dir = run_dir / "agent_run"
    allowed_from_skill = [
        rule_id
        for rule_id in extract_rule_ids(skill_path.read_text(encoding="utf-8"))
        if rule_id.startswith("R" if case.domain == "api_review" else "C")
    ]
    command = [
        sys.executable,
        str(ROOT / "agents" / "live_tool_case_agent.py"),
        "--domain",
        case.domain,
        "--case-root",
        str(workspace),
        "--skill",
        str(skill_path),
        "--out",
        str(agent_dir),
        "--allowed-rule-ids",
        ",".join(allowed_from_skill),
        "--base-url",
        base_url,
        "--model",
        model,
        "--timeout-seconds",
        str(timeout_seconds),
        "--max-steps",
        str(max_steps),
    ]
    env = dict(os.environ)
    env["OPENAI_API_KEY"] = api_key
    completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, env=env, check=False)
    write_text(run_dir / "stdout.log", completed.stdout)
    write_text(run_dir / "stderr.log", completed.stderr)
    review = read_json(agent_dir / "review.json", {"findings": [], "summary": "missing_review", "status": "failed"})
    evaluation = evaluate_review(case, review)
    summary = {
        "case_id": case.case_id,
        "domain": case.domain,
        "skill_path": str(skill_path),
        "returncode": completed.returncode,
        "review": review,
        "evaluation": evaluation,
        "artifact_dir": str(run_dir),
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def active_candidate_updates(selection_payload: dict[str, Any], query_run: dict[str, Any]) -> list[dict[str, Any]]:
    updates: list[dict[str, Any]] = []
    actual = set(query_run["evaluation"]["seen_rule_ids"])
    for candidate in selection_payload.get("candidates", []):
        predicted = set()
        for row in selection_payload.get("disagreement_matrix", []):
            if row["case_id"] != query_run["case_id"]:
                continue
            for item in row.get("predictions", []):
                if item.get("candidate_id") == candidate["candidate_id"]:
                    predicted = set(item.get("predicted_rule_ids", []))
                    break
        union = predicted | actual
        agreement = len(predicted & actual) / len(union) if union else 1.0
        updates.append(
            {
                "candidate_id": candidate["candidate_id"],
                "predicted_rule_ids": sorted(predicted),
                "actual_rule_ids": sorted(actual),
                "agreement": round(agreement, 4),
                "status": "kept" if agreement >= 0.5 else "downweighted",
            }
        )
    return updates


def render_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Teaching Utility v0.2 Pilot Status",
        "",
        f"Generated at: `{payload['generated_at']}`",
        "",
        "This pilot separates immediate task utility from teaching utility.",
        "It does not claim official external benchmark validity.",
        "",
        "## Fresh Command",
        "",
        "```powershell",
        "skill-deploy teaching-utility-v02 --repeats 3 --base-url https://api.deepseek.com --model deepseek-v4-flash",
        "```",
        "",
        "## Pilot Design",
        "",
        f"- repeats: `{payload['repeat_count']}`",
        f"- methods: `{', '.join(payload['methods'])}`",
        "- domains: `api_review`, `config_security`",
        "- split per repeat: `source_generation`, `active_query_pool`, `promotion_validation`, `sealed_hidden_test`",
        "- active budget: `1 query trajectory per method per repeat`",
        "",
        "## Method Summary",
        "",
        "| Method | Mean query score | Mean validation delta | Mean hidden delta | Hidden pass count |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in payload["method_summary"]:
        lines.append(
            f"| {row['method']} | {row['mean_query_score']} | {row['mean_validation_delta']} | "
            f"{row['mean_hidden_delta']} | {row['hidden_pass_count']} / {row['repeat_count']} |"
        )
    lines.extend(
        [
            "",
            "## Key Judgment",
            "",
            f"- `task_utility_vs_teaching_utility`: `{payload['task_utility_vs_teaching_utility']}`",
            f"- `active_selection_hypothesis`: `{payload['active_selection_hypothesis']}`",
            f"- `best_method_by_hidden_delta`: `{payload['best_method_by_hidden_delta']}`",
            "",
            "## Boundary",
            "",
            "- Query selection is budgeted and repeat-rotated across 8 local tasks over 2 domains.",
            "- Hidden-test evaluation uses the live tool agent; validation remains local and bounded.",
            "- If active discriminative selection does not beat contrast/diversity, the hypothesis is recorded as not supported or inconclusive.",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the v0.2 teaching-utility pilot over two domains and matched query budgets.")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--base-url", default=os.environ.get("OPENAI_BASE_URL") or "https://api.deepseek.com")
    parser.add_argument("--model", default=os.environ.get("MODEL") or os.environ.get("OPENAI_MODEL") or "deepseek-v4-flash")
    parser.add_argument("--timeout-seconds", type=float, default=60.0)
    parser.add_argument("--max-steps", type=int, default=4)
    args = parser.parse_args(argv)

    api_key = os.environ.get("OPENAI_API_KEY") or ""
    if not api_key:
        payload = {
            "generated_at": utc_now(),
            "status": "blocked_missing_openai_api_key",
            "repeat_count": args.repeats,
            "methods": list(METHODS),
        }
        write_json(SUMMARY_PATH, payload)
        write_text(REPORT, render_report({**payload, "method_summary": [], "task_utility_vs_teaching_utility": "blocked", "active_selection_hypothesis": "blocked", "best_method_by_hidden_delta": "none"}))
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 2

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    repeat_plans = build_repeat_plans(ROOT, repeats=args.repeats)
    base_skill_text = render_cross_domain_base_skill(ROOT)
    base_skill_path = OUTPUT_ROOT / "base_skill.md"
    write_text(base_skill_path, base_skill_text)

    repeats_output: list[dict[str, Any]] = []
    method_rows: list[dict[str, Any]] = []
    for plan in repeat_plans:
        repeat_dir = OUTPUT_ROOT / f"repeat_{plan.repeat_index:02d}"
        repeat_dir.mkdir(parents=True, exist_ok=True)
        source_runs: list[dict[str, Any]] = []
        for case in plan.generation_cases:
            run = run_case_agent(
                case=case,
                skill_path=base_skill_path,
                run_dir=repeat_dir / "source_generation" / case.case_id,
                base_url=args.base_url,
                model=args.model,
                timeout_seconds=args.timeout_seconds,
                max_steps=args.max_steps,
                api_key=api_key,
            )
            source_runs.append(run)
        source_lessons = [trajectory_lesson_from_run(next(case for case in plan.generation_cases if case.case_id == run["case_id"]), run["evaluation"], run["review"]) for run in source_runs]
        seed_skill_text = render_distilled_skill(
            ROOT,
            method_name="seed_material_plus_generation",
            repeat_index=plan.repeat_index,
            source_lessons=source_lessons,
            selected_query_lesson=None,
        )
        seed_skill_path = repeat_dir / "seed_skill.md"
        write_text(seed_skill_path, seed_skill_text)

        baseline_validation = []
        baseline_hidden = []
        for case in plan.validation_cases:
            baseline_validation.append(
                run_case_agent(
                    case=case,
                    skill_path=seed_skill_path,
                    run_dir=repeat_dir / "baseline_validation" / case.case_id,
                    base_url=args.base_url,
                    model=args.model,
                    timeout_seconds=args.timeout_seconds,
                    max_steps=args.max_steps,
                    api_key=api_key,
                )
            )
        for case in plan.hidden_cases:
            baseline_hidden.append(
                run_case_agent(
                    case=case,
                    skill_path=seed_skill_path,
                    run_dir=repeat_dir / "baseline_hidden" / case.case_id,
                    base_url=args.base_url,
                    model=args.model,
                    timeout_seconds=args.timeout_seconds,
                    max_steps=args.max_steps,
                    api_key=api_key,
                )
            )
        baseline_validation_score = mean([float(item["evaluation"]["score"]) for item in baseline_validation])
        baseline_hidden_score = mean([float(item["evaluation"]["score"]) for item in baseline_hidden])
        repeat_payload = {
            "repeat_index": plan.repeat_index,
            "generation_cases": [case.case_id for case in plan.generation_cases],
            "query_cases": [case.case_id for case in plan.query_cases],
            "validation_cases": [case.case_id for case in plan.validation_cases],
            "hidden_cases": [case.case_id for case in plan.hidden_cases],
            "source_runs": source_runs,
            "source_lessons": source_lessons,
            "baseline_validation_score": baseline_validation_score,
            "baseline_hidden_score": baseline_hidden_score,
            "methods": [],
        }

        for method_index, method_name in enumerate(METHODS, start=1):
            selection = select_query_case(
                method_name,
                query_cases=plan.query_cases,
                generation_cases=plan.generation_cases,
                source_lessons=source_lessons,
                seed=plan.repeat_index * 100 + method_index,
            )
            selected_case = next(case for case in plan.query_cases if case.case_id == selection["selected_case_id"])
            query_run = run_case_agent(
                case=selected_case,
                skill_path=seed_skill_path,
                run_dir=repeat_dir / method_name / "query" / selected_case.case_id,
                base_url=args.base_url,
                model=args.model,
                timeout_seconds=args.timeout_seconds,
                max_steps=args.max_steps,
                api_key=api_key,
            )
            query_lesson = trajectory_lesson_from_run(selected_case, query_run["evaluation"], query_run["review"])
            final_skill_text = render_distilled_skill(
                ROOT,
                method_name=method_name,
                repeat_index=plan.repeat_index,
                source_lessons=source_lessons,
                selected_query_lesson=query_lesson,
            )
            final_skill_path = repeat_dir / method_name / "distilled_skill.md"
            write_text(final_skill_path, final_skill_text)

            validation_runs = []
            hidden_runs = []
            for case in plan.validation_cases:
                validation_runs.append(
                    run_case_agent(
                        case=case,
                        skill_path=final_skill_path,
                        run_dir=repeat_dir / method_name / "validation" / case.case_id,
                        base_url=args.base_url,
                        model=args.model,
                        timeout_seconds=args.timeout_seconds,
                        max_steps=args.max_steps,
                        api_key=api_key,
                    )
                )
            for case in plan.hidden_cases:
                hidden_runs.append(
                    run_case_agent(
                        case=case,
                        skill_path=final_skill_path,
                        run_dir=repeat_dir / method_name / "hidden" / case.case_id,
                        base_url=args.base_url,
                        model=args.model,
                        timeout_seconds=args.timeout_seconds,
                        max_steps=args.max_steps,
                        api_key=api_key,
                    )
                )

            validation_score = mean([float(item["evaluation"]["score"]) for item in validation_runs])
            hidden_score = mean([float(item["evaluation"]["score"]) for item in hidden_runs])
            candidate_updates = active_candidate_updates(selection, query_run) if method_name == "active_discriminative_evidence" else []
            method_payload = {
                "method": method_name,
                "selection": selection,
                "query_case": selected_case.case_id,
                "query_run": query_run,
                "query_lesson": query_lesson,
                "final_skill_path": str(final_skill_path),
                "validation_runs": validation_runs,
                "hidden_runs": hidden_runs,
                "validation_score": validation_score,
                "hidden_score": hidden_score,
                "validation_delta": round(validation_score - baseline_validation_score, 4),
                "hidden_delta": round(hidden_score - baseline_hidden_score, 4),
                "hidden_pass_count": sum(1 for item in hidden_runs if item["evaluation"]["pass_at_1"]),
                "candidate_updates": candidate_updates,
            }
            if method_name == "active_discriminative_evidence":
                write_json(repeat_dir / method_name / "candidate_updates.json", candidate_updates)
            write_json(repeat_dir / method_name / "method_summary.json", method_payload)
            repeat_payload["methods"].append(method_payload)
            method_rows.append(
                {
                    "repeat_index": plan.repeat_index,
                    "method": method_name,
                    "query_score": round(float(query_run["evaluation"]["score"]), 4),
                    "validation_delta": method_payload["validation_delta"],
                    "hidden_delta": method_payload["hidden_delta"],
                    "hidden_pass_count": method_payload["hidden_pass_count"],
                    "selected_case_id": selected_case.case_id,
                }
            )

        write_json(repeat_dir / "repeat_summary.json", repeat_payload)
        repeats_output.append(repeat_payload)

    method_summary = []
    for method_name in METHODS:
        subset = [row for row in method_rows if row["method"] == method_name]
        method_summary.append(
            {
                "method": method_name,
                "repeat_count": len(subset),
                "mean_query_score": mean([float(row["query_score"]) for row in subset]),
                "mean_validation_delta": mean([float(row["validation_delta"]) for row in subset]),
                "mean_hidden_delta": mean([float(row["hidden_delta"]) for row in subset]),
                "hidden_pass_count": sum(int(row["hidden_pass_count"]) for row in subset),
            }
        )

    active = next(row for row in method_summary if row["method"] == "active_discriminative_evidence")
    contrast = next(row for row in method_summary if row["method"] == "success_failure_contrast")
    diversity = next(row for row in method_summary if row["method"] == "diversity")
    best_method = max(method_summary, key=lambda item: (item["mean_hidden_delta"], item["mean_validation_delta"]))["method"]
    if active["mean_hidden_delta"] > max(contrast["mean_hidden_delta"], diversity["mean_hidden_delta"]):
        active_hypothesis = "supported"
    elif active["mean_hidden_delta"] < max(contrast["mean_hidden_delta"], diversity["mean_hidden_delta"]):
        active_hypothesis = "hypothesis_not_supported"
    else:
        active_hypothesis = "inconclusive"
    task_vs_teaching = (
        "divergent_signal_detected"
        if best_method != "top_reward_success_only" and active["mean_query_score"] <= next(row for row in method_summary if row["method"] == "top_reward_success_only")["mean_query_score"]
        else "rough_alignment"
    )
    payload = {
        "generated_at": utc_now(),
        "repeat_count": args.repeats,
        "methods": list(METHODS),
        "base_url": args.base_url,
        "model": args.model,
        "repeats": repeats_output,
        "method_rows": method_rows,
        "method_summary": method_summary,
        "task_utility_vs_teaching_utility": task_vs_teaching,
        "active_selection_hypothesis": active_hypothesis,
        "best_method_by_hidden_delta": best_method,
    }
    write_json(SUMMARY_PATH, payload)
    write_text(REPORT, render_report(payload))
    print(
        json.dumps(
            {
                "summary": str(SUMMARY_PATH),
                "report": str(REPORT),
                "active_selection_hypothesis": active_hypothesis,
                "best_method_by_hidden_delta": best_method,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
