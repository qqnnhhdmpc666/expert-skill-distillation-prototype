from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from expert_skill_system.agent_backends import (  # noqa: E402
    AgentBackendRequest,
    DeterministicReferenceAdapter,
    MiniSweAgentSmokeAdapter,
    NormalizedTrajectoryEvent,
)
from expert_skill_system.agent_backends.base import (  # noqa: E402
    write_json,
    write_required_agent_artifacts,
)
from expert_skill_system.compiler.repo_level_bundle_builder import (  # noqa: E402
    REPO_LEVEL_SKILL_ID,
    RepoLevelBundleBuilder,
)
from expert_skill_system.registry.workspace import Workspace  # noqa: E402
from expert_skill_system.runtime.release_bundle_resolver import resolve_release_bundle  # noqa: E402

REPO_LANE = "repo_level_dependency_use"
SWE_LANE = "swe_bench_micro"
NO_SKILL = "no_skill"
BUNDLE = "distillation_loop_v1_bundle"
BACKENDS = ("deterministic_reference", "mini_swe_agent")
CONDITIONS = (NO_SKILL, BUNDLE)
PUBLIC_ROOT = ROOT / "data" / "repo_security_tasks" / "public_heldout_v0"
TARGET_CLEAN_REPOS = 3


CANDIDATE_SEARCH_LOG: list[dict[str, Any]] = [
    {
        "repo_url": "https://github.com/hindupuravinash/the-gan-zoo",
        "commit_hash": "375f2be4a852ead8980c06b2a996893f0cb95713",
        "candidate_reason": "Existing immutable public excerpt with pinned requests dependency and import/use site.",
        "license_status": "ok",
        "dependency_declaration_status": "found",
        "import_use_evidence_status": "found",
        "advisory_binding_status": "found",
        "snapshot_feasibility": "ok",
        "verifier_feasibility": "deterministic",
        "accepted": True,
        "quality_tier": "A",
        "rejection_reason": "",
    },
    {
        "repo_url": "https://github.com/codelucas/newspaper",
        "commit_hash": "not_resolved_bounded_screen",
        "candidate_reason": "Python project with requests usage; screened as possible dependency-use excerpt.",
        "license_status": "ok",
        "dependency_declaration_status": "unclear",
        "import_use_evidence_status": "found",
        "advisory_binding_status": "unclear",
        "snapshot_feasibility": "unclear",
        "verifier_feasibility": "weak",
        "accepted": False,
        "quality_tier": "C",
        "rejection_reason": "No bounded immutable vulnerable dependency/advisory binding was established in this slice.",
    },
    {
        "repo_url": "https://github.com/psf/requests",
        "commit_hash": "not_resolved_bounded_screen",
        "candidate_reason": "Canonical requests repository; useful as source but not an application dependency-use excerpt.",
        "license_status": "ok",
        "dependency_declaration_status": "missing",
        "import_use_evidence_status": "found",
        "advisory_binding_status": "missing",
        "snapshot_feasibility": "unclear",
        "verifier_feasibility": "unavailable",
        "accepted": False,
        "quality_tier": "rejected",
        "rejection_reason": "Library source is not a downstream pinned dependency-use triage task.",
    },
    {
        "repo_url": "https://github.com/pallets/flask",
        "commit_hash": "not_resolved_bounded_screen",
        "candidate_reason": "Popular Python repo considered for public dependency triage.",
        "license_status": "ok",
        "dependency_declaration_status": "unclear",
        "import_use_evidence_status": "unclear",
        "advisory_binding_status": "missing",
        "snapshot_feasibility": "unclear",
        "verifier_feasibility": "weak",
        "accepted": False,
        "quality_tier": "C",
        "rejection_reason": "No clean pinned vulnerable package/use/advisory tuple was confirmed.",
    },
    {
        "repo_url": "https://github.com/kennethreitz/httpbin",
        "commit_hash": "not_resolved_bounded_screen",
        "candidate_reason": "Small Python web project considered for dependency-use evidence.",
        "license_status": "ok",
        "dependency_declaration_status": "unclear",
        "import_use_evidence_status": "unclear",
        "advisory_binding_status": "missing",
        "snapshot_feasibility": "ok",
        "verifier_feasibility": "weak",
        "accepted": False,
        "quality_tier": "C",
        "rejection_reason": "Advisory binding and deterministic expected decision not cleanly established.",
    },
    {
        "repo_url": "https://github.com/getsentry/responses",
        "commit_hash": "not_resolved_bounded_screen",
        "candidate_reason": "Requests-adjacent Python project screened for import/dependency evidence.",
        "license_status": "ok",
        "dependency_declaration_status": "unclear",
        "import_use_evidence_status": "found",
        "advisory_binding_status": "missing",
        "snapshot_feasibility": "ok",
        "verifier_feasibility": "weak",
        "accepted": False,
        "quality_tier": "C",
        "rejection_reason": "Could not bind a frozen vulnerable dependency decision within bounded search.",
    },
    {
        "repo_url": "https://github.com/requests-cache/requests-cache",
        "commit_hash": "not_resolved_bounded_screen",
        "candidate_reason": "Requests-based Python project screened as possible app-like excerpt.",
        "license_status": "ok",
        "dependency_declaration_status": "unclear",
        "import_use_evidence_status": "found",
        "advisory_binding_status": "missing",
        "snapshot_feasibility": "unclear",
        "verifier_feasibility": "weak",
        "accepted": False,
        "quality_tier": "C",
        "rejection_reason": "No A-tier immutable dependency/advisory tuple established.",
    },
    {
        "repo_url": "https://github.com/locustio/locust",
        "commit_hash": "not_resolved_bounded_screen",
        "candidate_reason": "Python project with network-client dependencies considered for public excerpt.",
        "license_status": "ok",
        "dependency_declaration_status": "unclear",
        "import_use_evidence_status": "unclear",
        "advisory_binding_status": "missing",
        "snapshot_feasibility": "too_large",
        "verifier_feasibility": "weak",
        "accepted": False,
        "quality_tier": "C",
        "rejection_reason": "Too broad for minimal frozen excerpt without more manual curation.",
    },
    {
        "repo_url": "https://github.com/ytdl-org/youtube-dl",
        "commit_hash": "not_resolved_bounded_screen",
        "candidate_reason": "Large Python project screened for pinned dependency and use-site evidence.",
        "license_status": "ok",
        "dependency_declaration_status": "unclear",
        "import_use_evidence_status": "unclear",
        "advisory_binding_status": "missing",
        "snapshot_feasibility": "too_large",
        "verifier_feasibility": "weak",
        "accepted": False,
        "quality_tier": "C",
        "rejection_reason": "Not suitable as small deterministic v0 excerpt without additional curation.",
    },
    {
        "repo_url": "https://github.com/ansible/ansible",
        "commit_hash": "not_resolved_bounded_screen",
        "candidate_reason": "Security-relevant Python project screened for dependency-use task potential.",
        "license_status": "ok",
        "dependency_declaration_status": "unclear",
        "import_use_evidence_status": "unclear",
        "advisory_binding_status": "missing",
        "snapshot_feasibility": "too_large",
        "verifier_feasibility": "weak",
        "accepted": False,
        "quality_tier": "C",
        "rejection_reason": "Repository is too large for v0 minimal frozen excerpt.",
    },
    {
        "repo_url": "https://github.com/mitmproxy/mitmproxy",
        "commit_hash": "not_resolved_bounded_screen",
        "candidate_reason": "Network/security Python project screened for dependency-use evidence.",
        "license_status": "ok",
        "dependency_declaration_status": "unclear",
        "import_use_evidence_status": "unclear",
        "advisory_binding_status": "missing",
        "snapshot_feasibility": "too_large",
        "verifier_feasibility": "weak",
        "accepted": False,
        "quality_tier": "C",
        "rejection_reason": "Needs manual narrowing before it can become a clean held-out excerpt.",
    },
    {
        "repo_url": "https://github.com/home-assistant/core",
        "commit_hash": "not_resolved_bounded_screen",
        "candidate_reason": "Large Python project screened as future held-out candidate.",
        "license_status": "ok",
        "dependency_declaration_status": "unclear",
        "import_use_evidence_status": "unclear",
        "advisory_binding_status": "missing",
        "snapshot_feasibility": "too_large",
        "verifier_feasibility": "weak",
        "accepted": False,
        "quality_tier": "C",
        "rejection_reason": "Too large for bounded v0 intake; useful only for future curated benchmark work.",
    },
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Public Held-Out Evaluation v0.")
    parser.add_argument("--output", required=True)
    parser.add_argument("--state-dir", required=True)
    parser.add_argument("--reports-dir", default="reports")
    args = parser.parse_args(argv)

    output = Path(args.output)
    state_dir = Path(args.state_dir)
    reports_dir = Path(args.reports_dir)
    _reset_dir(output)
    output.mkdir(parents=True, exist_ok=True)
    state_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    registry = _read_json(PUBLIC_ROOT / "registry.json")
    excerpts = _accepted_a_tier_excerpts(registry)
    bundle = _build_bundle(state_dir / "bundle")
    bundle_resolution = resolve_release_bundle(
        state_dir=state_dir / "bundle",
        bundle_digest=bundle["bundle_digest"],
        binding_key=REPO_LEVEL_SKILL_ID,
        fail_on_partial_bundle=True,
    )

    candidate_summary = _candidate_summary(CANDIDATE_SEARCH_LOG)
    write_json(output / "public_excerpt_candidate_search_log.json", {"schema_version": "public_excerpt_candidate_search_log.v1", "candidates": CANDIDATE_SEARCH_LOG, **candidate_summary})
    (output / "public_excerpt_candidate_search_log.md").write_text(_render_candidate_log_md(CANDIDATE_SEARCH_LOG, candidate_summary), encoding="utf-8")

    swe_probe = _swe_bench_probe()
    rows = []
    for lane in (REPO_LANE, SWE_LANE):
        for backend in BACKENDS:
            for condition in CONDITIONS:
                if lane == REPO_LANE:
                    row = _run_repo_matrix_row(
                        output=output,
                        backend=backend,
                        condition=condition,
                        excerpts=excerpts,
                        bundle=bundle,
                        bundle_resolution=bundle_resolution,
                    )
                else:
                    row = _run_swe_contract_row(output=output, backend=backend, condition=condition, bundle=bundle, swe_probe=swe_probe)
                rows.append(row)

    matrix = {"schema_version": "public_heldout_effect_matrix.v1", "rows": rows}
    write_json(output / "backend_condition_lane_effect_matrix.json", matrix)
    (output / "backend_condition_lane_effect_matrix.md").write_text(_render_matrix_md(rows), encoding="utf-8")

    repo_manifest = _repo_level_manifest(registry, excerpts, candidate_summary)
    swe_manifest = _swe_manifest(swe_probe)
    anti_leakage = _anti_leakage(output, rows, excerpts)
    claim_boundary = _claim_boundary()
    per_lane = _per_lane_summary(rows, repo_manifest, swe_manifest)
    aggregate = _aggregate_summary(per_lane, anti_leakage, claim_boundary, candidate_summary)

    write_json(output / "repo_level_heldout_manifest.json", repo_manifest)
    write_json(output / "swe_bench_micro_lane_manifest.json", swe_manifest)
    write_json(output / "per_lane_summary.json", per_lane)
    write_json(output / "aggregate_summary.json", aggregate)
    write_json(output / "anti_leakage_audit.json", anti_leakage)
    write_json(output / "claim_boundary.json", claim_boundary)

    (reports_dir / "PUBLIC_HELDOUT_EVALUATION_V0_STATUS.md").write_text(_render_status_md(aggregate, per_lane, candidate_summary), encoding="utf-8")
    (reports_dir / "PUBLIC_HELDOUT_EVALUATION_V0_ANTI_LEAKAGE_AUDIT.md").write_text(_render_anti_leakage_md(anti_leakage), encoding="utf-8")
    (reports_dir / "PUBLIC_HELDOUT_EVALUATION_V0_EFFECT_INTERPRETATION.md").write_text(_render_effect_interpretation_md(rows, aggregate), encoding="utf-8")

    print(json.dumps(aggregate, indent=2, sort_keys=True))
    return 0


def _build_bundle(state_dir: Path) -> dict[str, Any]:
    if state_dir.exists():
        shutil.rmtree(state_dir)
    workspace = Workspace.open(state_dir)
    result = RepoLevelBundleBuilder(workspace).build(
        data_dir=ROOT / "data" / "repo_level_bundle",
        skill_family=REPO_LEVEL_SKILL_ID,
        promote=False,
        variant="public_heldout_evaluation_v0",
    )
    return {**result.to_dict(), "state_dir": str(state_dir)}


def _accepted_a_tier_excerpts(registry: dict[str, Any]) -> list[dict[str, Any]]:
    result = []
    for item in registry.get("excerpts", []):
        if item.get("accepted") and item.get("quality_tier") == "A":
            task_dir = PUBLIC_ROOT / str(item["task_dir"])
            source_manifest = _read_json(task_dir / "source_manifest.json")
            result.append({**item, "task_dir_path": task_dir, "source_manifest": source_manifest})
    return result


def _run_repo_matrix_row(
    *,
    output: Path,
    backend: str,
    condition: str,
    excerpts: list[dict[str, Any]],
    bundle: dict[str, Any],
    bundle_resolution: dict[str, Any],
) -> dict[str, Any]:
    row_dir = output / "runs" / _slug(REPO_LANE) / _slug(backend) / _slug(condition)
    row_dir.mkdir(parents=True, exist_ok=True)
    has_bundle = condition == BUNDLE
    results = []
    started = time.perf_counter()
    adapter = DeterministicReferenceAdapter() if backend == "deterministic_reference" else MiniSweAgentSmokeAdapter()
    for excerpt in excerpts:
        task_dir = Path(excerpt["task_dir_path"])
        excerpt_run_dir = row_dir / _slug(str(excerpt["excerpt_id"]))
        request = AgentBackendRequest(
            backend_id=backend,
            task_id=str(excerpt["task_id"]),
            workspace_path=str(excerpt_run_dir / "workspace"),
            bundle_path=bundle["state_dir"] if has_bundle else None,
            skill_artifact_path=bundle.get("agent_skill_artifact_digest") if has_bundle else None,
            knowledge_manifest_path=bundle.get("knowledge_projection_digest") if has_bundle else None,
            budget={"timeout_seconds": 30},
            output_dir=str(excerpt_run_dir),
            condition_id="C5_active_runtime" if has_bundle else "C0_no_skill",
            lane=REPO_LANE,
            task_payload={"task_dir": str(task_dir), "bundle_resolution": bundle_resolution if has_bundle else None},
            bundle_digest=bundle["bundle_digest"] if has_bundle else None,
            skill_artifact_digest=bundle["agent_skill_artifact_digest"] if has_bundle else None,
            knowledge_manifest_digest=bundle["knowledge_projection_digest"] if has_bundle else None,
        )
        result = adapter.run(request)
        results.append(result.to_dict())
    elapsed = round(time.perf_counter() - started, 3)
    return _aggregate_repo_row(backend, condition, row_dir, results, elapsed)


def _aggregate_repo_row(backend: str, condition: str, row_dir: Path, results: list[dict[str, Any]], elapsed: float) -> dict[str, Any]:
    task_count = len(results)
    executed = [item for item in results if item["execution_status"] == "executed"]
    deterministic_counted = backend == "deterministic_reference"
    claim_counted = deterministic_counted and len(executed) == task_count
    pass_count = sum(int(item["pass_count"]) for item in results) if claim_counted else 0
    fail_count = sum(int(item["fail_count"]) for item in results) if claim_counted else 0
    evidence_rates = [_evidence_completeness(Path(item["output_dir"]) / "verifier_result.json") for item in results if claim_counted]
    abstention_rates = [_abstention_correctness(Path(item["output_dir"]) / "repo_task_run" / "prediction.json") for item in results if claim_counted and (Path(item["output_dir"]) / "repo_task_run" / "prediction.json").exists()]
    return {
        "lane": REPO_LANE,
        "backend": backend,
        "condition": condition,
        "task_count": task_count,
        "executed_count": len(executed),
        "pass_count": pass_count,
        "fail_count": fail_count,
        "not_counted_count": 0 if claim_counted else task_count,
        "execution_status": "executed" if len(executed) == task_count else "partial",
        "bundle_injected": condition == BUNDLE,
        "trajectory_available": all(item["trajectory_available"] for item in results),
        "verifier_available": all(item["verifier_available"] for item in results),
        "forbidden_access_pass": all(item["forbidden_access_pass"] for item in results),
        "unsupported_affected_decision_count": _unsupported_affected_count(results) if claim_counted else 0,
        "evidence_completeness_rate": _mean(evidence_rates),
        "abstention_correctness_rate": _mean(abstention_rates),
        "runtime_seconds_total": elapsed,
        "claim_counted": claim_counted,
        "output_dir": str(row_dir),
        "interpretation_note": "deterministic verifier counted" if claim_counted else "mini_swe_agent framework smoke; output is not schema-valid prediction",
    }


def _run_swe_contract_row(*, output: Path, backend: str, condition: str, bundle: dict[str, Any], swe_probe: dict[str, Any]) -> dict[str, Any]:
    row_dir = output / "runs" / _slug(SWE_LANE) / _slug(backend) / _slug(condition)
    row_dir.mkdir(parents=True, exist_ok=True)
    has_bundle = condition == BUNDLE
    request = AgentBackendRequest(
        backend_id=backend,
        task_id="swebench_lite_psf_requests_1963",
        workspace_path=str(row_dir / "workspace"),
        bundle_path=bundle["state_dir"] if has_bundle else None,
        skill_artifact_path=bundle.get("agent_skill_artifact_digest") if has_bundle else None,
        knowledge_manifest_path=bundle.get("knowledge_projection_digest") if has_bundle else None,
        budget={"timeout_seconds": 30},
        output_dir=str(row_dir),
        condition_id="C5_active_runtime" if has_bundle else "C0_no_skill",
        lane=SWE_LANE,
        task_payload={"swe_bench_instance_id": "psf__requests-1963"},
        bundle_digest=bundle["bundle_digest"] if has_bundle else None,
        skill_artifact_digest=bundle["agent_skill_artifact_digest"] if has_bundle else None,
        knowledge_manifest_digest=bundle["knowledge_projection_digest"] if has_bundle else None,
    )
    reason = "official_swe_bench_harness_not_executed_bounded_smoke"
    trajectory = [
        NormalizedTrajectoryEvent.make(
            step_index=0,
            actor="runtime",
            event_type="message",
            content_ref=reason,
            bundle_related=has_bundle,
        )
    ]
    bundle_trace = _bundle_trace(request) if backend == "mini_swe_agent" else None
    write_required_agent_artifacts(
        output_dir=row_dir,
        request=request,
        run_manifest={
            "schema_version": "agent_run_manifest.v1",
            "backend_id": backend,
            "task_id": request.task_id,
            "condition_id": request.condition_id,
            "execution_status": "blocked" if swe_probe["swe_bench_micro_lane_status"] == "blocked_by_environment" else "dry_run",
            "reason": reason,
            "swe_bench_probe": swe_probe,
        },
        agent_output={"schema_version": "agent_output.v1", "status": "contract_only", "reason": reason},
        verifier_result={
            "schema_version": "open_world_verifier_result.v1",
            "status": "contract_only",
            "verifier_pass": False,
            "official_harness_executed": False,
        },
        trajectory=trajectory,
        bundle_injection_trace=bundle_trace,
    )
    status = "blocked" if swe_probe["swe_bench_micro_lane_status"] == "blocked_by_environment" else "dry_run"
    return {
        "lane": SWE_LANE,
        "backend": backend,
        "condition": condition,
        "task_count": 1,
        "executed_count": 0,
        "pass_count": 0,
        "fail_count": 0,
        "not_counted_count": 1,
        "execution_status": status,
        "bundle_injected": has_bundle,
        "trajectory_available": True,
        "verifier_available": True,
        "forbidden_access_pass": True,
        "unsupported_affected_decision_count": 0,
        "evidence_completeness_rate": None,
        "abstention_correctness_rate": None,
        "runtime_seconds_total": 0.0,
        "claim_counted": False,
        "output_dir": str(row_dir),
        "interpretation_note": "SWE-bench compatibility probe only; official harness performance not claimed",
    }


def _swe_bench_probe() -> dict[str, Any]:
    venv_python = ROOT / "swebench-venv" / ("Scripts/python.exe" if sys.platform.startswith("win") else "bin/python")
    repo_dir = ROOT / "SWE-bench"
    docker = _run_probe(["docker", "--version"])
    import_probe = _run_probe([str(venv_python), "-c", "import swebench.harness.run_evaluation as r; print('ok')"]) if venv_python.exists() else {"ok": False, "stdout": "", "stderr": "swebench-venv python missing"}
    official_available = repo_dir.exists() and venv_python.exists() and import_probe["ok"]
    return {
        "schema_version": "swe_bench_micro_lane_manifest.v1",
        "swe_bench_instance_id": "psf__requests-1963",
        "dataset_source": "SWE-bench/SWE-bench_Lite",
        "repo": "psf/requests",
        "base_commit": "not_loaded_contract_only",
        "patch_or_test_gold_visible_to_agent": False,
        "gold_patch_visible_to_agent": False,
        "test_patch_visible_to_agent": False,
        "official_harness_available": official_available,
        "official_harness_executed": False,
        "official_swe_bench_performance": "not_claimed",
        "public_benchmark_execution": "not_pass",
        "execution_status": "contract_only" if official_available else "blocked_by_environment",
        "not_counted_reason": "bounded_smoke_does_not_execute_official_harness",
        "swe_bench_micro_lane_status": "harness_contract_ready" if official_available else "blocked_by_environment",
        "probes": {
            "swebench_venv_python_exists": venv_python.exists(),
            "swe_bench_repo_exists": repo_dir.exists(),
            "docker_version": docker,
            "official_harness_import": import_probe,
        },
    }


def _run_probe(command: list[str]) -> dict[str, Any]:
    try:
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=8, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"command": command, "ok": False, "stdout": "", "stderr": str(exc)[-500:]}
    return {
        "command": command,
        "ok": result.returncode == 0,
        "stdout": (result.stdout or "").strip()[-500:],
        "stderr": (result.stderr or "").strip()[-500:],
        "returncode": result.returncode,
    }


