from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = ROOT / "scripts"
SRC_ROOT = ROOT / "src"
for item in (SCRIPTS_ROOT, SRC_ROOT):
    if str(item) not in sys.path:
        sys.path.insert(0, str(item))

from skill_deployment.evidence import write_json, write_text  # noqa: E402

import run_swebench_gold_patch_smoke as gold_smoke  # noqa: E402
from run_external_swebench_smoke import (  # noqa: E402
    OUTPUT_ROOT,
    prediction_rows,
    run_wsl,
    shell_quote,
    swebench_python_command,
    windows_to_wsl_path,
    write_jsonl,
)


REPORT_PATH = ROOT / "reports" / "SWEBENCH_OFFICIAL_HARNESS_INFRA_UNBLOCK_STATUS.md"
FAILED_PACKAGE_URL = "https://repo.anaconda.com/pkgs/main/linux-64/libstdcxx-15.2.0-h39759b7_8.conda"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def classify_summary(summary: dict[str, Any] | None) -> str:
    if not summary:
        return "infra_blocked"
    status = str(summary.get("official_harness_gold_patch_smoke") or "")
    gold = dict(summary.get("gold_patch") or {})
    recorded = str(gold.get("recorded_result") or "")
    if status == "pass" or recorded == "resolved":
        return "official_harness_gold_patch_smoke=pass"
    if recorded == "unresolved":
        return "evaluation_failed"
    return "infra_blocked"


def diagnostics(run_dir: Path) -> dict[str, Any]:
    commands = {
        "docker_version": "docker version --format '{{json .}}'",
        "docker_info": "docker info --format '{{json .}}'",
        "docker_images_sweb": "docker image ls --format '{{.Repository}}:{{.Tag}} {{.ID}} {{.CreatedSince}}' | grep -E 'sweb|ubuntu' || true",
        "docker_pull_ubuntu_22_04": "timeout 240s docker pull ubuntu:22.04",
        "curl_repo_anaconda": "curl -I --max-time 30 https://repo.anaconda.com || true",
        "curl_failed_conda_package": f"curl -I --max-time 30 {FAILED_PACKAGE_URL} || true",
        "wsl_resolv_conf": "cat /etc/resolv.conf || true",
        "proxy_env": "env | grep -iE 'proxy|http_proxy|https_proxy' || true",
    }
    results = {name: run_wsl(command, timeout=300) for name, command in commands.items()}
    write_json(run_dir / "infra_unblock" / "diagnostics.json", results)
    return results


def run_gold_retry(*, run_id: str, instance_id: str, timeout_seconds: int, retry_wall_timeout_seconds: int) -> dict[str, Any]:
    run_dir = OUTPUT_ROOT / run_id
    official_dataset_path = run_dir / "official_dataset.json"
    instance, _resolved_dataset, _prepared = gold_smoke.load_or_fetch_instance(gold_smoke.DEFAULT_DATASET, instance_id)
    if not official_dataset_path.exists():
        write_json(official_dataset_path, [instance])
    predictions_path = run_dir / "predictions" / "gold_patch.jsonl"
    if not predictions_path.exists():
        write_jsonl(predictions_path, prediction_rows([instance], "gold_patch", model_patch_blocked=False))
    report_dir = run_dir / "evaluation" / "gold_patch" / "official_reports"
    official_run_id = f"{run_id}_gold_patch"
    official_timeout = min(timeout_seconds, retry_wall_timeout_seconds)
    command = " ".join(
        [
            shell_quote(swebench_python_command()),
            "-m swebench.harness.run_evaluation",
            "--dataset_name",
            shell_quote(windows_to_wsl_path(official_dataset_path)),
            "--split test",
            "--instance_ids",
            shell_quote(instance_id),
            "--predictions_path",
            shell_quote(windows_to_wsl_path(predictions_path)),
            "--max_workers 1",
            "--timeout",
            str(official_timeout),
            "--run_id",
            shell_quote(official_run_id),
            "--report_dir",
            shell_quote(windows_to_wsl_path(report_dir)),
            "--namespace none",
        ]
    )
    result = run_wsl(command, cwd=run_dir, timeout=retry_wall_timeout_seconds)
    result["official_command"] = command
    result["retry_wall_timeout_seconds"] = retry_wall_timeout_seconds
    result["official_timeout_seconds"] = official_timeout
    result["timestamp"] = utc_now()
    if "TimeoutExpired" in str(result.get("error", "")):
        run_wsl("pkill -f 'swebench.harness.run_evaluation' || true", timeout=30)
        result["cleanup"] = "attempted pkill for timed-out swebench.harness.run_evaluation"
    return result


