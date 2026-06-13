from __future__ import annotations

import argparse
import json
import os
import subprocess
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

from skill_deployment import hash_file_sha256, hash_json_file_sha256, resolve_installed_skill  # noqa: E402
from skill_deployment.evidence import write_json, write_text  # noqa: E402


OUTPUT_ROOT = ROOT / "outputs" / "external_swebench"
REPORT_PATH = ROOT / "reports" / "SWEBENCH_EXTERNAL_SMOKE_STATUS.md"
MATURITY_LEDGER_PATH = ROOT / "reports" / "FRAMEWORK_MATURITY_EVIDENCE_LEDGER.md"
DEFAULT_RUN_ID = "swebench_lite_smoke_20260612"
WSL_DISTRO = "Ubuntu-24.04-Codex"
DEFAULT_WSL_SWEBENCH_PYTHON = "/opt/spark/swebench-tools/swebench-venv/bin/python"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def read_json(path: Path, default: Any | None = None) -> Any:
    if not path.exists():
        if default is not None:
            return default
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8-sig"))


def dataset_slug(dataset: str) -> str:
    return dataset.replace("/", "_").replace("-", "_")


def windows_to_wsl_path(path: Path) -> str:
    resolved = path.resolve()
    drive = resolved.drive.rstrip(":").lower()
    rest = str(resolved)[3:].replace("\\", "/")
    return f"/mnt/{drive}/{rest}"


