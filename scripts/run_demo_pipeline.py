from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


OUTPUT_DIR = Path("outputs/demo_pipeline_check")


REQUIRED_RUNS = {
    "baseline_001": Path("outputs/mvp_vertical_slice/baseline_001"),
    "harbor_api_review_001": Path("outputs/mvp_vertical_slice/harbor_api_review_001"),
    "harbor_api_review_002": Path("outputs/mvp_vertical_slice/harbor_api_review_002"),
    "agent_mock_api_review_001": Path("outputs/mvp_vertical_slice/agent_mock_api_review_001"),
    "llm_agent_api_review_001": Path("outputs/mvp_vertical_slice/llm_agent_api_review_001"),
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def run_command(command: list[str]) -> dict[str, Any]:
    completed = subprocess.run(command, text=True, capture_output=True, check=False)
    return {
        "command": command,
        "returncode": completed.returncode,
        "stdout_tail": completed.stdout[-2000:],
        "stderr_tail": completed.stderr[-2000:],
    }


def status(name: str, state: str, message: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"name": name, "status": state, "message": message, "details": details or {}}


def check_baseline(run_dir: Path) -> dict[str, Any]:
    summary_path = run_dir / "comparison_summary.json"
    if not summary_path.exists():
        return status("baseline_001", "missing", "comparison_summary.json not found")
    rows = {row["variant"]: row for row in read_json(summary_path)}
    expected = {
        "no_skill": (False, ["R001", "R002", "R003", "R004", "R005", "R006"]),
        "full_skill": (True, []),
        "compact_skill_v1": (False, ["R005", "R006"]),
        "compact_skill_v2": (True, []),
    }
    failures: list[str] = []
    for variant, (passed, missed) in expected.items():
        row = rows.get(variant)
        if not row:
            failures.append(f"{variant} missing")
            continue
        if row.get("passed") != passed or row.get("missed_rules") != missed:
            failures.append(f"{variant} expected passed={passed}, missed={missed}; got {row}")
    return status("baseline_001", "ok" if not failures else "failed", "baseline comparison checked", {"failures": failures, "rows": rows})


def check_feedback_run(name: str, run_dir: Path) -> dict[str, Any]:
    gate_path = run_dir / "validation_gate.json"
    report_path = run_dir / "execution_report_spark.json"
    comparison_path = run_dir / "execution_report_comparison.json"
    missing = [str(path.name) for path in (gate_path, report_path) if not path.exists()]
    if missing:
        return status(name, "missing", f"missing artifacts: {', '.join(missing)}")
    gate = read_json(gate_path)
    report = read_json(report_path)
    comparison = read_json(comparison_path) if comparison_path.exists() else None
    ok = bool(gate.get("accepted")) and report.get("failure_type") == "missing_rule"
    if comparison is not None:
        ok = ok and comparison.get("passed") is True
    return status(
        name,
        "ok" if ok else "failed",
        "feedback run checked",
        {
            "failure_type": report.get("failure_type"),
            "affected_rule_ids": (report.get("diagnosis") or {}).get("affected_rule_ids"),
            "validation_gate_accepted": gate.get("accepted"),
            "comparison_passed": comparison.get("passed") if comparison else None,
        },
    )


def check_llm_run(run_dir: Path) -> dict[str, Any]:
    summary_path = run_dir / "summary.json"
    if not summary_path.exists():
        return status("llm_agent_api_review_001", "missing", "summary.json not found")
    summary = read_json(summary_path)
    if not summary.get("env_ready"):
        return status("llm_agent_api_review_001", "unavailable", "LLM endpoint was not configured when this run was generated", summary)
    runs = summary.get("runs") or []
    expected = {
        ("case001", "compact_v1"): False,
        ("case001", "compact_v2"): True,
        ("case002", "compact_v1"): False,
        ("case002", "compact_v2"): True,
    }
    failures: list[str] = []
    for run in runs:
        key = (run.get("case_id"), run.get("variant"))
        if key in expected and run.get("passed") != expected[key]:
            failures.append(f"{key} expected passed={expected[key]}, got {run.get('passed')}")
    return status(
        "llm_agent_api_review_001",
        "ok" if not failures else "failed",
        "LLM matrix checked",
        {"env_ready": summary.get("env_ready"), "model": summary.get("model"), "failures": failures},
    )


def check_existing() -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for name, path in REQUIRED_RUNS.items():
        if not path.exists():
            results.append(status(name, "missing", f"{path} not found"))
    if REQUIRED_RUNS["baseline_001"].exists():
        results.append(check_baseline(REQUIRED_RUNS["baseline_001"]))
    for name in ("harbor_api_review_001", "harbor_api_review_002", "agent_mock_api_review_001"):
        if REQUIRED_RUNS[name].exists():
            results.append(check_feedback_run(name, REQUIRED_RUNS[name]))
    if REQUIRED_RUNS["llm_agent_api_review_001"].exists():
        results.append(check_llm_run(REQUIRED_RUNS["llm_agent_api_review_001"]))
    return results


def rerun_light() -> list[dict[str, Any]]:
    commands = [
        [
            sys.executable,
            "scripts/run_mvp_vertical_slice.py",
            "--run-id",
            "baseline_001",
            "--created-at",
            "2026-06-03T18:06:09.686982+00:00",
        ],
        [
            sys.executable,
            "scripts/verify_api_review_json.py",
            "--review",
            "outputs/mvp_vertical_slice/agent_mock_api_review_001/review_v1.json",
            "--output",
            "outputs/agent-mock-smoke/verify_review_v1.json",
        ],
        [
            sys.executable,
            "scripts/verify_api_review_json.py",
            "--review",
            "outputs/mvp_vertical_slice/agent_mock_api_review_001/review_v2.json",
            "--output",
            "outputs/agent-mock-smoke/verify_review_v2.json",
        ],
    ]
    command_results = []
    for command in commands:
        result = run_command(command)
        if command[1].endswith("verify_api_review_json.py") and any("review_v1" in part for part in command):
            result["expected_nonzero"] = True
            result["accepted"] = result["returncode"] == 1
        else:
            result["accepted"] = result["returncode"] == 0
        command_results.append(result)
    return [status("rerun_light", "ok" if all(row["accepted"] for row in command_results) else "failed", "light rerun finished", {"commands": command_results})]


def rerun_heavy() -> list[dict[str, Any]]:
    env_ready = all(os.environ.get(name) for name in ("OPENAI_BASE_URL", "OPENAI_API_KEY", "MODEL"))
    if not env_ready:
        return [status("rerun_heavy", "unavailable", "LLM endpoint env vars are not fully configured; Harbor reruns are intentionally not automatic.")]
    result = run_command(
        [
            sys.executable,
            "scripts/run_llm_agent_api_review_matrix.py",
            "--output-dir",
            "outputs/mvp_vertical_slice/llm_agent_api_review_001",
            "--created-at",
            datetime.now(timezone.utc).isoformat(),
        ]
    )
    return [status("rerun_heavy", "ok" if result["returncode"] == 0 else "failed", "LLM matrix rerun attempted; Harbor heavy reruns remain manual", result)]


def render_summary(results: list[dict[str, Any]], mode: str) -> str:
    lines = [
        "# Demo Pipeline Check",
        "",
        f"- Mode: `{mode}`",
        f"- Generated at: `{datetime.now(timezone.utc).isoformat()}`",
        "",
        "| Item | Status | Message |",
        "|---|---|---|",
    ]
    for row in results:
        lines.append(f"| {row['name']} | {row['status']} | {row['message']} |")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- This script checks or lightly reruns demo artifacts.",
            "- It never writes API keys to files.",
            "- Heavy Harbor and LLM reruns are opt-in; unavailable endpoints are marked rather than faked.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Check or lightly rerun the expert skill distillation demo pipeline.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check-existing", action="store_true")
    group.add_argument("--rerun-light", action="store_true")
    group.add_argument("--rerun-heavy", action="store_true")
    args = parser.parse_args()

    mode = "check-existing" if args.check_existing else "rerun-light" if args.rerun_light else "rerun-heavy"
    results = []
    if args.rerun_light:
        results.extend(rerun_light())
    elif args.rerun_heavy:
        results.extend(rerun_heavy())
    results.extend(check_existing())
    summary = {
        "mode": mode,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "results": results,
        "overall_status": "ok" if all(row["status"] in {"ok", "unavailable"} for row in results) else "failed",
    }
    write_json(OUTPUT_DIR / "summary.json", summary)
    write_text(OUTPUT_DIR / "summary.md", render_summary(results, mode))
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["overall_status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
