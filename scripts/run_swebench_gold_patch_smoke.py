from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from skill_deployment.evidence import write_json, write_text  # noqa: E402

from run_external_swebench_smoke import (  # noqa: E402
    OUTPUT_ROOT,
    WSL_DISTRO,
    check_wsl_environment,
    fetch_hf_rows,
    prediction_rows,
    read_json,
    read_official_report,
    run_wsl,
    select_instances,
    shell_quote,
    swebench_python_command,
    windows_to_wsl_path,
    write_jsonl,
)


REPORT_PATH = ROOT / "reports" / "SWEBENCH_OFFICIAL_HARNESS_GOLD_PATCH_SMOKE_STATUS.md"
DEFAULT_RUN_ID = "swebench_gold_patch_smoke_20260612"
DEFAULT_INSTANCE_ID = "astropy__astropy-12907"
DEFAULT_DATASET = "SWE-bench/SWE-bench_Lite"
DATASET_SOURCE = "https://huggingface.co/datasets/SWE-bench/SWE-bench_Lite"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_text(value: str) -> str:
    import hashlib

    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def load_or_fetch_instance(dataset: str, instance_id: str) -> tuple[dict[str, Any], str, str | None]:
    latest_path = OUTPUT_ROOT / "latest_prepare.json"
    if latest_path.exists():
        latest = read_json(latest_path)
        prepared_path = Path(str(latest.get("instances_path", "")))
        if prepared_path.exists():
            payload = read_json(prepared_path)
            for instance in payload.get("instances", []):
                if instance.get("instance_id") == instance_id:
                    return instance, str(payload.get("resolved_dataset") or dataset), str(prepared_path)

    rows, resolved_dataset, _errors = fetch_hf_rows(dataset, length=100)
    for instance in select_instances(rows, limit=100):
        if instance.get("instance_id") == instance_id:
            return instance, resolved_dataset, None
    for offset in range(0, 500, 100):
        params = urllib.parse.urlencode(
            {
                "dataset": dataset,
                "config": "default",
                "split": "test",
                "offset": offset,
                "length": 100,
            }
        )
        url = f"https://datasets-server.huggingface.co/rows?{params}"
        with urllib.request.urlopen(url, timeout=60) as response:
            payload = json.loads(response.read().decode("utf-8"))
        page_rows = [dict(item.get("row", {})) for item in payload.get("rows", []) if item.get("row")]
        for row in page_rows:
            if row.get("instance_id") == instance_id:
                return select_instances([row], limit=1)[0], dataset, None
        if len(page_rows) < 100:
            break
    raise ValueError(f"instance_id not found in {dataset}: {instance_id}")


def instance_metadata(instance: dict[str, Any], *, dataset: str, resolved_dataset: str, official_dataset_path: Path) -> dict[str, Any]:
    return {
        "instance_id": instance["instance_id"],
        "repo": instance.get("repo"),
        "base_commit": instance.get("base_commit"),
        "problem_statement_hash": sha256_text(str(instance.get("problem_statement") or "")),
        "gold_patch_hash": sha256_text(str(instance.get("patch") or "")),
        "test_patch_hash": sha256_text(str(instance.get("test_patch") or "")) if instance.get("test_patch") is not None else None,
        "dataset": dataset,
        "resolved_dataset": resolved_dataset,
        "dataset_source": DATASET_SOURCE,
        "official_dataset_json": str(official_dataset_path),
    }


