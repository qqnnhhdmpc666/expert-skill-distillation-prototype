from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BASELINE_DIR = ROOT / "outputs" / "harbor_llm_repair_loop_upload_001"
WORK_DIR = ROOT / "outputs" / "validation" / "harbor_llm_repeatability_upload_runs"
JSON_OUT = ROOT / "outputs" / "validation" / "harbor_llm_repeatability_upload.json"
MD_OUT = ROOT / "reports" / "HARBOR_LLM_REPEATABILITY_STATUS.md"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def copy_tree(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def usage_for(run_dir: Path, attempt: str) -> dict[str, Any]:
    model_calls = load_json(run_dir / attempt / "model_calls.json")
    backend = load_json(run_dir / attempt / "backend_metadata.json")
    usage = model_calls.get("usage") or {}
    return {
        "prompt_tokens": usage.get("prompt_tokens"),
        "completion_tokens": usage.get("completion_tokens"),
        "total_tokens": usage.get("total_tokens"),
        "latency_ms": backend.get("latency_ms"),
    }


def summarize_run(run_dir: Path, label: str, origin: str) -> dict[str, Any]:
    summary = load_json(run_dir / "summary.json")
    a1 = summary["A1"]
    a2 = summary["A2"]
    return {
        "label": label,
        "origin": origin,
        "path": str(run_dir.relative_to(ROOT)),
        "a1_pass": a1["pass"],
        "a2_pass": a2["pass"],
        "a1_reward": a1["reward"],
        "a2_reward": a2["reward"],
        "reward_delta": summary["reward_delta"],
        "a1_feedback_type": a1["feedback_type"],
        "a2_feedback_type": a2["feedback_type"],
        "a1_missing_capabilities": a1["missing_capabilities"],
        "a2_missing_capabilities": a2["missing_capabilities"],
        "a1_schema_errors": a1["schema_errors"],
        "a2_schema_errors": a2["schema_errors"],
        "a1_usage": usage_for(run_dir, "A1"),
        "a2_usage": usage_for(run_dir, "A2"),
    }


def render_md(payload: dict[str, Any]) -> str:
    lines = [
        "# Harbor LLM Repeatability Status",
        "",
        f"- Runs observed: `{payload['run_count']}`",
        f"- A1 all fail: `{payload['a1_all_fail']}`",
        f"- A2 all pass: `{payload['a2_all_pass']}`",
        f"- Reward stable: `{payload['reward_stable']}`",
        f"- Failure reason stable: `{payload['failure_reason_stable']}`",
        "",
        "| Run | Origin | A1 | A2 | Reward Delta | A1 Feedback | A1 Missing | Tokens A1/A2 | Latency ms A1/A2 |",
        "|---|---|---:|---:|---:|---|---|---|---|",
    ]
    for run in payload["runs"]:
        a1_usage = run["a1_usage"]
        a2_usage = run["a2_usage"]
        lines.append(
            f"| {run['label']} | {run['origin']} | {run['a1_pass']} | {run['a2_pass']} | {run['reward_delta']} | "
            f"{run['a1_feedback_type']} | {', '.join(run['a1_missing_capabilities']) or 'none'} | "
            f"{a1_usage['total_tokens']}/{a2_usage['total_tokens']} | {a1_usage['latency_ms']}/{a2_usage['latency_ms']} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            f"- Failure mode consistency: `{payload['failure_reason_summary']}`",
            f"- Prompt sensitivity risk: `{payload['prompt_sensitivity_risk']}`",
            f"- Token / latency assessment: `{payload['token_latency_assessment']}`",
            "",
            "## Boundary",
            "",
            "This is repeatability evidence for one controlled Harbor LLM upload repair loop. It is not multi-task Harbor LLM stability evidence.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    if not BASELINE_DIR.exists():
        raise SystemExit(f"missing baseline Harbor loop: {BASELINE_DIR}")
    if WORK_DIR.exists():
        shutil.rmtree(WORK_DIR)
    WORK_DIR.mkdir(parents=True)

    runs: list[dict[str, Any]] = []
    baseline_copy = WORK_DIR / "repeat_1_baseline_existing"
    copy_tree(BASELINE_DIR, baseline_copy)
    runs.append(summarize_run(baseline_copy, "repeat_1", "existing_baseline"))

    for repeat_index in (2, 3):
        out_dir = WORK_DIR / f"repeat_{repeat_index}"
        completed = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "run_harbor_llm_repair_loop.py"),
                "--output-dir",
                str(out_dir),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        write_text(out_dir / "repeat_process_stdout.log", completed.stdout)
        write_text(out_dir / "repeat_process_stderr.log", completed.stderr)
        write_json(out_dir / "repeat_process.json", {"returncode": completed.returncode})
        if completed.returncode != 0:
            raise SystemExit(f"repeat_{repeat_index} failed with returncode {completed.returncode}")
        runs.append(summarize_run(out_dir, f"repeat_{repeat_index}", "fresh_rerun"))

    a1_feedbacks = {run["a1_feedback_type"] for run in runs}
    reward_pairs = {(run["a1_reward"], run["a2_reward"]) for run in runs}
    a1_missing_sets = {tuple(run["a1_missing_capabilities"]) for run in runs}
    avg_total_tokens = round(sum((run["a1_usage"]["total_tokens"] or 0) + (run["a2_usage"]["total_tokens"] or 0) for run in runs) / len(runs), 2)
    avg_latency_ms = round(sum((run["a1_usage"]["latency_ms"] or 0) + (run["a2_usage"]["latency_ms"] or 0) for run in runs) / len(runs), 2)

    payload = {
        "run_id": "harbor_llm_repeatability_upload_001",
        "run_count": len(runs),
        "runs": runs,
        "a1_all_fail": all(not run["a1_pass"] for run in runs),
        "a2_all_pass": all(run["a2_pass"] for run in runs),
        "reward_stable": len(reward_pairs) == 1,
        "failure_reason_stable": len(a1_feedbacks) == 1 and len(a1_missing_sets) == 1,
        "failure_reason_summary": f"feedback_types={sorted(a1_feedbacks)}, missing_sets={sorted(a1_missing_sets)}",
        "prompt_sensitivity_risk": "low_in_this_slice" if len(a1_feedbacks) == 1 and len(a1_missing_sets) == 1 else "nontrivial",
        "token_latency_assessment": f"average total tokens per loop={avg_total_tokens}, average combined latency ms per loop={avg_latency_ms}",
        "boundary": "Repeatability evaluated only for the controlled Harbor LLM upload A1/A2 repair loop.",
    }
    write_json(JSON_OUT, payload)
    write_text(MD_OUT, render_md(payload))
    print(json.dumps({"json": str(JSON_OUT), "report": str(MD_OUT), "run_count": len(runs)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