def render_report(payload: dict[str, Any]) -> str:
    lines = [
        "# SWE-bench Official Harness Infra Unblock Status",
        "",
        f"Run id: `{payload['run_id']}`",
        f"Instance id: `{payload['instance_id']}`",
        f"Generated at: `{payload['generated_at']}`",
        "",
        "## Boundary",
        "",
        "- Official SWE-bench harness only.",
        "- Evaluation logic unchanged.",
        "- Gold patch unchanged.",
        "- No custom evaluator.",
        "- No skill_llm_patch attempt unless MODEL or OPENAI_MODEL is configured.",
        "",
        "## Diagnostics",
        "",
        f"- Diagnostics artifact: `{payload['diagnostics_path']}`",
        f"- Docker pull ubuntu status: `{payload['diagnostic_summary'].get('docker_pull_ubuntu_22_04')}`",
        f"- repo.anaconda HEAD status: `{payload['diagnostic_summary'].get('curl_repo_anaconda')}`",
        f"- failed package HEAD status: `{payload['diagnostic_summary'].get('curl_failed_conda_package')}`",
        "",
        "## Retry Attempts",
        "",
    ]
    if payload["retry_attempts"]:
        for attempt in payload["retry_attempts"]:
            lines.append(f"- attempt `{attempt['attempt_index']}`: return_code=`{attempt['result'].get('return_code')}`, status_after=`{attempt['status_after']}`")
    else:
        lines.append("- No retry was needed or allowed.")
    lines.extend(
        [
            "",
            "## Final Status",
            "",
            f"- `external_harness`: `{payload['final_status']}`",
            f"- `blocked_reason`: `{payload.get('blocked_reason')}`",
            f"- Updated summary: `{payload['summary_path']}`",
            "",
            "## Claim",
            "",
            "SWE-bench remains a software_patch_review harness-readiness lane only. It does not support secure_code_review claims.",
        ]
    )
    return "\n".join(lines) + "\n"


def diagnostic_status(result: dict[str, Any] | None) -> str:
    if not result:
        return "missing"
    if result.get("ok"):
        return "ok"
    return f"return_code_{result.get('return_code')}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Bounded SWE-bench official harness infrastructure unblock attempt.")
    parser.add_argument("--run-id", default="swebench_gold_patch_smoke_requests_20260612")
    parser.add_argument("--instance-id", default="psf__requests-1963")
    parser.add_argument("--max-retries", type=int, default=2)
    parser.add_argument("--timeout-seconds", type=int, default=1800)
    parser.add_argument("--retry-wall-timeout-seconds", type=int, default=180)
    args = parser.parse_args(argv)

    max_retries = max(0, min(int(args.max_retries), 2))
    run_dir = OUTPUT_ROOT / args.run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    diagnostics_payload = diagnostics(run_dir)

    retry_attempts: list[dict[str, Any]] = []
    summary_path = run_dir / "summary.json"
    summary = read_json(summary_path, {})
    status = classify_summary(summary)
    if status == "infra_blocked":
        for index in range(1, max_retries + 1):
            result = run_gold_retry(
                run_id=args.run_id,
                instance_id=args.instance_id,
                timeout_seconds=args.timeout_seconds,
                retry_wall_timeout_seconds=args.retry_wall_timeout_seconds,
            )
            summary = read_json(summary_path, {})
            status = classify_summary(summary)
            retry_attempts.append({"attempt_index": index, "result": result, "status_after": status})
            if status != "infra_blocked":
                break

    summary = read_json(summary_path, {})
    gold = dict(summary.get("gold_patch") or {})
    blocked_reason = gold.get("blocked_reason") or (gold.get("infra_error") or {}).get("reason")
    if status == "official_harness_gold_patch_smoke=pass":
        final_status = "pass"
    elif status == "evaluation_failed":
        final_status = "evaluation_failed"
    else:
        final_status = "infra_blocked"

    payload = {
        "run_id": args.run_id,
        "instance_id": args.instance_id,
        "generated_at": utc_now(),
        "max_retries": max_retries,
        "retry_attempts": retry_attempts,
        "diagnostics_path": str(run_dir / "infra_unblock" / "diagnostics.json"),
        "diagnostic_summary": {
            key: diagnostic_status(diagnostics_payload.get(key))
            for key in ("docker_pull_ubuntu_22_04", "curl_repo_anaconda", "curl_failed_conda_package")
        },
        "summary_path": str(summary_path),
        "final_status": final_status,
        "blocked_reason": blocked_reason,
        "evaluation_logic_changed": False,
        "dependency_fetch_mirror_changed": False,
        "skill_llm_patch_attempted": bool(os.environ.get("MODEL") or os.environ.get("OPENAI_MODEL")) and False,
        "claim_boundary": "SWE-bench harness readiness only; not secure_code_review evidence.",
    }
    if summary:
        summary["infra_unblock"] = payload
        write_json(summary_path, summary)
    write_json(run_dir / "infra_unblock" / "summary.json", payload)
    write_text(REPORT_PATH, render_report(payload))
    print(json.dumps({"report": str(REPORT_PATH), "final_status": final_status, "blocked_reason": blocked_reason}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