def probe_docker(run_dir: Path, *, attempt_mirrors: bool) -> dict[str, Any]:
    previous = read_json(run_dir / "docker_status.json", {}) if (run_dir / "docker_status.json").exists() else {}
    probes: dict[str, Any] = {
        "wsl_distro": WSL_DISTRO,
        "created_at": utc_now(),
        "docker_version": run_wsl("docker version --format '{{json .}}'", timeout=60),
        "docker_info": run_wsl("docker info --format '{{json .RegistryConfig.Mirrors}}'", timeout=60),
        "docker_hub_v2": run_wsl("curl -I --max-time 20 https://registry-1.docker.io/v2/ || true", timeout=40),
        "existing_ubuntu_22_04": run_wsl("docker image inspect ubuntu:22.04 >/dev/null 2>&1", timeout=30),
        "pull_attempts": [],
    }

    if probes["existing_ubuntu_22_04"].get("ok"):
        probes["ubuntu_22_04_ready"] = True
        probes["ubuntu_22_04_source"] = previous.get("ubuntu_22_04_source") or "existing_local_image"
        write_json(run_dir / "docker_status.json", probes)
        return probes

    direct = "timeout 240s docker pull ubuntu:22.04"
    direct_result = run_wsl(direct, timeout=270)
    probes["pull_attempts"].append({"source": "docker_hub", "command": direct, "result": direct_result})
    if direct_result.get("ok"):
        probes["ubuntu_22_04_ready"] = True
        probes["ubuntu_22_04_source"] = "docker_hub"
        write_json(run_dir / "docker_status.json", probes)
        return probes

    probes["ubuntu_22_04_ready"] = False
    probes["ubuntu_22_04_source"] = None
    if attempt_mirrors:
        mirrors = [
            "public.ecr.aws/ubuntu/ubuntu:22.04",
            "docker.m.daocloud.io/library/ubuntu:22.04",
            "docker.1ms.run/library/ubuntu:22.04",
        ]
        for source in mirrors:
            pull = f"timeout 240s docker pull {shell_quote(source)}"
            pull_result = run_wsl(pull, timeout=270)
            tag_result = None
            if pull_result.get("ok"):
                tag_cmd = f"docker tag {shell_quote(source)} ubuntu:22.04"
                tag_result = run_wsl(tag_cmd, timeout=60)
                if tag_result.get("ok"):
                    probes["ubuntu_22_04_ready"] = True
                    probes["ubuntu_22_04_source"] = source
                    probes["pull_attempts"].append({"source": source, "command": pull, "result": pull_result, "tag_result": tag_result})
                    break
            probes["pull_attempts"].append({"source": source, "command": pull, "result": pull_result, "tag_result": tag_result})

    write_json(run_dir / "docker_status.json", probes)
    return probes


def classify_docker_block(command_result: dict[str, Any], docker_status: dict[str, Any]) -> tuple[str | None, str | None]:
    text = f"{command_result.get('stdout', '')}\n{command_result.get('stderr', '')}"
    if "registry-1.docker.io" in text and ("i/o timeout" in text or "connection refused" in text):
        return "infra_blocked", "Docker registry access failed while resolving ubuntu:22.04 or SWE-bench images."
    if not docker_status.get("ubuntu_22_04_ready") and docker_status.get("pull_attempts"):
        return "infra_blocked", "ubuntu:22.04 could not be pulled or preloaded before official harness execution."
    return None, None


def read_tail(path: Path, max_chars: int = 2500) -> str | None:
    if not path.exists():
        return None
    try:
        return path.read_text(encoding="utf-8", errors="replace")[-max_chars:]
    except Exception:
        return None


def collect_infra_error(run_dir: Path, official_run_id: str, variant: str, instance_id: str) -> dict[str, Any]:
    run_log = run_dir / "logs" / "run_evaluation" / official_run_id / variant / instance_id / "run_instance.log"
    build_logs = sorted((run_dir / "logs" / "build_images").glob("**/build_image.log"), key=lambda item: item.stat().st_mtime)
    build_log = build_logs[-1] if build_logs else None
    run_tail = read_tail(run_log)
    build_tail = read_tail(build_log, max_chars=6000) if build_log else None
    run_text = run_log.read_text(encoding="utf-8", errors="replace") if run_log.exists() else ""
    build_text = build_log.read_text(encoding="utf-8", errors="replace") if build_log else ""
    combined = f"{run_text}\n{build_text}"
    if "Downloaded bytes did not match Content-Length" in combined and "repo.anaconda.com" in combined:
        reason = "Official harness environment-image build failed during conda package download from repo.anaconda.com: Content-Length mismatch after network timeout."
    elif "ReadTimeoutError" in combined and "repo.anaconda.com" in combined:
        reason = "Official harness environment-image build failed during conda package download from repo.anaconda.com: read timeout."
    elif "RPC failed" in combined and "early EOF" in combined and "git clone" in combined:
        reason = "Official harness instance-image build failed while cloning the target GitHub repository: RPC failed / early EOF."
    elif "setup_env.sh" in combined and "returned a non-zero code" in combined:
        reason = "Official harness environment-image build failed while running setup_env.sh."
    elif "registry-1.docker.io" in combined:
        reason = "Official harness Docker image resolution failed against Docker Hub."
    elif combined:
        reason = "Official harness reported an infrastructure error; see captured log tails."
    else:
        reason = "Official harness reported an infrastructure error but no detailed log was found."
    return {
        "reason": reason,
        "run_instance_log": str(run_log) if run_log.exists() else None,
        "build_image_log": str(build_log) if build_log else None,
        "run_instance_tail": run_tail,
        "build_image_tail": build_tail,
    }


