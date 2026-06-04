from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    if not path.exists():
        return events
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped:
            events.append(json.loads(stripped))
    return events


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def summarize_events(events: list[dict[str, Any]]) -> dict[str, Any]:
    execution_events = [event for event in events if event.get("type") == "execution_result"]
    skill_gen_events = [event for event in events if event.get("type") == "skill_gen_call"]
    task_summary_events = [event for event in events if event.get("type") == "task_summary"]
    total_input_tokens = sum(int(event.get("input_tokens") or 0) for event in skill_gen_events)
    total_output_tokens = sum(int(event.get("output_tokens") or 0) for event in skill_gen_events)
    total_skill_gen_latency_s = sum(float(event.get("latency_s") or 0) for event in skill_gen_events)
    return {
        "event_count": len(events),
        "execution_event_count": len(execution_events),
        "skill_gen_call_count": len(skill_gen_events),
        "task_summary_count": len(task_summary_events),
        "total_input_tokens": total_input_tokens,
        "total_output_tokens": total_output_tokens,
        "total_skill_gen_latency_s": round(total_skill_gen_latency_s, 3),
        "task_summary": task_summary_events[-1] if task_summary_events else None,
    }


def infer_failure_type(final_status: str, final_reward: float | None, events: list[dict[str, Any]]) -> str:
    if final_status == "PASS" or final_reward == 1.0:
        return "none"
    if any(event.get("error") for event in events):
        return "execution_error"
    if final_reward is not None and final_reward < 1.0:
        return "verifier_failure"
    return "unknown_failure"


def convert_task_dir(task_dir: Path) -> dict[str, Any]:
    attempts_path = task_dir / "attempts.json"
    trajectory_path = task_dir / "trajectory.jsonl"
    attempts_payload = read_json(attempts_path)
    events = read_jsonl(trajectory_path)
    event_summary = summarize_events(events)
    attempts = attempts_payload.get("attempts", [])
    final_attempt = attempts[-1] if attempts else {}
    final_status = str(final_attempt.get("status") or "UNKNOWN")
    final_reward = final_attempt.get("reward")
    task_summary = event_summary.get("task_summary") or {}
    total_time_s = task_summary.get("total_time_s")
    pdi_payload = attempts_payload.get("pdi") or {}
    pdi_history = pdi_payload.get("history") or []
    return {
        "adapter": "spark_artifact_adapter_v1",
        "source_task_dir": str(task_dir),
        "task_name": attempts_payload.get("task_name") or task_dir.name,
        "passed": final_status == "PASS" or final_reward == 1.0,
        "final_status": final_status,
        "final_reward": final_reward,
        "attempt_count": len(attempts),
        "status_trajectory": [attempt.get("status") for attempt in attempts],
        "reward_trajectory": [attempt.get("reward") for attempt in attempts],
        "failure_type": infer_failure_type(final_status, final_reward, events),
        "pdi": {
            "enabled": pdi_payload.get("enabled", False),
            "observe_only": pdi_payload.get("observe_only", None),
            "method": pdi_payload.get("method", None),
            "history_count": len(pdi_history),
            "history": pdi_history,
        },
        "cost": {
            "input_tokens": event_summary["total_input_tokens"],
            "output_tokens": event_summary["total_output_tokens"],
            "skill_gen_calls": event_summary["skill_gen_call_count"],
            "skill_gen_latency_s": event_summary["total_skill_gen_latency_s"],
            "total_time_s": total_time_s,
        },
        "events": {
            "event_count": event_summary["event_count"],
            "execution_event_count": event_summary["execution_event_count"],
            "skill_gen_call_count": event_summary["skill_gen_call_count"],
            "task_summary_count": event_summary["task_summary_count"],
        },
        "raw_files": {
            "attempts_json": str(attempts_path),
            "trajectory_jsonl": str(trajectory_path),
        },
    }


def render_report(report: dict[str, Any]) -> str:
    pdi = report["pdi"]
    cost = report["cost"]
    lines = [
        "# SPARK Adapter Report",
        "",
        "## Summary",
        "",
        f"- Task: {report['task_name']}",
        f"- Passed: {report['passed']}",
        f"- Final status: {report['final_status']}",
        f"- Final reward: {report['final_reward']}",
        f"- Attempts: {report['attempt_count']}",
        f"- Failure type: {report['failure_type']}",
        "",
        "## Cost And Runtime",
        "",
        f"- Skill generation calls: {cost['skill_gen_calls']}",
        f"- Input tokens: {cost['input_tokens']}",
        f"- Output tokens: {cost['output_tokens']}",
        f"- Skill generation latency seconds: {cost['skill_gen_latency_s']}",
        f"- Total task time seconds: {cost['total_time_s']}",
        "",
        "## PDI",
        "",
        f"- Enabled: {pdi['enabled']}",
        f"- Observe only: {pdi['observe_only']}",
        f"- Method: {pdi['method']}",
        f"- History count: {pdi['history_count']}",
        "",
        "## Interpretation",
        "",
    ]
    if report["passed"]:
        lines.append("This SPARK run provides a positive execution signal. It can be used as execution evidence, but it does not produce a repair patch because no failure was observed.")
    else:
        lines.append("This SPARK run provides a failure signal. The next step is to map `failure_type` and trajectory details to a rule-level patch.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert SPARK attempts/trajectory artifacts into the MVP execution_report format.")
    parser.add_argument("--task-dir", type=Path, required=True, help="Directory containing attempts.json and trajectory.jsonl.")
    parser.add_argument("--output-dir", type=Path, required=True, help="Directory where converted reports should be written.")
    args = parser.parse_args()

    report = convert_task_dir(args.task_dir)
    write_json(args.output_dir / "execution_report_spark.json", report)
    write_text(args.output_dir / "spark_adapter_report.md", render_report(report))
    print(json.dumps({"task_name": report["task_name"], "passed": report["passed"], "output_dir": str(args.output_dir)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
