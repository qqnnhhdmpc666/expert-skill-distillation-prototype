from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def seconds_between(start: str | None, end: str | None) -> float | None:
    started = parse_time(start)
    finished = parse_time(end)
    if not started or not finished:
        return None
    return round((finished - started).total_seconds(), 3)


def find_trial_dir(job_dir: Path) -> Path:
    trial_dirs = [path for path in job_dir.iterdir() if path.is_dir() and (path / "result.json").exists()]
    if len(trial_dirs) != 1:
        raise ValueError(f"Expected exactly one trial dir under {job_dir}, found {len(trial_dirs)}.")
    return trial_dirs[0]


def infer_failure_type(reward: float, verifier_stdout: str, exception_info: Any) -> str:
    if reward == 1.0:
        return "none"
    if exception_info:
        return "execution_error"
    if "missing expected findings" in verifier_stdout.lower():
        return "missing_rule"
    return "verifier_failure"


def convert_harbor_job(job_dir: Path) -> dict[str, Any]:
    trial_dir = find_trial_dir(job_dir)
    trial_result = read_json(trial_dir / "result.json")
    verifier_stdout_path = trial_dir / "verifier" / "test-stdout.txt"
    verifier_stdout = verifier_stdout_path.read_text(encoding="utf-8") if verifier_stdout_path.exists() else ""
    reward = float((trial_result.get("verifier_result") or {}).get("rewards", {}).get("reward", 0.0))
    passed = reward == 1.0
    final_status = "PASS" if passed else "FAIL"
    failure_type = infer_failure_type(reward, verifier_stdout, trial_result.get("exception_info"))
    affected_rule_ids = [] if passed else sorted(set(re.findall(r"\bR\d{3}\b", verifier_stdout)))
    total_time_s = seconds_between(trial_result.get("started_at"), trial_result.get("finished_at"))
    agent_time_s = seconds_between(
        (trial_result.get("agent_execution") or {}).get("started_at"),
        (trial_result.get("agent_execution") or {}).get("finished_at"),
    )
    verifier_time_s = seconds_between(
        (trial_result.get("verifier") or {}).get("started_at"),
        (trial_result.get("verifier") or {}).get("finished_at"),
    )
    return {
        "adapter": "harbor_result_adapter_v1",
        "source_job_dir": str(job_dir),
        "source_trial_dir": str(trial_dir),
        "task_name": trial_result.get("task_name") or trial_dir.name,
        "passed": passed,
        "final_status": final_status,
        "final_reward": reward,
        "attempt_count": 1,
        "status_trajectory": [final_status],
        "reward_trajectory": [reward],
        "failure_type": failure_type,
        "diagnosis": {
            "affected_rule_ids": affected_rule_ids,
            "patch_ready": bool(affected_rule_ids and not passed),
            "patch_hint": "Map affected_rule_ids to rule_ledger patches." if affected_rule_ids and not passed else "",
            "verifier_stdout": verifier_stdout.strip(),
        },
        "pdi": {
            "enabled": False,
            "observe_only": None,
            "method": None,
            "history_count": 0,
            "history": [],
        },
        "cost": {
            "input_tokens": (trial_result.get("agent_result") or {}).get("n_input_tokens"),
            "output_tokens": (trial_result.get("agent_result") or {}).get("n_output_tokens"),
            "skill_gen_calls": 0,
            "skill_gen_latency_s": 0,
            "agent_time_s": agent_time_s,
            "verifier_time_s": verifier_time_s,
            "total_time_s": total_time_s,
        },
        "events": {
            "event_count": 1,
            "execution_event_count": 1,
            "skill_gen_call_count": 0,
            "task_summary_count": 0,
        },
        "raw_files": {
            "job_result_json": str(job_dir / "result.json"),
            "trial_result_json": str(trial_dir / "result.json"),
            "verifier_stdout": str(verifier_stdout_path),
        },
    }


def render_report(report: dict[str, Any]) -> str:
    diagnosis = report["diagnosis"]
    cost = report["cost"]
    lines = [
        "# Harbor Result Adapter Report",
        "",
        "## Summary",
        "",
        f"- Task: {report['task_name']}",
        f"- Passed: {report['passed']}",
        f"- Final status: {report['final_status']}",
        f"- Final reward: {report['final_reward']}",
        f"- Failure type: {report['failure_type']}",
        f"- Affected rule IDs: {', '.join(diagnosis['affected_rule_ids']) if diagnosis['affected_rule_ids'] else 'none'}",
        f"- Patch ready: {diagnosis['patch_ready']}",
        "",
        "## Runtime",
        "",
        f"- Agent time seconds: {cost['agent_time_s']}",
        f"- Verifier time seconds: {cost['verifier_time_s']}",
        f"- Total time seconds: {cost['total_time_s']}",
        "",
        "## Verifier Output",
        "",
        "```text",
        diagnosis.get("verifier_stdout") or "",
        "```",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert a Harbor native job result into SPARK-compatible execution report format.")
    parser.add_argument("--job-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    report = convert_harbor_job(args.job_dir)
    write_json(args.output_dir / "execution_report_spark.json", report)
    write_text(args.output_dir / "harbor_adapter_report.md", render_report(report))
    print(json.dumps({"task_name": report["task_name"], "passed": report["passed"], "output_dir": str(args.output_dir)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