def run_official_variant(
    run_dir: Path,
    variant: str,
    instance: dict[str, Any],
    official_dataset_path: Path,
    docker_status: dict[str, Any],
    *,
    max_workers: int,
    timeout_seconds: int,
) -> dict[str, Any]:
    rows = prediction_rows([instance], variant, model_patch_blocked=False)
    predictions_path = run_dir / "predictions" / f"{variant}.jsonl"
    write_jsonl(predictions_path, rows)

    env = check_wsl_environment()
    report_dir = run_dir / "evaluation" / variant / "official_reports"
    official_run_id = f"{run_dir.name}_{variant}"
    result_path = run_dir / "evaluation" / variant / "results.json"

    if not env["docker_available"]:
        result = {
            "variant": variant,
            "status": "infra_blocked",
            "recorded_result": "infra_failed",
            "blocked_reason": "Docker daemon is not available in WSL.",
            "environment": env,
        }
        write_json(result_path, result)
        return result
    if not env["official_harness_available"]:
        result = {
            "variant": variant,
            "status": "infra_blocked",
            "recorded_result": "infra_failed",
            "blocked_reason": "Official SWE-bench Python package is not installed in the configured WSL venv.",
            "environment": env,
        }
        write_json(result_path, result)
        return result

    command = " ".join(
        [
            shell_quote(swebench_python_command()),
            "-m swebench.harness.run_evaluation",
            "--dataset_name",
            shell_quote(windows_to_wsl_path(official_dataset_path)),
            "--split test",
            "--instance_ids",
            shell_quote(str(instance["instance_id"])),
            "--predictions_path",
            shell_quote(windows_to_wsl_path(predictions_path)),
            "--max_workers",
            str(max_workers),
            "--timeout",
            str(timeout_seconds),
            "--run_id",
            shell_quote(official_run_id),
            "--report_dir",
            shell_quote(windows_to_wsl_path(report_dir)),
            "--namespace",
            "none",
        ]
    )
    completed = run_wsl(command, cwd=run_dir, timeout=timeout_seconds + 3600)
    official_report = read_official_report([report_dir, run_dir], variant, official_run_id) if completed.get("ok") else None
    report_payload = official_report["payload"] if official_report else {}

    if completed.get("ok") and official_report:
        completed_instances = int(report_payload.get("completed_instances") or 0)
        resolved_instances = int(report_payload.get("resolved_instances") or 0)
        empty_patch_instances = int(report_payload.get("empty_patch_instances") or 0)
        error_instances = int(report_payload.get("error_instances") or 0)
        blocked_reason = None
        if empty_patch_instances == 1 and completed_instances == 0:
            status = "empty_patch_skipped_by_official_harness"
            recorded_result = "empty_patch_skipped_by_official_harness"
        elif error_instances > 0 and completed_instances == 0:
            status = "official_harness_infra_failed"
            recorded_result = "infra_failed"
            infra_error = collect_infra_error(run_dir, official_run_id, variant, str(instance["instance_id"]))
            blocked_reason = infra_error["reason"]
        elif resolved_instances > 0:
            status = "completed"
            recorded_result = "resolved"
        elif completed_instances > 0:
            status = "completed"
            recorded_result = "unresolved"
        else:
            status = "official_harness_inconclusive"
            recorded_result = "infra_failed"
            blocked_reason = "Official harness produced no completed, resolved, or empty-patch outcome."
    else:
        blocked_status, blocked_reason = classify_docker_block(completed, docker_status)
        if blocked_status:
            status = blocked_status
            recorded_result = "infra_failed"
        elif not completed.get("ok"):
            status = "official_harness_failed"
            recorded_result = "infra_failed"
            blocked_reason = "Official harness exited non-zero before producing a complete report."
        else:
            status = "official_harness_inconclusive"
            recorded_result = "infra_failed"
            blocked_reason = "Official harness exited zero but did not produce a readable official report."
    infra_error = None
    if recorded_result == "infra_failed":
        infra_error = collect_infra_error(run_dir, official_run_id, variant, str(instance["instance_id"]))
        if infra_error.get("reason") and not blocked_reason:
            blocked_reason = infra_error["reason"]

    result = {
        "variant": variant,
        "status": status,
        "recorded_result": recorded_result,
        "official_harness": True,
        "official_harness_call_path": f"{swebench_python_command()} -m swebench.harness.run_evaluation",
        "official_command": command,
        "command_result": completed,
        "official_report": official_report,
        "resolved_count": report_payload.get("resolved_instances"),
        "completed_instances": report_payload.get("completed_instances"),
        "error_instances": report_payload.get("error_instances"),
        "empty_patch_instances": report_payload.get("empty_patch_instances"),
        "prediction_path": str(predictions_path),
        "environment": env,
        "blocked_reason": blocked_reason,
        "infra_error": infra_error,
    }
    write_json(result_path, result)
    return result


