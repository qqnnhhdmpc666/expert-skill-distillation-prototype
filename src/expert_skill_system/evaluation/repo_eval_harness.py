from __future__ import annotations

import json
import platform
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ..core.canonical import sha256_json
from ..runtime.release_bundle_resolver import resolve_release_bundle
from .repo_run_report import build_repo_run_report, write_repo_run_report
from .repo_security_task import run_dependency_use_triage
from .repo_task_registry import load_repo_task_registry, select_registry_tasks, task_entry_dir

RUNNER_VERSION = "repo_level_eval_harness.v1"


def run_repo_level_eval(
    *,
    task_registry: Path,
    output_dir: Path,
    state_dir: Path,
    bundle_digest: str | None = None,
    use_active_binding: bool = False,
    task_id: str | None = None,
    condition: str = "C5_active_runtime",
    allow_local_manifest_only: bool = False,
    fail_on_partial_bundle: bool = False,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    registry = load_repo_task_registry(task_registry)
    tasks = select_registry_tasks(registry, task_id=task_id)
    bundle_resolution = resolve_release_bundle(
        state_dir=state_dir,
        bundle_digest=bundle_digest,
        use_active_binding=use_active_binding,
        allow_local_manifest_only=allow_local_manifest_only,
        fail_on_partial_bundle=fail_on_partial_bundle,
    )
    _write_json(output_dir / "bundle_resolution.json", _without_bundle_manifest(bundle_resolution))
    run_manifest = {
        "schema_version": "repo_level_eval_run_manifest.v1",
        "run_id": output_dir.name,
        "task_registry": str(task_registry),
        "task_registry_digest": registry["registry_digest"],
        "state_dir": str(state_dir),
        "condition": condition,
        "task_ids": [task["task_id"] for task in tasks],
        "bundle_attachment_mode": bundle_resolution["bundle_attachment_mode"],
        "runner_version": RUNNER_VERSION,
    }
    _write_json(output_dir / "run_manifest.json", run_manifest)
    _write_json(
        output_dir / "run_provenance.json",
        {
            "schema_version": "repo_level_eval_run_provenance.v1",
            "run_id": output_dir.name,
            "timestamp": datetime.now(UTC).isoformat(),
            "git_commit": _git_commit(),
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "state_dir": str(state_dir),
            "bundle_digest": bundle_resolution.get("bundle_digest"),
            "task_registry_digest": registry["registry_digest"],
            "task_ids": [task["task_id"] for task in tasks],
            "runner_version": RUNNER_VERSION,
        },
    )

    task_results: list[dict[str, Any]] = []
    jsonl_lines: list[str] = []
    for task in tasks:
        task_dir = task_entry_dir(task_registry, task)
        task_output = output_dir / "tasks" / task["task_id"]
        result = run_dependency_use_triage(
            task_dir,
            task_output,
            condition_id=condition,
            bundle_resolution=bundle_resolution,
        )
        row = {
            "schema_version": "repo_level_eval_task_result.v1",
            "task_id": task["task_id"],
            "task_type": task["task_type"],
            "fixture_type": task["fixture_type"],
            "verifier_pass": result["verifier_pass"],
            "failure_category": result["failure_category"],
            "decision": result["decision"],
            "runtime_status": "completed",
            "prediction_path": result["prediction_path"],
            "verifier_result_path": result["verifier_result_path"],
            "trajectory_evidence_dir": result["trajectory_evidence"]["package_dir"],
            "bundle_attachment_mode": bundle_resolution["bundle_attachment_mode"],
        }
        task_results.append(row)
        jsonl_lines.append(json.dumps(row, ensure_ascii=False, sort_keys=True))
    (output_dir / "task_results.jsonl").write_text("\n".join(jsonl_lines) + ("\n" if jsonl_lines else ""), encoding="utf-8")
    report = build_repo_run_report(task_results=task_results, bundle_resolution=bundle_resolution, registry=registry)
    write_repo_run_report(output_dir, report)
    summary = {
        "schema_version": "repo_level_eval_run_summary.v1",
        "run_manifest_digest": sha256_json(run_manifest),
        "task_count": len(task_results),
        "pass_count": report["pass_count"],
        "fail_count": report["fail_count"],
        "bundle_attachment_mode": bundle_resolution["bundle_attachment_mode"],
        "output_dir": str(output_dir),
    }
    _write_json(output_dir / "run_summary.json", summary)
    return summary


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def _without_bundle_manifest(bundle_resolution: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in bundle_resolution.items() if key != "bundle_manifest"}


def _git_commit() -> str | None:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL).strip()
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
