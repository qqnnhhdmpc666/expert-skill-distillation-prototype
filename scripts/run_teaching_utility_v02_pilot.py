from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
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
    update_active_candidates,
)


OUTPUT_ROOT = ROOT / "outputs" / "teaching_utility_v02"
REPORT = ROOT / "reports" / "TEACHING_UTILITY_V02_STATUS.md"
SUMMARY_PATH = OUTPUT_ROOT / "teaching_utility_v02_summary.json"
FREEZE_MANIFEST_PATH = OUTPUT_ROOT / "frozen_method_manifest.json"
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


def sha256_text(path: Path) -> str:
    return hashlib.sha256(path.read_text(encoding="utf-8").encode("utf-8")).hexdigest()


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
    infra_retries: int = 1,
) -> dict[str, Any]:
    if run_dir.exists():
        shutil.rmtree(run_dir)
    attempts: list[dict[str, Any]] = []
    final_summary: dict[str, Any] | None = None
    for attempt_index in range(1, infra_retries + 2):
        attempt_dir = run_dir / f"attempt_{attempt_index:02d}"
        workspace = attempt_dir / "visible_case"
        materialize_visible_case(case, workspace)
        agent_dir = attempt_dir / "agent_run"
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
        write_text(attempt_dir / "stdout.log", completed.stdout)
        write_text(attempt_dir / "stderr.log", completed.stderr)
        review = read_json(agent_dir / "review.json", {"findings": [], "summary": "missing_review", "status": "failed"})
        evaluation = evaluate_review(case, review)
        status = str(review.get("status") or "")
        attempt_summary = {
            "attempt_index": attempt_index,
            "case_id": case.case_id,
            "domain": case.domain,
            "skill_path": str(skill_path),
            "returncode": completed.returncode,
            "review": review,
            "evaluation": evaluation,
            "artifact_dir": str(attempt_dir),
        }
        write_json(attempt_dir / "summary.json", attempt_summary)
        attempts.append(
            {
                "attempt_index": attempt_index,
                "status": status,
                "artifact_dir": str(attempt_dir),
            }
        )
        final_summary = attempt_summary
        infra_blocked = status in {"blocked:URLError", "blocked_http_error", "blocked:HTTPError", "blocked:TimeoutError"}
        if infra_blocked and attempt_index <= infra_retries:
            continue
        break
    assert final_summary is not None
    write_json(run_dir / "attempts.json", attempts)
    write_json(run_dir / "summary.json", final_summary)
    return final_summary


