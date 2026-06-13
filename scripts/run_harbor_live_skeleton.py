from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from skill_deployment import ExecutionReport, select_controlled_task_cases, verify_controlled_execution, write_evidence_bundle  # noqa: E402
from skill_deployment.evidence import write_json, write_text  # noqa: E402


DATA_ROOT = ROOT / "data" / "task_cases"
OUTPUT_ROOT = ROOT / "outputs" / "harbor_live_skeleton_upload_001"


def probe_command(command: list[str]) -> dict[str, Any]:
    try:
        completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=20, check=False)
        return {
            "command": command,
            "available": completed.returncode == 0,
            "return_code": completed.returncode,
            "stdout": completed.stdout[-2000:],
            "stderr": completed.stderr[-2000:],
        }
    except Exception as exc:  # pragma: no cover - environment dependent
        return {"command": command, "available": False, "error": f"{type(exc).__name__}: {exc}"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write a P0 Harbor live-runner skeleton evidence bundle.")
    parser.add_argument("--case", default="upload_security_001")
    parser.add_argument("--output-dir", default=str(OUTPUT_ROOT))
    args = parser.parse_args(argv)
    case = select_controlled_task_cases(DATA_ROOT, args.case)[0]
    out_dir = Path(args.output_dir)
    probes = {
        "docker": probe_command(["docker", "--version"]),
        "wsl": probe_command(["wsl", "--status"]),
    }
    live_ready = bool(probes["docker"].get("available"))
    report = ExecutionReport(
        attempt="harbor_live_skeleton",
        backend="harbor_live_skeleton",
        findings=(),
        notes=(
            "P0 skeleton only; this does not replace replay evidence.",
            "Live Harbor run is ready only if Docker/Harbor task launcher is available.",
        ),
    )
    verifier = verify_controlled_execution(case.expected_capabilities, report, target_text=case.target_asset)
    qualification = {
        "decision": "not_promoted",
        "reason": "P0 Harbor skeleton records environment readiness and evidence schema only.",
        "live_ready": live_ready,
        "boundary": "not a successful Harbor LLM repair loop",
    }
    write_evidence_bundle(
        out_dir / "evidence_bundle",
        case_id=case.case_id,
        backend="harbor_live_skeleton",
        variant="harbor_live_skeleton",
        target_text=case.target_asset,
        skill=None,
        skill_text="",
        execution=report,
        verifier=verifier,
        patch={"repair_action": "not_attempted", "reason": "skeleton_only"},
        qualification=qualification,
        status="live_ready" if live_ready else "environment_unavailable",
    )
    summary = {
        "run_id": "harbor_live_skeleton_upload_001",
        "case_id": case.case_id,
        "live_ready": live_ready,
        "probes": probes,
        "evidence_bundle": str(out_dir / "evidence_bundle"),
        "boundary": "P0 skeleton; failure/unavailability is valid evidence and is not hidden.",
    }
    write_json(out_dir / "summary.json", summary)
    write_text(
        out_dir / "summary.md",
        "\n".join(
            [
                "# Harbor Live Runner Skeleton",
                "",
                f"- Case: `{case.case_id}`",
                f"- Live ready: `{live_ready}`",
                "- Boundary: P0 skeleton only; does not replace replay-backed Harbor evidence.",
                "",
            ]
        ),
    )
    print(json.dumps({"output": str(out_dir / "summary.json"), "live_ready": live_ready}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
