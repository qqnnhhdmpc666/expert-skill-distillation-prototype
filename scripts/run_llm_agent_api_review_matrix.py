from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CASES = {
    "case001": Path("data/harbor_api_review_tasks/api-review-001-compact-v1/case_001_openapi.md"),
    "case002": Path("data/harbor_api_review_tasks/api-review-002-compact-v1/case_002_openapi.md"),
}

SKILLS = {
    "compact_v1": Path("outputs/mvp_vertical_slice/baseline_001/compact_skill_v1.md"),
    "compact_v2": Path("outputs/mvp_vertical_slice/harbor_api_review_002/compact_skill_v2.md"),
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, text=True, capture_output=True, check=False)


def run_case(case_id: str, variant: str, output_dir: Path) -> dict[str, Any]:
    run_dir = output_dir / f"{case_id}_{variant}"
    review_path = run_dir / "review.json"
    diagnostic_path = run_dir / "llm_agent_diagnostic.json"
    verify_path = run_dir / "verification_result.json"
    agent_cmd = [
        sys.executable,
        "agents/api_review_llm_agent.py",
        "--skill",
        str(SKILLS[variant]),
        "--case",
        str(CASES[case_id]),
        "--output",
        str(review_path),
        "--diagnostic",
        str(diagnostic_path),
    ]
    agent_result = run_command(agent_cmd)
    verification: dict[str, Any] | None = None
    if review_path.exists():
        verify_cmd = [
            sys.executable,
            "scripts/verify_api_review_json.py",
            "--review",
            str(review_path),
            "--output",
            str(verify_path),
        ]
        run_command(verify_cmd)
        if verify_path.exists():
            verification = read_json(verify_path)
    diagnostic = read_json(diagnostic_path) if diagnostic_path.exists() else {"status": "missing_diagnostic"}
    return {
        "case_id": case_id,
        "variant": variant,
        "skill": str(SKILLS[variant]),
        "case": str(CASES[case_id]),
        "review": str(review_path) if review_path.exists() else None,
        "diagnostic": str(diagnostic_path),
        "verification": str(verify_path) if verify_path.exists() else None,
        "agent_exit_code": agent_result.returncode,
        "agent_status": diagnostic.get("status"),
        "passed": verification.get("passed") if verification else None,
        "reward": verification.get("reward") if verification else None,
        "failure_type": verification.get("failure_type") if verification else diagnostic.get("status"),
        "rule_ids": diagnostic.get("rule_ids", []),
        "message": verification.get("message") if verification else diagnostic.get("reason") or diagnostic.get("error"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the OpenAI-compatible API review agent on a small case/skill matrix.")
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/mvp_vertical_slice/llm_agent_api_review_001"))
    parser.add_argument("--created-at", default=None)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    runs = [run_case(case_id, variant, args.output_dir) for case_id in CASES for variant in SKILLS]
    env_ready = all(os.environ.get(name) for name in ("OPENAI_BASE_URL", "OPENAI_API_KEY", "MODEL"))
    summary = {
        "run_id": args.output_dir.name,
        "created_at": args.created_at or datetime.now(timezone.utc).isoformat(),
        "layer": "openai_compatible_llm_agent_external",
        "env_ready": env_ready,
        "base_url": os.environ.get("OPENAI_BASE_URL"),
        "model": os.environ.get("MODEL"),
        "boundary": "This layer validates the real/OpenAI-compatible LLM interface and skill-conditioned output when credentials are configured. It is not the two-week demo's only success path.",
        "runs": runs,
    }
    write_json(args.output_dir / "summary.json", summary)
    write_json(
        args.output_dir / "manifest.json",
        {
            "run_id": args.output_dir.name,
            "created_at": summary["created_at"],
            "artifacts": ["summary.json"] + [
                artifact
                for run in runs
                for artifact in [run["review"], run["diagnostic"], run["verification"]]
                if artifact
            ],
            "note": "External LLM-agent matrix. If env_ready is false, diagnostics are skipped placeholders.",
        },
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if env_ready else 2


if __name__ == "__main__":
    raise SystemExit(main())