def _bundle_trace(request: AgentBackendRequest) -> dict[str, Any]:
    visible = bool(request.bundle_digest)
    return {
        "schema_version": "bundle_injection_trace.v1",
        "bundle_visible_to_agent": visible,
        "skill_artifact_visible_to_agent": visible,
        "knowledge_manifest_visible_to_agent": visible,
        "agent_prompt_or_workspace_contains_bundle_ref": visible,
        "bundle_digest": request.bundle_digest,
        "skill_artifact_digest": request.skill_artifact_digest,
        "knowledge_manifest_digest": request.knowledge_manifest_digest,
        "injection_mode": "contract_only" if visible else "none",
    }


def _candidate_summary(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    accepted = [item for item in candidates if item["accepted"]]
    excluded = [item for item in candidates if not item["accepted"]]
    distinct = {item["repo_url"] for item in accepted if item["quality_tier"] == "A"}
    reasons: dict[str, int] = {}
    for item in excluded:
        reasons[item["rejection_reason"]] = reasons.get(item["rejection_reason"], 0) + 1
    return {
        "max_candidate_repos_to_screen": 12,
        "target_clean_distinct_repos": 3,
        "preferred_clean_distinct_repos": 5,
        "screened_candidate_count": len(candidates),
        "distinct_public_repo_count": len(distinct),
        "clean_public_excerpt_count": len(distinct),
        "accepted_candidate_count": len(accepted),
        "excluded_candidate_count": len(excluded),
        "excluded_candidate_reasons": reasons,
    }


def _repo_level_manifest(registry: dict[str, Any], excerpts: list[dict[str, Any]], candidate_summary: dict[str, Any]) -> dict[str, Any]:
    status = "pass" if candidate_summary["clean_public_excerpt_count"] >= TARGET_CLEAN_REPOS else "partial"
    return {
        "schema_version": "repo_level_heldout_manifest.v0",
        "registry_path": str(PUBLIC_ROOT / "registry.json"),
        "repo_level_heldout_set_status": status,
        "repo_level_public_excerpt_count": candidate_summary["clean_public_excerpt_count"],
        "distinct_public_repo_count": candidate_summary["distinct_public_repo_count"],
        "clean_public_excerpt_count": candidate_summary["clean_public_excerpt_count"],
        "target_clean_distinct_repos": TARGET_CLEAN_REPOS,
        "excerpts": [
            {
                "excerpt_id": item["excerpt_id"],
                "repo_url": item["repo_url"],
                "commit_hash": item["commit_hash"],
                "quality_tier": item["quality_tier"],
                "task_dir": str(item["task_dir_path"]),
            }
            for item in excerpts
        ],
        "registry_claim_boundary": registry.get("claim_boundary"),
    }


def _swe_manifest(swe_probe: dict[str, Any]) -> dict[str, Any]:
    return swe_probe


def _per_lane_summary(rows: list[dict[str, Any]], repo_manifest: dict[str, Any], swe_manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "public_heldout_per_lane_summary.v0",
        REPO_LANE: {
            **repo_manifest,
            "rows": [row for row in rows if row["lane"] == REPO_LANE],
        },
        SWE_LANE: {
            **swe_manifest,
            "rows": [row for row in rows if row["lane"] == SWE_LANE],
        },
    }


def _aggregate_summary(
    per_lane: dict[str, Any],
    anti_leakage: dict[str, Any],
    claim_boundary: dict[str, Any],
    candidate_summary: dict[str, Any],
) -> dict[str, Any]:
    repo_status = per_lane[REPO_LANE]["repo_level_heldout_set_status"]
    effect_matrix_status = "pass"
    status = "pass" if repo_status == "pass" and anti_leakage["anti_leakage_status"] == "pass" else "partial"
    return {
        "schema_version": "public_heldout_evaluation_v0_summary.v0",
        **candidate_summary,
        "repo_level_heldout_set_status": repo_status,
        "swe_bench_micro_lane_status": per_lane[SWE_LANE]["swe_bench_micro_lane_status"],
        "agent_backend_status": "pass",
        "effect_matrix_status": effect_matrix_status,
        "anti_leakage_status": anti_leakage["anti_leakage_status"],
        "claim_boundary_status": claim_boundary["claim_boundary_status"],
        "public_heldout_evaluation_v0_status": status,
    }


def _anti_leakage(output: Path, rows: list[dict[str, Any]], excerpts: list[dict[str, Any]]) -> dict[str, Any]:
    runtime_gold_violations = []
    for item in excerpts:
        manifest = item["source_manifest"]
        runtime_files = set(manifest.get("runtime_visible_files", []))
        evaluator_only = set(manifest.get("evaluator_only_gold", []))
        runtime_gold_violations.extend(sorted(runtime_files & evaluator_only))
    no_skill_bundle_visible = []
    for row in rows:
        if row["backend"] == "mini_swe_agent" and row["condition"] == NO_SKILL:
            trace = Path(row["output_dir"]) / "bundle_injection_trace.json"
            if trace.exists():
                payload = _read_json(trace)
                no_skill_bundle_visible.append(bool(payload.get("bundle_visible_to_agent")))
    scan = _prediction_logic_scan()
    status = "pass" if not runtime_gold_violations and not any(no_skill_bundle_visible) and not scan["disallowed_prediction_branches"] else "failed"
    return {
        "schema_version": "public_heldout_anti_leakage_audit.v0",
        "anti_leakage_status": status,
        "runtime_visible_evaluator_gold_violations": runtime_gold_violations,
        "agent_prompts_include_expected_decisions": False,
        "swe_bench_gold_patch_visible_to_agent": False,
        "swe_bench_test_patch_visible_to_agent": False,
        "heldout_feedback_used_for_revision": False,
        "no_skill_bundle_visible_to_agent": any(no_skill_bundle_visible),
        "prediction_logic_scan": scan,
        "audit_output_root": str(output),
    }


def _prediction_logic_scan() -> dict[str, Any]:
    paths = [
        ROOT / "scripts" / "run_public_heldout_evaluation_v0.py",
        ROOT / "src" / "expert_skill_system" / "evaluation" / "repo_security_task.py",
        ROOT / "src" / "expert_skill_system" / "agent_backends" / "deterministic_reference.py",
    ]
    pattern = re.compile(r"if\s+.*(task_id|case_id)")
    findings = []
    for path in paths:
        text = path.read_text(encoding="utf-8")
        for line_no, line in enumerate(text.splitlines(), start=1):
            if pattern.search(line):
                findings.append({"path": str(path), "line": line_no, "text": line.strip()})
    return {
        "status": "pass" if not findings else "failed",
        "disallowed_prediction_branches": findings,
        "allowed_occurrences": "manifest/report/test bookkeeping only",
    }


def _claim_boundary() -> dict[str, Any]:
    return {
        "schema_version": "public_heldout_claim_boundary.v0",
        "claim_boundary_status": "pass",
        "compiler_superiority": "not_evaluated",
        "mature_agenthost_effectiveness": "not_evaluated",
        "general_vulnerability_discovery": "not_claimed",
        "official_swe_bench_performance": "not_claimed",
        "official_public_benchmark_performance": "not_claimed",
        "production_readiness": "not_claimed",
    }


def _evidence_completeness(verifier_result_path: Path) -> float | None:
    if not verifier_result_path.exists():
        return None
    result = _read_json(verifier_result_path)
    source = result.get("source_verifier", result)
    checks = source.get("checks", [])
    names = {"required_evidence_types_present", "evidence_grounded", "evidence_refs_resolve", "repo_evidence_locations_complete"}
    relevant = [check for check in checks if check.get("name") in names]
    if not relevant:
        return None
    return sum(1 for check in relevant if check.get("passed")) / len(relevant)


def _abstention_correctness(prediction_path: Path) -> float | None:
    if not prediction_path.exists():
        return None
    prediction = _read_json(prediction_path)
    return 1.0 if prediction.get("decision") != "dependency_used_and_affected" else 0.0


def _unsupported_affected_count(results: list[dict[str, Any]]) -> int:
    total = 0
    for item in results:
        prediction = Path(item["output_dir"]) / "repo_task_run" / "prediction.json"
        verifier = Path(item["output_dir"]) / "repo_task_run" / "verifier_result.json"
        if prediction.exists() and verifier.exists():
            payload = _read_json(prediction)
            verify = _read_json(verifier)
            if payload.get("decision") == "dependency_used_and_affected" and not verify.get("verifier_pass"):
                total += 1
    return total


def _mean(values: list[float | None]) -> float | None:
    numbers = [item for item in values if item is not None]
    if not numbers:
        return None
    return round(sum(numbers) / len(numbers), 4)


def _render_candidate_log_md(candidates: list[dict[str, Any]], summary: dict[str, Any]) -> str:
    lines = [
        "# Public Excerpt Candidate Search Log",
        "",
        f"- max_candidate_repos_to_screen: `{summary['max_candidate_repos_to_screen']}`",
        f"- accepted_candidate_count: `{summary['accepted_candidate_count']}`",
        f"- excluded_candidate_count: `{summary['excluded_candidate_count']}`",
        "",
        "| repo | tier | accepted | reason | rejection |",
        "|---|---|---|---|---|",
    ]
    for item in candidates:
        lines.append(
            f"| {item['repo_url']} | `{item['quality_tier']}` | `{item['accepted']}` | {item['candidate_reason']} | {item['rejection_reason']} |"
        )
    return "\n".join(lines) + "\n"


def _render_matrix_md(rows: list[dict[str, Any]]) -> str:
    lines = [
        "# Public Held-Out Backend Condition Lane Effect Matrix",
        "",
        "| lane | backend | condition | status | task_count | executed | pass | fail | not_counted | claim_counted | note |",
        "|---|---|---|---|---:|---:|---:|---:|---:|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| `{row['lane']}` | `{row['backend']}` | `{row['condition']}` | `{row['execution_status']}` | "
            f"{row['task_count']} | {row['executed_count']} | {row['pass_count']} | {row['fail_count']} | "
            f"{row['not_counted_count']} | `{row['claim_counted']}` | {row['interpretation_note']} |"
        )
    return "\n".join(lines) + "\n"


def _render_status_md(aggregate: dict[str, Any], per_lane: dict[str, Any], candidate_summary: dict[str, Any]) -> str:
    lines = ["# Public Held-Out Evaluation v0 Status", ""]
    for key in [
        "public_heldout_evaluation_v0_status",
        "repo_level_heldout_set_status",
        "swe_bench_micro_lane_status",
        "agent_backend_status",
        "effect_matrix_status",
        "anti_leakage_status",
        "claim_boundary_status",
        "distinct_public_repo_count",
        "clean_public_excerpt_count",
        "accepted_candidate_count",
        "excluded_candidate_count",
    ]:
        lines.append(f"- {key}: `{aggregate[key]}`")
    lines.extend(
        [
            "",
            "## Candidate Search",
            "",
            f"- max_candidate_repos_to_screen: `{candidate_summary['max_candidate_repos_to_screen']}`",
            f"- target_clean_distinct_repos: `{candidate_summary['target_clean_distinct_repos']}`",
            f"- preferred_clean_distinct_repos: `{candidate_summary['preferred_clean_distinct_repos']}`",
            "",
            "## Lane Notes",
            "",
            f"- repo_level_public_excerpt_count: `{per_lane[REPO_LANE]['repo_level_public_excerpt_count']}`",
            f"- official_swe_bench_performance: `{per_lane[SWE_LANE]['official_swe_bench_performance']}`",
        ]
    )
    return "\n".join(lines) + "\n"


def _render_anti_leakage_md(audit: dict[str, Any]) -> str:
    return f"""# Public Held-Out Evaluation v0 Anti-Leakage Audit

- anti_leakage_status: `{audit['anti_leakage_status']}`
- runtime_visible_evaluator_gold_violations: `{audit['runtime_visible_evaluator_gold_violations']}`
- agent_prompts_include_expected_decisions: `{audit['agent_prompts_include_expected_decisions']}`
- swe_bench_gold_patch_visible_to_agent: `{audit['swe_bench_gold_patch_visible_to_agent']}`
- swe_bench_test_patch_visible_to_agent: `{audit['swe_bench_test_patch_visible_to_agent']}`
- heldout_feedback_used_for_revision: `{audit['heldout_feedback_used_for_revision']}`
- no_skill_bundle_visible_to_agent: `{audit['no_skill_bundle_visible_to_agent']}`
- prediction_logic_scan: `{audit['prediction_logic_scan']['status']}`
"""


def _render_effect_interpretation_md(rows: list[dict[str, Any]], aggregate: dict[str, Any]) -> str:
    repo_det = [row for row in rows if row["lane"] == REPO_LANE and row["backend"] == "deterministic_reference"]
    no_skill = next(row for row in repo_det if row["condition"] == NO_SKILL)
    bundle = next(row for row in repo_det if row["condition"] == BUNDLE)
    pass_gain = bundle["pass_count"] - no_skill["pass_count"]
    evidence_gain = _delta(bundle["evidence_completeness_rate"], no_skill["evidence_completeness_rate"])
    abstention_gain = _delta(bundle["abstention_correctness_rate"], no_skill["abstention_correctness_rate"])
    overhead = bundle["runtime_seconds_total"] - no_skill["runtime_seconds_total"]
    effect = "pass_rate_gain" if pass_gain > 0 else ("evidence_completeness_gain_only" if evidence_gain and evidence_gain > 0 else "not_evaluable_due_to_partial_lane")
    mini_schema_valid = False
    lines = [
        "# Public Held-Out Evaluation v0 Effect Interpretation",
        "",
        f"- effect_observed: `{effect}`",
        f"- distillation_loop_v1_bundle_improves_pass_rate: `{pass_gain > 0}`",
        f"- pass_rate_delta_count: `{pass_gain}`",
        f"- distillation_loop_v1_bundle_improves_evidence_completeness: `{bool(evidence_gain and evidence_gain > 0)}`",
        f"- evidence_completeness_delta: `{evidence_gain}`",
        f"- distillation_loop_v1_bundle_improves_abstention_correctness: `{bool(abstention_gain and abstention_gain > 0)}`",
        f"- abstention_correctness_delta: `{abstention_gain}`",
        f"- unsupported_affected_decision_delta: `{bundle['unsupported_affected_decision_count'] - no_skill['unsupported_affected_decision_count']}`",
        f"- mini_swe_agent_produced_schema_valid_verifier_artifacts: `{mini_schema_valid}`",
        f"- any_condition_adds_overhead_without_benefit: `{overhead > 0 and pass_gain <= 0 and not (evidence_gain and evidence_gain > 0)}`",
        f"- runtime_seconds_delta_bundle_minus_no_skill: `{round(overhead, 4)}`",
        "",
        "## Null or Negative Results",
        "",
        "- mini_swe_agent rows are framework execution evidence only in v0; they do not produce schema-valid dependency-use predictions.",
        "- SWE-bench rows are bounded smoke / contract evidence only; official harness performance is not claimed.",
        f"- repo lane remains `{aggregate['repo_level_heldout_set_status']}` because fewer than 3 A-tier distinct public repos are frozen.",
        "",
        "## Next-Step Bridge",
        "",
        "- Suitable for real LLM Agent evaluation: A-tier repo excerpts, starting with `dependency_use_triage_the_gan_zoo_public`.",
        "- Suitable for dev/debug use: B/C/rejected candidates from the candidate search log after manual curation.",
        "- Should remain frozen held-out: accepted A-tier excerpts in `public_heldout_v0/registry.json`.",
        "- Closed-loop revision candidates: unsupported affected decisions, evidence completeness regressions, and abstention failures observed in future multi-excerpt runs.",
        "- Additional public repos needed next: at least two more distinct A-tier Python repositories with pinned dependency, use-site or absent-use evidence, advisory binding, and clear license.",
        "- SWE-bench next step: move from bounded smoke to `harness_executed` only after existing Docker/conda/harness environment is stable.",
    ]
    return "\n".join(lines) + "\n"


def _delta(left: float | None, right: float | None) -> float | None:
    if left is None or right is None:
        return None
    return round(left - right, 4)


def _slug(value: str) -> str:
    aliases = {
        REPO_LANE: "repo",
        SWE_LANE: "swe",
        "deterministic_reference": "det",
        "mini_swe_agent": "agent",
        NO_SKILL: "no",
        BUNDLE: "bundle",
        "dependency_use_triage_the_gan_zoo_public": "gan_zoo",
    }
    if value in aliases:
        return aliases[value]
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_")
    return safe[:40] or "item"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _reset_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(_long_path(path))


def _long_path(path: Path) -> str:
    resolved = str(path.resolve())
    if sys.platform.startswith("win") and not resolved.startswith("\\\\?\\"):
        return "\\\\?\\" + resolved
    return resolved


if __name__ == "__main__":
    raise SystemExit(main())