def render_report(payload: dict[str, Any]) -> str:
    metadata = payload["instance_metadata"]
    docker_status = payload["docker_status"]
    gold = payload["gold_patch"]
    empty = payload["empty_patch"]
    skill = payload["skill_llm_patch"]
    attempt_mirrors = " --attempt-mirrors" if payload.get("attempt_mirrors") else ""
    gold_infra = gold.get("infra_error") or {}
    lines = [
        "# SWE-bench Official Harness Gold-Patch Smoke Status",
        "",
        f"Date: 2026-06-12",
        f"Run id: `{payload['run_id']}`",
        "",
        "## Boundary",
        "",
        "- Official SWE-bench harness only",
        "- One fixed SWE-bench Lite instance",
        "- No custom evaluator",
        "- No Harbor bridge",
        "- No `skill_llm_patch` attempt without model env",
        "",
        "## Fresh Commands",
        "",
        "```powershell",
        f"skill-deploy external-swebench gold-smoke --run-id {payload['run_id']} --instance-id {metadata['instance_id']} --backend official_docker{attempt_mirrors}",
        "```",
        "",
        "Official harness call path:",
        "",
        f"`{gold['official_harness_call_path']}`",
        "",
        "## Dataset Instance Metadata",
        "",
        f"- `instance_id`: `{metadata['instance_id']}`",
        f"- `repo`: `{metadata['repo']}`",
        f"- `base_commit`: `{metadata['base_commit']}`",
        f"- `problem_statement_hash`: `{metadata['problem_statement_hash']}`",
        f"- `gold_patch_hash`: `{metadata['gold_patch_hash']}`",
        f"- `test_patch_hash`: `{metadata['test_patch_hash']}`",
        f"- `dataset_source`: `{metadata['dataset_source']}`",
        f"- `official_dataset.json`: `{metadata['official_dataset_json']}`",
        "",
        "## Docker / Image Status",
        "",
        f"- WSL distro: `{docker_status.get('wsl_distro')}`",
        f"- Docker available: `{docker_status.get('docker_version', {}).get('ok')}`",
        f"- Registry mirrors: `{docker_status.get('docker_info', {}).get('stdout', '').strip()}`",
        f"- `ubuntu:22.04` ready: `{docker_status.get('ubuntu_22_04_ready')}`",
        f"- `ubuntu:22.04` source: `{docker_status.get('ubuntu_22_04_source')}`",
        f"- Docker status artifact: `{payload['docker_status_path']}`",
        "",
        "Docker pull attempts:",
        "",
    ]
    for attempt in docker_status.get("pull_attempts", []):
        result = attempt.get("result", {})
        source = attempt.get("source")
        command = attempt.get("command")
        ok = result.get("ok")
        return_code = result.get("return_code")
        stderr_tail = (result.get("stderr") or result.get("stdout") or "").strip().splitlines()
        error_line = stderr_tail[-1] if stderr_tail else ""
        lines.append(f"- `{source}`: ok=`{ok}`, return_code=`{return_code}`, command=`{command}`, last_log=`{error_line}`")
    if not docker_status.get("pull_attempts"):
        lines.append("- No pull attempt was needed because `ubuntu:22.04` already existed locally.")
    lines.extend(
        [
            "",
            "Gold official command:",
            "",
            "```text",
            gold.get("official_command") or "",
            "```",
            "",
        "## Results",
        "",
        f"- `gold_patch`: `{gold['recorded_result']}` (`{gold['status']}`)",
        f"- `empty_patch`: `{empty['recorded_result']}` (`{empty['status']}`)",
        f"- `skill_llm_patch`: `{skill['status']}`",
        "",
        "## Gold-Patch Detail",
        "",
        f"- Official report: `{(gold.get('official_report') or {}).get('path')}`",
        f"- Result artifact: `{payload['gold_result_path']}`",
        f"- Blocked reason: `{gold.get('blocked_reason')}`",
        f"- Run-instance log: `{gold_infra.get('run_instance_log')}`",
        f"- Build-image log: `{gold_infra.get('build_image_log')}`",
        "",
        "## Empty-Patch Detail",
        "",
        "`empty_patch` is recorded as `empty_patch_skipped_by_official_harness` when the official harness skips empty predictions. This is a harness baseline behavior, not a model or Skill failure.",
        "",
        "## Skill-LLM Patch Status",
        "",
        f"`skill_llm_patch` is `{skill['status']}`. Reason: {skill['blocked_reason']}",
        "",
        "## Claim",
        "",
        f"- `official_harness_gold_patch_smoke`: `{payload['official_harness_gold_patch_smoke']}`",
        "- `software_patch_review` external effectiveness: `not_claimed`",
        "",
        "## Remaining Gap",
        "",
        ]
    )
    if payload["official_harness_gold_patch_smoke"] == "pass":
        lines.append("- Next gap: run a non-oracle `skill_llm_patch` only after model env is explicitly configured.")
    else:
        lines.append("- Resolve the recorded infrastructure blocker, then rerun this exact one-instance gold-patch smoke.")
    return "\n".join(lines) + "\n"


