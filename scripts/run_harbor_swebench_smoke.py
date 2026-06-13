from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from skill_deployment.evidence import write_json, write_text  # noqa: E402


OUTPUT_ROOT = ROOT / "outputs" / "harbor_swebench_smoke_001"
REPORT_PATH = ROOT / "reports" / "HARBOR_SWEBENCH_SMOKE_STATUS.md"
WSL_DISTRO = "Ubuntu-24.04-Codex"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path, default: Any | None = None) -> Any:
    if not path.exists():
        if default is not None:
            return default
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8-sig"))


def run_wsl(command: str, *, timeout: int = 60) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            ["wsl", "-d", WSL_DISTRO, "--", "bash", "-lc", command],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
        return {
            "command": command,
            "return_code": completed.returncode,
            "stdout": completed.stdout[-4000:],
            "stderr": completed.stderr[-4000:],
            "ok": completed.returncode == 0,
        }
    except Exception as exc:
        return {"command": command, "ok": False, "error": f"{type(exc).__name__}: {exc}"}


def render_report(summary: dict[str, Any]) -> str:
    lines = [
        "# Harbor SWE-bench Smoke Status",
        "",
        f"- Source run: `{summary['source_run']}`",
        f"- Status: `{summary['status']}`",
        f"- Instances mirrored: `{summary['instances_requested']}`",
        f"- Variants requested: `{', '.join(summary['variants_requested'])}`",
        "",
        "## Boundary",
        "",
        summary["boundary"],
        "",
    ]
    if summary.get("blocked_reason"):
        lines.extend(["## Blocked Reason", "", summary["blocked_reason"], ""])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Gate a narrow SWE-bench-to-Harbor smoke bridge.")
    parser.add_argument("--source-run", required=True)
    parser.add_argument("--instances", type=int, default=1)
    parser.add_argument("--variants", default="empty_patch,gold_patch")
    args = parser.parse_args(argv)

    source_dir = ROOT / "outputs" / "external_swebench" / args.source_run
    source_summary = read_json(source_dir / "run_summary.json", {})
    marginal = read_json(source_dir / "marginal_utility.json", {})
    variants = [item.strip() for item in args.variants.split(",") if item.strip()]
    docker = run_wsl("docker --version")
    harbor_src = run_wsl("test -d /opt/spark/harbor-src-locked")
    official_ready = bool(marginal.get("adapter_maturity_supported"))

    blocked_reason = None
    status = "ready_to_launch"
    if not source_summary:
        status = "blocked_source_run_missing"
        blocked_reason = f"Missing source run summary at {source_dir / 'run_summary.json'}."
    elif not official_ready:
        status = "blocked_source_official_smoke_incomplete"
        blocked_reason = "SWE-bench official smoke has not completed for all requested variants."
    elif not docker.get("ok"):
        status = "blocked_wsl_docker_unavailable"
        blocked_reason = "WSL Docker is unavailable."
    elif not harbor_src.get("ok"):
        status = "blocked_harbor_source_missing"
        blocked_reason = "Harbor locked source is missing inside WSL."
    else:
        status = "blocked_harbor_launcher_not_integrated"
        blocked_reason = "Harbor source and Docker are present, but this repo does not yet expose a SWE-bench Harbor launcher command."

    summary = {
        "run_id": "harbor_swebench_smoke_001",
        "created_at": utc_now(),
        "source_run": args.source_run,
        "source_dir": str(source_dir),
        "instances_requested": args.instances,
        "variants_requested": variants,
        "status": status,
        "blocked_reason": blocked_reason,
        "probes": {
            "docker": docker,
            "harbor_src": harbor_src,
            "source_summary_present": bool(source_summary),
            "source_adapter_maturity_supported": official_ready,
        },
        "boundary": "This bridge must not count plain Docker as Harbor. It only claims success after a Harbor launcher creates a task and captures verifier artifacts.",
    }
    write_json(OUTPUT_ROOT / "summary.json", summary)
    write_text(REPORT_PATH, render_report(summary))
    print(json.dumps({"output": str(OUTPUT_ROOT / "summary.json"), "status": status}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
