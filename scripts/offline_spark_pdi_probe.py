"""Offline probe for SPARK PDI history on released trajectory artifacts.

This script intentionally avoids Harbor/Docker execution. It reuses SPARK's
PDITracker against an existing attempts.json artifact so we can validate the
"execution feedback signal" interface before the full runtime is available.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


DEFAULT_REPO = Path(__file__).resolve().parents[1] / "external_repos" / "spark-skills"
DEFAULT_TASK = "3d-scan-calc"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Recompute SPARK PDI snapshots from attempts.json.")
    parser.add_argument("--repo", type=Path, default=DEFAULT_REPO, help="Path to the spark-skills repo.")
    parser.add_argument("--task", default=DEFAULT_TASK, help="Task name under all_model_pdi.")
    parser.add_argument("--method", choices=["token_overlap", "js_divergence"], default="token_overlap")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    return parser.parse_args()


def load_attempts(repo: Path, task: str) -> dict[str, Any]:
    path = repo / "spark_skills_gen" / "skills_gen_result" / "all_model_pdi" / task / "attempts.json"
    if not path.exists():
        raise FileNotFoundError(f"attempts.json not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def recompute(repo: Path, data: dict[str, Any], method: str) -> dict[str, Any]:
    sys.path.insert(0, str(repo))
    from spark_skills_gen.context import PDITracker  # noqa: PLC0415

    pdi_config = data.get("pdi", {})
    tracker = PDITracker(
        enabled=True,
        observe_only=bool(pdi_config.get("observe_only", False)),
        warmup=int(pdi_config.get("warmup", 2)),
        threshold=float(pdi_config.get("threshold", -0.5)),
        method=method,
    )

    attempts = data.get("attempts", [])
    memos = data.get("memo_history", []) + [data.get("exploration_memo", "")]
    prev_memo = ""
    prev_summary = ""

    snapshots: list[dict[str, Any]] = []
    for step, memo in enumerate(memos):
        if step >= len(attempts):
            break
        attempt = attempts[step]
        snapshot = tracker.compute(
            step=step,
            current_memo=memo,
            previous_memo=prev_memo,
            agent_commands=attempt.get("agent_commands", ""),
            test_summary=attempt.get("test_summary", ""),
            previous_test_summary=prev_summary,
        )
        snapshots.append(snapshot.to_dict())
        prev_memo = memo
        prev_summary = attempt.get("test_summary", "")

    final_attempt = attempts[-1] if attempts else {}
    triggers = [s for s in snapshots if s.get("triggered")]

    return {
        "task_name": data.get("task_name"),
        "attempt_count": len(attempts),
        "final_status": final_attempt.get("status"),
        "final_reward": final_attempt.get("reward"),
        "method": method,
        "stored_history_count": len(pdi_config.get("history", [])),
        "recomputed_history_count": len(snapshots),
        "trigger_count": len(triggers),
        "trigger_steps": [
            {"step": s["step"], "level": s["level"], "weighted_pdi": s["weighted_pdi"]}
            for s in triggers
        ],
        "snapshots": snapshots,
    }


def print_summary(result: dict[str, Any]) -> None:
    print(f"task: {result['task_name']}")
    print(
        "attempts: "
        f"{result['attempt_count']} final={result['final_status']} reward={result['final_reward']}"
    )
    print(
        "pdi history: "
        f"stored={result['stored_history_count']} recomputed={result['recomputed_history_count']}"
    )
    print(f"triggers: {result['trigger_count']}")
    for trigger in result["trigger_steps"]:
        print(
            "  "
            f"step={trigger['step']} level={trigger['level']} weighted_pdi={trigger['weighted_pdi']}"
        )
    print("snapshots:")
    for snapshot in result["snapshots"]:
        print(
            "  "
            f"step={snapshot['step']} exec={snapshot['proxy_exec']} "
            f"plan={snapshot['proxy_plan']} oss={snapshot['proxy_oss']} "
            f"weighted={snapshot['weighted_pdi']} triggered={snapshot['triggered']} "
            f"level={snapshot['level']}"
        )


def main() -> None:
    args = parse_args()
    data = load_attempts(args.repo.resolve(), args.task)
    result = recompute(args.repo.resolve(), data, args.method)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_summary(result)


if __name__ == "__main__":
    main()