def run_gold_smoke(args: argparse.Namespace) -> int:
    run_dir = OUTPUT_ROOT / args.run_id
    instance, resolved_dataset, prepared_path = load_or_fetch_instance(args.dataset, args.instance_id)
    official_dataset_path = run_dir / "official_dataset.json"
    write_json(official_dataset_path, [instance])
    metadata = instance_metadata(
        instance,
        dataset=args.dataset,
        resolved_dataset=resolved_dataset,
        official_dataset_path=official_dataset_path,
    )
    metadata["prepared_instances_path"] = prepared_path
    write_json(run_dir / "instance_metadata.json", metadata)

    docker_status = probe_docker(run_dir, attempt_mirrors=args.attempt_mirrors)
    empty = run_official_variant(
        run_dir,
        "empty_patch",
        instance,
        official_dataset_path,
        docker_status,
        max_workers=args.max_workers,
        timeout_seconds=args.timeout_seconds,
    )
    gold = run_official_variant(
        run_dir,
        "gold_patch",
        instance,
        official_dataset_path,
        docker_status,
        max_workers=args.max_workers,
        timeout_seconds=args.timeout_seconds,
    )
    skill = {
        "variant": "skill_llm_patch",
        "status": "blocked_by_missing_model_env",
        "blocked_reason": "MODEL or OPENAI_MODEL is not configured for a non-oracle SWE-bench patch attempt.",
    }
    if os.environ.get("MODEL") or os.environ.get("OPENAI_MODEL"):
        skill["status"] = "not_run_by_p0_h_scope"
        skill["blocked_reason"] = "P0-H intentionally does not run skill_llm_patch; this smoke only proves gold-patch official harness execution."
    write_json(run_dir / "evaluation" / "skill_llm_patch" / "results.json", skill)

    official_pass = "pass" if gold.get("recorded_result") == "resolved" else "infra_blocked"
    if gold.get("recorded_result") == "unresolved":
        official_pass = "ran_unresolved"
    payload = {
        "run_id": args.run_id,
        "created_at": utc_now(),
        "instance_metadata": metadata,
        "docker_status": docker_status,
        "docker_status_path": str(run_dir / "docker_status.json"),
        "empty_patch": empty,
        "gold_patch": gold,
        "skill_llm_patch": skill,
        "gold_result_path": str(run_dir / "evaluation" / "gold_patch" / "results.json"),
        "official_harness_gold_patch_smoke": official_pass,
        "attempt_mirrors": args.attempt_mirrors,
        "boundary": "P0-H one-instance official SWE-bench gold-patch smoke; no custom evaluator and no external effectiveness claim.",
    }
    write_json(run_dir / "summary.json", payload)
    write_text(REPORT_PATH, render_report(payload))
    print(
        json.dumps(
            {
                "summary": str(run_dir / "summary.json"),
                "report": str(REPORT_PATH),
                "official_harness_gold_patch_smoke": official_pass,
                "gold_patch": gold.get("recorded_result"),
                "empty_patch": empty.get("recorded_result"),
                "skill_llm_patch": skill.get("status"),
            },
            indent=2,
        )
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="P0-H one-instance SWE-bench official gold-patch smoke.")
    parser.add_argument("--run-id", default=DEFAULT_RUN_ID)
    parser.add_argument("--dataset", default=DEFAULT_DATASET)
    parser.add_argument("--instance-id", default=DEFAULT_INSTANCE_ID)
    parser.add_argument("--backend", default="official_docker")
    parser.add_argument("--max-workers", type=int, default=1)
    parser.add_argument("--timeout-seconds", type=int, default=1800)
    parser.add_argument("--attempt-mirrors", action="store_true")
    args = parser.parse_args(argv)
    if args.backend != "official_docker":
        raise SystemExit(f"unsupported backend for P0-H: {args.backend}")
    return run_gold_smoke(args)


if __name__ == "__main__":
    raise SystemExit(main())