def run_wsl(command: str, *, cwd: Path | None = None, timeout: int = 300) -> dict[str, Any]:
    script = command if cwd is None else f"cd {shell_quote(windows_to_wsl_path(cwd))} && {command}"
    try:
        completed = subprocess.run(
            ["wsl", "-d", WSL_DISTRO, "--", "bash", "-lc", script],
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


def shell_quote(value: str) -> str:
    return "'" + value.replace("'", "'\"'\"'") + "'"


def swebench_python_command() -> str:
    configured = os.environ.get("WSL_SWEBENCH_PYTHON")
    if configured:
        return configured
    probe = run_wsl(f"test -x {shell_quote(DEFAULT_WSL_SWEBENCH_PYTHON)}", timeout=30)
    if probe.get("ok"):
        return DEFAULT_WSL_SWEBENCH_PYTHON
    return "python3"


def fetch_hf_rows_once(dataset: str, *, length: int) -> list[dict[str, Any]]:
    params = urllib.parse.urlencode(
        {
            "dataset": dataset,
            "config": "default",
            "split": "test",
            "offset": 0,
            "length": length,
        }
    )
    url = f"https://datasets-server.huggingface.co/rows?{params}"
    with urllib.request.urlopen(url, timeout=60) as response:
        payload = json.loads(response.read().decode("utf-8"))
    rows = []
    for item in payload.get("rows", []):
        row = dict(item.get("row", {}))
        if row:
            rows.append(row)
    if not rows:
        raise ValueError(f"Hugging Face rows API returned no rows for {dataset}")
    return rows


def fetch_hf_rows(dataset: str, *, length: int) -> tuple[list[dict[str, Any]], str, list[str]]:
    candidates = [dataset]
    if dataset == "SWE-bench/SWE-bench_Lite":
        candidates.append("princeton-nlp/SWE-bench_Lite")
    errors: list[str] = []
    for candidate in candidates:
        try:
            return fetch_hf_rows_once(candidate, length=length), candidate, errors
        except Exception as exc:
            errors.append(f"{candidate}: {type(exc).__name__}: {exc}")
    raise ValueError("; ".join(errors))


def select_instances(rows: list[dict[str, Any]], *, limit: int) -> list[dict[str, Any]]:
    def key(row: dict[str, Any]) -> str:
        return str(row.get("instance_id") or row.get("id") or "")

    selected = sorted(rows, key=key)[:limit]
    normalized = []
    for row in selected:
        normalized.append(
            {
                "instance_id": str(row.get("instance_id") or ""),
                "repo": row.get("repo"),
                "base_commit": row.get("base_commit"),
                "problem_statement": row.get("problem_statement"),
                "patch": row.get("patch") or "",
                "test_patch": row.get("test_patch") or "",
                "version": row.get("version"),
                "FAIL_TO_PASS": row.get("FAIL_TO_PASS"),
                "PASS_TO_PASS": row.get("PASS_TO_PASS"),
            }
        )
    return normalized


def prepare(args: argparse.Namespace) -> int:
    out_dir = OUTPUT_ROOT / "prepared" / f"{dataset_slug(args.dataset)}_limit{args.limit}_seed{args.seed}"
    try:
        rows, resolved_dataset, fetch_errors = fetch_hf_rows(args.dataset, length=max(args.limit * 10, 50))
        instances = select_instances(rows, limit=args.limit)
        status = "prepared"
        error = None
    except Exception as exc:
        instances = []
        resolved_dataset = args.dataset
        fetch_errors = []
        status = "blocked_dataset_fetch"
        error = f"{type(exc).__name__}: {exc}"
    payload = {
        "prepared_at": utc_now(),
        "status": status,
        "dataset": args.dataset,
        "resolved_dataset": resolved_dataset,
        "limit": args.limit,
        "selection": args.selection,
        "seed": args.seed,
        "instances": instances,
        "error": error,
        "fetch_errors": fetch_errors,
        "source": "https://huggingface.co/datasets/SWE-bench/SWE-bench_Lite",
    }
    write_json(out_dir / "instances.json", payload)
    write_json(OUTPUT_ROOT / "latest_prepare.json", {"instances_path": str(out_dir / "instances.json"), **payload})
    print(json.dumps({"output": str(out_dir / "instances.json"), "status": status, "count": len(instances)}, indent=2))
    return 0 if status == "prepared" else 2


def prediction_rows(instances: list[dict[str, Any]], variant: str, *, model_patch_blocked: bool) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for instance in instances:
        if variant == "empty_patch":
            patch = ""
        elif variant == "gold_patch":
            patch = str(instance.get("patch") or "")
        elif variant == "skill_llm_patch":
            patch = "" if model_patch_blocked else ""
        else:
            raise ValueError(f"unsupported SWE-bench variant: {variant}")
        rows.append(
            {
                "instance_id": instance["instance_id"],
                "model_name_or_path": variant,
                "model_patch": patch,
            }
        )
    return rows


def check_wsl_environment() -> dict[str, Any]:
    python_cmd = swebench_python_command()
    docker = run_wsl("docker --version", timeout=30)
    harness = run_wsl(
        f"{shell_quote(python_cmd)} -c \"import importlib.util; raise SystemExit(0 if importlib.util.find_spec('swebench') else 3)\"",
        timeout=30,
    )
    return {
        "wsl_distro": WSL_DISTRO,
        "python": python_cmd,
        "docker": docker,
        "swebench_python_package": harness,
        "docker_available": bool(docker.get("ok")),
        "official_harness_available": bool(harness.get("ok")),
    }


def read_official_report(report_dirs: list[Path], variant: str, run_id: str) -> dict[str, Any] | None:
    report_path: Path | None = None
    for candidate_dir in report_dirs:
        exact = candidate_dir / f"{variant}.{run_id}.json"
        if exact.exists():
            report_path = exact
            break
        candidates = sorted(candidate_dir.glob(f"{variant}.*.json"))
        if candidates:
            report_path = candidates[-1]
            break
    if report_path is None:
        return None
    try:
        payload = read_json(report_path)
    except Exception:
        return None
    return {"path": str(report_path), "payload": payload}


def official_evaluate(
    run_dir: Path,
    dataset: str,
    variant: str,
    predictions_path: Path,
    max_workers: int,
    instance_ids: list[str],
) -> dict[str, Any]:
    env = check_wsl_environment()
    result_path = run_dir / "evaluation" / variant / "results.json"
    report_dir = run_dir / "evaluation" / variant / "official_reports"
    official_run_id = f"{run_dir.name}_{variant}"
    if not env["docker_available"]:
        result = {
            "status": "blocked_docker_unavailable",
            "variant": variant,
            "official_harness": True,
            "environment": env,
            "resolved_count": None,
            "total_instances": None,
        }
        write_json(result_path, result)
        return result
    if not env["official_harness_available"]:
        result = {
            "status": "blocked_official_harness_missing",
            "variant": variant,
            "official_harness": True,
            "environment": env,
            "resolved_count": None,
            "total_instances": None,
            "note": "Install the official SWE-bench package inside WSL to execute Docker evaluation.",
        }
        write_json(result_path, result)
        return result
    command = " ".join(
        [
            shell_quote(str(env["python"])),
            "-m swebench.harness.run_evaluation",
            "--dataset_name",
            shell_quote(dataset),
            "--split test",
            "--instance_ids",
            " ".join(shell_quote(item) for item in instance_ids),
            "--predictions_path",
            shell_quote(windows_to_wsl_path(predictions_path)),
            "--max_workers",
            str(max_workers),
            "--run_id",
            shell_quote(official_run_id),
            "--report_dir",
            shell_quote(windows_to_wsl_path(report_dir)),
            "--namespace",
            "none",
        ]
    )
    completed = run_wsl(command, cwd=run_dir, timeout=60 * 60)
    official_report = read_official_report([report_dir, run_dir], variant, official_run_id) if completed.get("ok") else None
    report_payload = official_report["payload"] if official_report else {}
    completed_instances = report_payload.get("completed_instances")
    resolved_instances = report_payload.get("resolved_instances")
    empty_patch_instances = report_payload.get("empty_patch_instances")
    error_instances = report_payload.get("error_instances")
    if completed.get("ok") and official_report:
        status = "completed"
        if empty_patch_instances == len(instance_ids) and completed_instances == 0:
            status = "completed_empty_patch_skipped_by_official_harness"
        elif isinstance(error_instances, int) and error_instances > 0:
            status = "completed_with_errors"
    else:
        stderr_text = str(completed.get("stderr", ""))
        if "registry-1.docker.io" in stderr_text and (
            "i/o timeout" in stderr_text or "connection refused" in stderr_text
        ):
            status = "blocked_docker_registry_unavailable"
        else:
            status = "official_harness_failed"
    result = {
        "status": status,
        "variant": variant,
        "official_harness": True,
        "environment": env,
        "command_result": completed,
        "official_report": official_report,
        "resolved_count": resolved_instances,
        "total_instances": len(instance_ids),
        "completed_instances": completed_instances,
        "empty_patch_instances": empty_patch_instances,
        "error_instances": error_instances,
        "note": "Raw official harness logs are stored in command_result; resolved counts are parsed from the official report when present.",
        "blocked_reason": (
            "Docker registry access failed while resolving official SWE-bench images/base images."
            if status == "blocked_docker_registry_unavailable"
            else None
        ),
    }
    write_json(result_path, result)
    return result


def installed_skill_provenance(installed: str) -> dict[str, Any]:
    try:
        resolved = resolve_installed_skill(ROOT, installed)
        skill_dir = Path(resolved["skill_dir"])
        return {
            "installed_skill": installed,
            "skill_package_path": str(skill_dir),
            "skill_version": resolved["skill_package"].version,
            "skill_hash": hash_file_sha256(skill_dir / "SKILL.md"),
            "manifest_hash": hash_json_file_sha256(skill_dir / "manifest.json"),
        }
    except Exception as exc:
        return {
            "installed_skill": installed,
            "status": "unresolved",
            "error": f"{type(exc).__name__}: {exc}",
        }


def run(args: argparse.Namespace) -> int:
    latest = read_json(OUTPUT_ROOT / "latest_prepare.json", {})
    instances_payload = read_json(Path(str(latest.get("instances_path", ""))), {}) if latest.get("instances_path") else {}
    instances = list(instances_payload.get("instances", []))
    dataset = str(instances_payload.get("resolved_dataset") or args.dataset)
    run_dir = OUTPUT_ROOT / args.run_id
    write_json(run_dir / "instances.json", {"run_id": args.run_id, "dataset": dataset, "prepared_from": latest.get("instances_path"), "instances": instances})
    official_dataset_path = run_dir / "official_dataset.json"
    write_json(official_dataset_path, instances)
    variants = [item.strip() for item in args.variants.split(",") if item.strip()]
    model_env_available = bool(os.environ.get("OPENAI_API_KEY") and (os.environ.get("MODEL") or os.environ.get("OPENAI_MODEL")))
    skill_provenance = installed_skill_provenance(args.installed)
    evaluations: dict[str, Any] = {}
    for variant in variants:
        blocked_model = variant == "skill_llm_patch" and not model_env_available
        rows = prediction_rows(instances, variant, model_patch_blocked=blocked_model)
        predictions_path = run_dir / "predictions" / f"{variant}.jsonl"
        write_jsonl(predictions_path, rows)
        if blocked_model:
            evaluation = {
                "status": "blocked_no_model",
                "variant": variant,
                "official_harness": False,
                "resolved_count": None,
                "total_instances": len(instances),
                "reason": "OPENAI_API_KEY plus MODEL or OPENAI_MODEL is required for non-oracle patch generation.",
            }
            write_json(run_dir / "evaluation" / variant / "results.json", evaluation)
        else:
            evaluation = official_evaluate(
                run_dir,
                windows_to_wsl_path(official_dataset_path),
                variant,
                predictions_path,
                args.max_workers,
                [str(instance["instance_id"]) for instance in instances],
            )
        evaluations[variant] = evaluation
        for instance in instances:
            write_json(
                run_dir / "evidence" / instance["instance_id"] / variant / "summary.json",
                {
                    "run_id": args.run_id,
                    "instance_id": instance["instance_id"],
                    "variant": variant,
                    "dataset": dataset,
                    "prediction_path": str(predictions_path),
                    "evaluation_status": evaluation["status"],
                    "skill_provenance": skill_provenance if variant == "skill_llm_patch" else None,
                    "claim_boundary": "SWE-bench smoke evidence; no external effectiveness claim unless non-oracle patch beats empty_patch.",
                },
            )
    marginal = build_marginal_utility(args.run_id, instances, evaluations)
    write_json(run_dir / "marginal_utility.json", marginal)
    write_json(
        run_dir / "run_summary.json",
        {
            "run_id": args.run_id,
            "dataset": dataset,
            "variant_status": {key: value["status"] for key, value in evaluations.items()},
            "blocked_reasons": {
                key: value.get("blocked_reason") or value.get("reason")
                for key, value in evaluations.items()
                if value.get("blocked_reason") or value.get("reason")
            },
            "instance_count": len(instances),
            "skill_provenance": skill_provenance,
            "marginal_utility": str(run_dir / "marginal_utility.json"),
        },
    )
    print(json.dumps({"output": str(run_dir / "run_summary.json"), "variant_status": {k: v["status"] for k, v in evaluations.items()}}, indent=2))
    return 0


def build_marginal_utility(run_id: str, instances: list[dict[str, Any]], evaluations: dict[str, Any]) -> dict[str, Any]:
    resolved = {key: value.get("resolved_count") for key, value in evaluations.items()}
    empty = resolved.get("empty_patch")
    skill = resolved.get("skill_llm_patch")
    if isinstance(empty, int) and isinstance(skill, int):
        skill_over_empty = skill - empty
        effectiveness_supported = skill > empty
    else:
        skill_over_empty = None
        effectiveness_supported = False
    return {
        "run_id": run_id,
        "generated_at": utc_now(),
        "instance_count": len(instances),
        "resolved_count": resolved,
        "skill_llm_patch_over_empty_patch": skill_over_empty,
        "adapter_maturity_supported": all(
            value.get("status") == "completed" for value in evaluations.values()
        ),
        "official_gold_plumbing_supported": evaluations.get("gold_patch", {}).get("status") == "completed",
        "framework_effectiveness_supported": effectiveness_supported,
        "boundary": "Gold patch is plumbing upper bound only and is excluded from framework effectiveness.",
    }


def render_status(run_dir: Path, summary: dict[str, Any], marginal: dict[str, Any]) -> str:
    lines = [
        "# SWE-bench External Smoke Status",
        "",
        f"- Run: `{summary['run_id']}`",
        f"- Dataset: `{summary['dataset']}`",
        f"- Instances: `{summary['instance_count']}`",
        "",
        "## Variant Status",
        "",
    ]
    for variant, status in summary["variant_status"].items():
        lines.append(f"- `{variant}`: `{status}`")
    blocked_reasons = summary.get("blocked_reasons", {})
    if blocked_reasons:
        lines.extend(["", "## Blocked Reasons", ""])
        for variant, reason in blocked_reasons.items():
            lines.append(f"- `{variant}`: {reason}")
    lines.extend(
        [
            "",
            "## Evidence",
            "",
            f"- Instances: `{run_dir / 'instances.json'}`",
            f"- Marginal utility: `{run_dir / 'marginal_utility.json'}`",
            "",
            "## Claims",
            "",
            f"- Adapter maturity supported: `{marginal['adapter_maturity_supported']}`",
            f"- Official gold-patch plumbing supported: `{marginal.get('official_gold_plumbing_supported')}`",
            f"- Framework effectiveness supported: `{marginal['framework_effectiveness_supported']}`",
            "",
            "No SWE-bench effectiveness claim is made unless `skill_llm_patch` beats `empty_patch` on resolved count.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_ledger(swe_status: dict[str, Any], marginal: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Framework Maturity Evidence Ledger",
            "",
            "## Internal Evidence",
            "",
            "- Multi-security installed runtime evidence is recorded in `reports/MULTI_CAPABILITY_GENERALIZATION_STATUS.md`.",
            "",
            "## External Evidence",
            "",
            f"- SWE-bench run: `{swe_status['run_id']}`",
            f"- Adapter maturity supported: `{marginal['adapter_maturity_supported']}`",
            f"- Official gold-patch plumbing supported: `{marginal.get('official_gold_plumbing_supported')}`",
            f"- Framework effectiveness supported: `{marginal['framework_effectiveness_supported']}`",
            "",
            "## Boundary",
            "",
            "This ledger separates internal controlled evidence, external adapter plumbing, and external effectiveness evidence.",
            "",
        ]
    )


def summarize(args: argparse.Namespace) -> int:
    run_dir = OUTPUT_ROOT / args.run_id
    summary = read_json(run_dir / "run_summary.json")
    marginal = read_json(run_dir / "marginal_utility.json")
    write_text(REPORT_PATH, render_status(run_dir, summary, marginal))
    write_text(MATURITY_LEDGER_PATH, render_ledger(summary, marginal))
    print(json.dumps({"report": str(REPORT_PATH), "ledger": str(MATURITY_LEDGER_PATH)}, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Narrow SWE-bench Lite smoke adapter.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare_parser = subparsers.add_parser("prepare")
    prepare_parser.add_argument("--dataset", default="SWE-bench/SWE-bench_Lite")
    prepare_parser.add_argument("--limit", type=int, default=5)
    prepare_parser.add_argument("--selection", default="stable")
    prepare_parser.add_argument("--seed", default="20260612")
    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--run-id", default=DEFAULT_RUN_ID)
    run_parser.add_argument("--dataset", default="SWE-bench/SWE-bench_Lite")
    run_parser.add_argument("--variants", default="empty_patch,gold_patch,skill_llm_patch")
    run_parser.add_argument("--installed", default="software_patch_review")
    run_parser.add_argument("--max-workers", type=int, default=1)
    run_parser.add_argument("--backend", default="official_docker")
    summarize_parser = subparsers.add_parser("summarize")
    summarize_parser.add_argument("--run-id", default=DEFAULT_RUN_ID)
    args = parser.parse_args(argv)
    if args.command == "prepare":
        return prepare(args)
    if args.command == "run":
        if args.backend != "official_docker":
            raise SystemExit(f"unsupported SWE-bench backend: {args.backend}")
        return run(args)
    if args.command == "summarize":
        return summarize(args)
    raise SystemExit(f"unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