def render_report(payload: dict[str, Any]) -> str:
    split_integrity = payload.get("split_integrity", {})
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
        "- sealed hidden cases are fixed globally and excluded from generation/query/validation roles",
        f"- hidden evaluation mode: `{payload.get('hidden_evaluation_mode', 'inline')}`",
        f"- active budget: `{payload['query_budget']} query trajectories per method per repeat`",
        f"- split integrity: `hidden_reused_outside_hidden={split_integrity.get('hidden_reused_outside_hidden', 'unknown')}`",
        "",
        "## Method Summary",
        "",
        "| Method | Mean query score | Mean validation delta | Mean hidden delta | Hidden pass count |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in payload["method_summary"]:
        lines.append(
            f"| {row['method']} | {row['mean_query_score']} | {row['mean_validation_delta']} | "
            f"{row['mean_hidden_delta']} | {row['hidden_pass_count']} / {row['hidden_row_count']} |"
        )
    lines.extend(
        [
            "",
            "## Key Judgment",
            "",
            f"- `task_utility_vs_teaching_utility`: `{payload['task_utility_vs_teaching_utility']}`",
            f"- `active_selection_hypothesis`: `{payload['active_selection_hypothesis']}`",
            f"- `best_method_by_hidden_delta`: `{payload['best_method_by_hidden_delta']}`",
            f"- `active_hidden_delta_minus_contrast`: `{payload.get('active_hidden_delta_minus_contrast', 'unknown')}`",
            f"- `active_hidden_delta_minus_diversity`: `{payload.get('active_hidden_delta_minus_diversity', 'unknown')}`",
            f"- `global_sealed_hidden_cases`: `{', '.join(payload.get('global_sealed_hidden_cases', []))}`",
            f"- `interpretation`: `{payload.get('interpretation', 'not_available')}`",
            "",
            "## Boundary",
            "",
            f"- Query selection is budgeted and repeat-rotated across {payload['task_count']} local tasks over 2 domains.",
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
    parser.add_argument("--query-budget", type=int, default=2)
    parser.add_argument(
        "--defer-hidden",
        action="store_true",
        help="Freeze final method skills and skip sealed-hidden evaluation; run scripts/run_teaching_utility_v02_hidden_eval.py once afterward.",
    )
    args = parser.parse_args(argv)

    api_key = os.environ.get("OPENAI_API_KEY") or ""
    if not api_key:
        payload = {
            "generated_at": utc_now(),
            "status": "blocked_missing_openai_api_key",
            "repeat_count": args.repeats,
            "query_budget": args.query_budget,
            "methods": list(METHODS),
        }
        write_json(SUMMARY_PATH, payload)
        write_text(REPORT, render_report({**payload, "method_summary": [], "task_utility_vs_teaching_utility": "blocked", "active_selection_hypothesis": "blocked", "best_method_by_hidden_delta": "none"}))
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 2

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    repeat_plans = build_repeat_plans(ROOT, repeats=args.repeats)
    global_hidden_ids = sorted({case.case_id for plan in repeat_plans for case in plan.hidden_cases})
    non_hidden_role_ids = sorted(
        {
            case.case_id
            for plan in repeat_plans
            for case in (*plan.generation_cases, *plan.query_cases, *plan.validation_cases)
        }
    )
    hidden_reused_outside_hidden = bool(set(global_hidden_ids) & set(non_hidden_role_ids))
    base_skill_text = render_cross_domain_base_skill(ROOT)
    base_skill_path = OUTPUT_ROOT / "base_skill.md"
    write_text(base_skill_path, base_skill_text)

    repeats_output: list[dict[str, Any]] = []
    method_rows: list[dict[str, Any]] = []
    frozen_methods: list[dict[str, Any]] = []
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
            selected_query_lessons=[],
        )
        seed_skill_path = repeat_dir / "seed_skill.md"
        write_text(seed_skill_path, seed_skill_text)
        split_manifest = {
            "repeat_index": plan.repeat_index,
            "generation_cases": [case.case_id for case in plan.generation_cases],
            "active_query_pool": [case.case_id for case in plan.query_cases],
            "validation_cases": [case.case_id for case in plan.validation_cases],
            "sealed_hidden_cases": [case.case_id for case in plan.hidden_cases],
            "hidden_first_accessed_at": None,
        }
        write_json(repeat_dir / "split_manifest.json", split_manifest)

        baseline_validation = []
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
        baseline_hidden = []
        if not args.defer_hidden:
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
            "baseline_hidden_score": baseline_hidden_score if baseline_hidden else None,
            "baseline_seed_skill_path": str(seed_skill_path),
            "baseline_seed_skill_hash": sha256_text(seed_skill_path),
            "methods": [],
        }

        for method_index, method_name in enumerate(METHODS, start=1):
            selected_query_lessons: list[dict[str, Any]] = []
            selected_query_cases: list[PilotCase] = []
            prior_candidates: list[dict[str, Any]] | None = None
            query_rounds: list[dict[str, Any]] = []
            current_skill_path = seed_skill_path
            remaining_query_cases = list(plan.query_cases)

            for round_index in range(1, min(args.query_budget, len(remaining_query_cases)) + 1):
                selection = select_query_case(
                    method_name,
                    query_cases=tuple(remaining_query_cases),
                    generation_cases=plan.generation_cases,
                    source_lessons=source_lessons,
                    selected_query_lessons=selected_query_lessons,
                    seed=(plan.repeat_index * 1000) + (method_index * 100) + round_index,
                    prior_candidates=prior_candidates,
                    observed_cases=plan.generation_cases + tuple(selected_query_cases),
                )
                selected_case = next(case for case in remaining_query_cases if case.case_id == selection["selected_case_id"])
                query_run = run_case_agent(
                    case=selected_case,
                    skill_path=current_skill_path,
                    run_dir=repeat_dir / method_name / f"round_{round_index:02d}" / "query" / selected_case.case_id,
                    base_url=args.base_url,
                    model=args.model,
                    timeout_seconds=args.timeout_seconds,
                    max_steps=args.max_steps,
                    api_key=api_key,
                )
                query_lesson = trajectory_lesson_from_run(selected_case, query_run["evaluation"], query_run["review"])
                selected_query_lessons.append(query_lesson)
                selected_query_cases.append(selected_case)
                if method_name == "active_discriminative_evidence":
                    prior_candidates = update_active_candidates(
                        candidates=[dict(candidate) for candidate in selection.get("candidates", [])],
                        case=selected_case,
                        query_run=query_run,
                    )
                round_skill_text = render_distilled_skill(
                    ROOT,
                    method_name=method_name,
                    repeat_index=plan.repeat_index,
                    source_lessons=source_lessons,
                    selected_query_lessons=selected_query_lessons,
                )
                current_skill_path = repeat_dir / method_name / f"round_{round_index:02d}" / "distilled_skill.md"
                write_text(current_skill_path, round_skill_text)
                round_payload = {
                    "round_index": round_index,
                    "selection": selection,
                    "selected_case_id": selected_case.case_id,
                    "query_run": query_run,
                    "query_lesson": query_lesson,
                    "candidate_updates": prior_candidates if method_name == "active_discriminative_evidence" else [],
                    "skill_path_after_round": str(current_skill_path),
                }
                write_json(repeat_dir / method_name / f"round_{round_index:02d}" / "round_summary.json", round_payload)
                query_rounds.append(round_payload)
                remaining_query_cases = [case for case in remaining_query_cases if case.case_id != selected_case.case_id]

            final_skill_text = render_distilled_skill(
                ROOT,
                method_name=method_name,
                repeat_index=plan.repeat_index,
                source_lessons=source_lessons,
                selected_query_lessons=selected_query_lessons,
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
            if not args.defer_hidden:
                split_manifest["hidden_first_accessed_at"] = split_manifest["hidden_first_accessed_at"] or utc_now()
                write_json(repeat_dir / "split_manifest.json", split_manifest)
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
            final_skill_hash = sha256_text(final_skill_path)
            method_payload = {
                "method": method_name,
                "query_rounds": query_rounds,
                "selected_query_case_ids": [row["selected_case_id"] for row in query_rounds],
                "selected_query_lessons": selected_query_lessons,
                "mean_query_score": mean([float(row["query_run"]["evaluation"]["score"]) for row in query_rounds]),
                "final_skill_path": str(final_skill_path),
                "validation_runs": validation_runs,
                "hidden_runs": hidden_runs,
                "validation_score": validation_score,
                "hidden_score": hidden_score if hidden_runs else None,
                "validation_delta": round(validation_score - baseline_validation_score, 4),
                "hidden_delta": round(hidden_score - baseline_hidden_score, 4) if hidden_runs and baseline_hidden else None,
                "hidden_pass_count": sum(1 for item in hidden_runs if item["evaluation"]["pass_at_1"]),
                "hidden_row_count": len(hidden_runs),
                "final_skill_hash": final_skill_hash,
                "hidden_evaluation_status": "deferred" if args.defer_hidden else "inline_complete",
                "final_candidate_state": prior_candidates if method_name == "active_discriminative_evidence" else [],
            }
            write_json(repeat_dir / method_name / "method_summary.json", method_payload)
            frozen_methods.append(
                {
                    "repeat_index": plan.repeat_index,
                    "method": method_name,
                    "final_skill_path": str(final_skill_path),
                    "final_skill_hash": final_skill_hash,
                    "validation_score": validation_score,
                    "validation_delta": method_payload["validation_delta"],
                    "selected_query_case_ids": method_payload["selected_query_case_ids"],
                    "sealed_hidden_cases": [case.case_id for case in plan.hidden_cases],
                }
            )
            repeat_payload["methods"].append(method_payload)
            for round_payload in query_rounds:
                method_rows.append(
                    {
                        "repeat_index": plan.repeat_index,
                        "method": method_name,
                        "round_index": round_payload["round_index"],
                        "query_score": round(float(round_payload["query_run"]["evaluation"]["score"]), 4),
                        "validation_delta": method_payload["validation_delta"],
                        "hidden_delta": method_payload["hidden_delta"],
                        "hidden_pass_count": method_payload["hidden_pass_count"],
                        "selected_case_id": round_payload["selected_case_id"],
                    }
                )

        write_json(repeat_dir / "repeat_summary.json", repeat_payload)
        repeats_output.append(repeat_payload)

    method_summary = []
    for method_name in METHODS:
        repeat_subset = [
            method_payload
            for repeat_payload in repeats_output
            for method_payload in repeat_payload["methods"]
            if method_payload["method"] == method_name
        ]
        method_summary.append(
            {
                "method": method_name,
                "repeat_count": len(repeat_subset),
                "mean_query_score": mean([float(row["mean_query_score"]) for row in repeat_subset]),
                "mean_validation_delta": mean([float(row["validation_delta"]) for row in repeat_subset]),
                "mean_hidden_delta": mean([float(row["hidden_delta"]) for row in repeat_subset if row["hidden_delta"] is not None]),
                "hidden_pass_count": sum(int(row["hidden_pass_count"]) for row in repeat_subset),
                "hidden_row_count": sum(int(row["hidden_row_count"]) for row in repeat_subset),
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
    query_scores = [float(row["mean_query_score"]) for row in method_summary]
    hidden_deltas = [float(row["mean_hidden_delta"]) for row in method_summary]
    if args.defer_hidden:
        task_vs_teaching = "pending_independent_hidden_eval"
        active_hypothesis = "pending_independent_hidden_eval"
        best_method = "pending_independent_hidden_eval"
        interpretation = "method skills are frozen; run the independent sealed-hidden evaluator once"
    elif round(max(hidden_deltas) - min(hidden_deltas), 4) == 0.0 and round(max(query_scores) - min(query_scores), 4) > 0.0:
        task_vs_teaching = "task_utility_not_predictive_in_this_sealed_run"
        interpretation = "query/task scores differ, but sealed hidden teaching utility is flat across methods"
    elif best_method != "top_reward_success_only" and active["mean_query_score"] <= next(row for row in method_summary if row["method"] == "top_reward_success_only")["mean_query_score"]:
        task_vs_teaching = "divergent_signal_detected"
        interpretation = "the hidden-best method is not explained by immediate top-reward task utility"
    else:
        task_vs_teaching = "rough_alignment"
        interpretation = "hidden signal does not contradict immediate task utility under this bounded pilot"
    active_minus_contrast = round(float(active["mean_hidden_delta"]) - float(contrast["mean_hidden_delta"]), 4)
    active_minus_diversity = round(float(active["mean_hidden_delta"]) - float(diversity["mean_hidden_delta"]), 4)
    freeze_manifest = {
        "generated_at": utc_now(),
        "status": "frozen_pending_independent_hidden_eval" if args.defer_hidden else "inline_hidden_eval_also_present",
        "base_url": args.base_url,
        "model": args.model,
        "repeat_count": args.repeats,
        "query_budget": args.query_budget,
        "global_sealed_hidden_cases": global_hidden_ids,
        "split_integrity": {
            "hidden_reused_outside_hidden": hidden_reused_outside_hidden,
            "non_hidden_role_case_ids": non_hidden_role_ids,
        },
        "baseline_seed_skills": [
            {
                "repeat_index": repeat_payload["repeat_index"],
                "skill_path": repeat_payload["baseline_seed_skill_path"],
                "skill_hash": repeat_payload["baseline_seed_skill_hash"],
                "sealed_hidden_cases": repeat_payload["hidden_cases"],
            }
            for repeat_payload in repeats_output
        ],
        "methods": frozen_methods,
        "hidden_eval_command": "skill-deploy teaching-utility-v02-hidden-eval --manifest outputs/teaching_utility_v02/frozen_method_manifest.json",
    }
    write_json(FREEZE_MANIFEST_PATH, freeze_manifest)
    payload = {
        "generated_at": utc_now(),
        "repeat_count": args.repeats,
        "query_budget": args.query_budget,
        "methods": list(METHODS),
        "base_url": args.base_url,
        "model": args.model,
        "hidden_evaluation_mode": "deferred_independent_script" if args.defer_hidden else "inline",
        "freeze_manifest": str(FREEZE_MANIFEST_PATH),
        "task_count": len({case.case_id for case in repeat_plans[0].generation_cases + repeat_plans[0].query_cases + repeat_plans[0].validation_cases + repeat_plans[0].hidden_cases}),
        "global_sealed_hidden_cases": global_hidden_ids,
        "split_integrity": {
            "hidden_reused_outside_hidden": hidden_reused_outside_hidden,
            "non_hidden_role_case_ids": non_hidden_role_ids,
            "boundary": "candidate generation and query selection use generation/query/validation roles only; sealed hidden ids are fixed globally.",
        },
        "repeats": repeats_output,
        "method_rows": method_rows,
        "method_summary": method_summary,
        "task_utility_vs_teaching_utility": task_vs_teaching,
        "active_selection_hypothesis": active_hypothesis,
        "best_method_by_hidden_delta": best_method,
        "active_hidden_delta_minus_contrast": active_minus_contrast,
        "active_hidden_delta_minus_diversity": active_minus_diversity,
        "interpretation": interpretation,
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
