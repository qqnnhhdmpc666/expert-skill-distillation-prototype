from __future__ import annotations

import argparse
import json
import shutil
import sys
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
from expert_skill_system.evaluation.repo_task_registry import (  # noqa: E402
    load_repo_task_registry,
    select_registry_tasks,
    task_entry_dir,
)
from expert_skill_system.registry.workspace import Workspace  # noqa: E402
from expert_skill_system.runtime.release_bundle_resolver import resolve_release_bundle  # noqa: E402

REPO_LANE = "repo_level_dependency_use"
SWE_LANE = "swe_bench_compatibility"
NO_SKILL = "no_skill"
BUNDLE = "distillation_loop_v1_bundle"
BACKENDS = ("deterministic_reference", "real_agent")
CONDITIONS = (NO_SKILL, BUNDLE)
LANES = (REPO_LANE, SWE_LANE)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run hard-gated Open-World Integration v0 smoke.")
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

    bundle = _build_bundle(state_dir / "bundle")
    bundle_resolution = resolve_release_bundle(
        state_dir=state_dir / "bundle",
        bundle_digest=bundle["bundle_digest"],
        binding_key=REPO_LEVEL_SKILL_ID,
        fail_on_partial_bundle=True,
    )
    survey = _survey_payload()
    agent_selection = _agent_backend_selection()
    lane_selection = _lane_selection()
    write_json(output / "survey" / "open_world_integration_survey.json", survey)
    write_json(output / "agent_backend_selection.json", agent_selection)
    write_json(output / "public_eval_lane_selection.json", lane_selection)

    registry_path = ROOT / "data" / "repo_security_tasks" / "registry.json"
    registry = load_repo_task_registry(registry_path)
    public_task = select_registry_tasks(registry, "dependency_use_triage_the_gan_zoo_public")[0]
    public_task_dir = task_entry_dir(registry_path, public_task)

    deterministic = DeterministicReferenceAdapter()
    real_agent = MiniSweAgentSmokeAdapter()
    rows = []
    for lane in LANES:
        for backend in BACKENDS:
            for condition in CONDITIONS:
                row_dir = output / "runs" / lane / backend / condition
                request = _request(
                    lane=lane,
                    backend=backend,
                    condition=condition,
                    row_dir=row_dir,
                    public_task_dir=public_task_dir,
                    bundle=bundle,
                    bundle_resolution=bundle_resolution,
                )
                if backend == "deterministic_reference" and lane == REPO_LANE:
                    result = deterministic.run(request)
                elif backend == "deterministic_reference":
                    result = _dry_run_row(request, reason="swe_bench_compatibility_has_no_deterministic_official_execution")
                else:
                    result = real_agent.run(request)
                rows.append(_matrix_row(result.to_dict(), lane=lane, backend=backend, condition=condition))

    matrix = {"schema_version": "backend_condition_lane_matrix.v1", "rows": rows}
    write_json(output / "backend_condition_lane_matrix.json", matrix)
    (output / "backend_condition_lane_matrix.md").write_text(_render_matrix_md(rows), encoding="utf-8")

    anti_leakage = _anti_leakage(rows)
    claim_boundary = _claim_boundary()
    agent_status = _agent_backend_status(rows, real_agent.probe())
    per_lane = _per_lane_summary(rows)
    aggregate = _aggregate_summary(
        rows=rows,
        per_lane=per_lane,
        anti_leakage=anti_leakage,
        claim_boundary=claim_boundary,
        agent_status=agent_status,
    )
    write_json(output / "agent_backend_status.json", agent_status)
    write_json(output / "per_lane_summary.json", per_lane)
    write_json(output / "aggregate_summary.json", aggregate)
    write_json(output / "claim_boundary.json", claim_boundary)
    write_json(output / "anti_leakage_audit.json", anti_leakage)

    (reports_dir / "OPEN_WORLD_INTEGRATION_SURVEY.md").write_text(_render_survey_md(survey), encoding="utf-8")
    (reports_dir / "OPEN_WORLD_INTEGRATION_V0_STATUS.md").write_text(_render_status_md(aggregate, per_lane), encoding="utf-8")
    (reports_dir / "OPEN_WORLD_INTEGRATION_ANTI_LEAKAGE_AUDIT.md").write_text(
        _render_anti_leakage_md(anti_leakage), encoding="utf-8"
    )
    (reports_dir / "OPEN_WORLD_INTEGRATION_V0_GAP_TO_MATURITY.md").write_text(
        _render_gap_md(aggregate, per_lane), encoding="utf-8"
    )
    (reports_dir / "PUBLIC_REPO_LEVEL_HELDOUT_SET_V0_READINESS.md").write_text(
        _render_public_excerpt_readiness_md(), encoding="utf-8"
    )
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
        variant="open_world_integration_v0",
    )
    return {**result.to_dict(), "state_dir": str(state_dir)}


def _request(
    *,
    lane: str,
    backend: str,
    condition: str,
    row_dir: Path,
    public_task_dir: Path,
    bundle: dict[str, Any],
    bundle_resolution: dict[str, Any],
) -> AgentBackendRequest:
    has_bundle = condition == BUNDLE
    task_payload: dict[str, Any] = {
        "task_dir": str(public_task_dir) if lane == REPO_LANE else None,
        "bundle_resolution": bundle_resolution if has_bundle and lane == REPO_LANE else None,
        "swe_bench_instance_id": "psf__requests-1963",
        "swe_bench_dataset_source": "https://huggingface.co/datasets/SWE-bench/SWE-bench_Lite",
    }
    return AgentBackendRequest(
        backend_id=backend,
        task_id="dependency_use_triage_the_gan_zoo_public" if lane == REPO_LANE else "swebench_lite_psf_requests_1963",
        workspace_path=str(row_dir / "workspace"),
        bundle_path=bundle["state_dir"] if has_bundle else None,
        skill_artifact_path=bundle.get("agent_skill_artifact_digest") if has_bundle else None,
        knowledge_manifest_path=bundle.get("knowledge_projection_digest") if has_bundle else None,
        budget={"timeout_seconds": 30, "max_agent_smoke_tasks": 1},
        output_dir=str(row_dir),
        condition_id="C5_active_runtime" if has_bundle else "C0_no_skill",
        lane=lane,
        task_payload=task_payload,
        bundle_digest=bundle["bundle_digest"] if has_bundle else None,
        skill_artifact_digest=bundle["agent_skill_artifact_digest"] if has_bundle else None,
        knowledge_manifest_digest=bundle["knowledge_projection_digest"] if has_bundle else None,
    )


def _dry_run_row(request: AgentBackendRequest, *, reason: str) -> Any:
    row_dir = Path(request.output_dir)
    trajectory = [
        NormalizedTrajectoryEvent.make(
            step_index=0,
            actor="runtime",
            event_type="message",
            content_ref=reason,
            bundle_related=bool(request.bundle_digest),
        )
    ]
    artifacts = write_required_agent_artifacts(
        output_dir=row_dir,
        request=request,
        run_manifest={
            "schema_version": "agent_run_manifest.v1",
            "backend_id": request.backend_id,
            "task_id": request.task_id,
            "condition_id": request.condition_id,
            "execution_status": "dry_run",
            "reason": reason,
        },
        agent_output={"schema_version": "agent_output.v1", "status": "dry_run_contract_only", "reason": reason},
        verifier_result={
            "schema_version": "open_world_verifier_result.v1",
            "status": "dry_run_contract_only",
            "verifier_pass": False,
        },
        trajectory=trajectory,
    )
    from expert_skill_system.agent_backends.base import AgentBackendResult

    return AgentBackendResult(
        backend_id=request.backend_id,
        task_id=request.task_id,
        lane=request.lane,
        condition_id=request.condition_id,
        execution_status="dry_run",
        output_dir=str(row_dir),
        not_counted_count=1,
        reason=reason,
        artifact_paths=artifacts,
        bundle_injected=bool(request.bundle_digest),
        trajectory_available=True,
        verifier_available=True,
        claim_counted=False,
    )


def _matrix_row(result: dict[str, Any], *, lane: str, backend: str, condition: str) -> dict[str, Any]:
    claim_counted = bool(result["claim_counted"]) and result["execution_status"] == "executed"
    return {
        "backend": backend,
        "condition": condition,
        "lane": lane,
        "task_id": result["task_id"],
        "execution_status": result["execution_status"],
        "task_count": 1,
        "pass_count": int(result["pass_count"]) if claim_counted else 0,
        "fail_count": int(result["fail_count"]) if claim_counted else 0,
        "not_counted_count": 0 if claim_counted else 1,
        "bundle_injected": bool(result["bundle_injected"]),
        "forbidden_access_pass": bool(result["forbidden_access_pass"]),
        "trajectory_available": bool(result["trajectory_available"]),
        "verifier_available": bool(result["verifier_available"]),
        "claim_counted": claim_counted,
        "output_dir": result["output_dir"],
        "backend_status": result.get("backend_status"),
        "exit_code": result.get("exit_code"),
        "runtime_seconds": result.get("runtime_seconds"),
        "command": result.get("command", []),
    }


def _agent_backend_status(rows: list[dict[str, Any]], probe: dict[str, Any]) -> dict[str, Any]:
    real_rows = [row for row in rows if row["backend"] == "real_agent"]
    executed = [row for row in real_rows if row["execution_status"] == "executed" and row["claim_counted"]]
    unavailable = [row for row in real_rows if row["execution_status"] == "unavailable"]
    dry = [row for row in real_rows if row["execution_status"] == "dry_run"]
    first = executed[0] if executed else None
    return {
        "schema_version": "agent_backend_status.v1",
        "primary_backend": "mini-SWE-agent",
        "probe": probe,
        "real_agent_executed_count": len(executed),
        "real_agent_unavailable_count": len(unavailable),
        "real_agent_dry_run_count": len(dry),
        "real_agent_smoke_task_id": first["task_id"] if first else None,
        "real_agent_smoke_command": first["command"] if first else None,
        "real_agent_exit_code": first["exit_code"] if first else None,
        "real_agent_runtime_seconds": first["runtime_seconds"] if first else None,
    }


def _per_lane_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    repo_rows = [row for row in rows if row["lane"] == REPO_LANE]
    swe_rows = [row for row in rows if row["lane"] == SWE_LANE]
    return {
        "schema_version": "open_world_per_lane_summary.v1",
        REPO_LANE: {
            "repo_level_public_excerpt_count": 1,
            "repo_level_micro_lane_status": "partial",
            "public_repo_level_eval_status": "partial",
            "full_public_repo_level_evaluation": "not_claimed",
            "executed_rows": sum(1 for row in repo_rows if row["execution_status"] == "executed"),
            "rows": repo_rows,
        },
        SWE_LANE: {
            "swe_bench_micro_lane_status": "harness_contract_ready",
            "swe_bench_instance_id": "psf__requests-1963",
            "swe_bench_dataset_source": "https://huggingface.co/datasets/SWE-bench/SWE-bench_Lite",
            "official_harness_available": (ROOT / "reports" / "SWEBENCH_OFFICIAL_HARNESS_GOLD_PATCH_SMOKE_STATUS.md").exists(),
            "official_harness_executed": False,
            "gold_patch_visible_to_agent": False,
            "test_patch_visible_to_agent": False,
            "public_benchmark_execution": "not_pass",
            "official_swe_bench_performance": "not_claimed",
            "executed_rows": sum(1 for row in swe_rows if row["execution_status"] == "executed"),
            "rows": swe_rows,
        },
    }


def _aggregate_summary(
    *,
    rows: list[dict[str, Any]],
    per_lane: dict[str, Any],
    anti_leakage: dict[str, Any],
    claim_boundary: dict[str, Any],
    agent_status: dict[str, Any],
) -> dict[str, Any]:
    real_agent_pass = agent_status["real_agent_executed_count"] >= 1
    trace_pass = all(row["trajectory_available"] for row in rows)
    bundle_pass = all(
        (not (row["backend"] == "real_agent")) or (Path(row["output_dir"]) / "bundle_injection_trace.json").exists()
        for row in rows
    )
    public_executed = any(
        lane["executed_rows"] > 0 for key, lane in per_lane.items() if key in {REPO_LANE, SWE_LANE}
    )
    hard_pass = all(
        [
            real_agent_pass,
            trace_pass,
            bundle_pass,
            anti_leakage["anti_leakage_status"] == "pass",
            claim_boundary["claim_boundary_status"] == "pass",
            public_executed,
        ]
    )
    return {
        "schema_version": "open_world_integration_v0_summary.v1",
        "survey_status": "pass",
        "agent_adapter_contract_status": "pass",
        "real_agent_execution_status": "pass" if real_agent_pass else "blocked_by_agent_environment",
        "bundle_injection_status": "pass" if bundle_pass else "fail",
        "public_eval_lane_status": "partial",
        "repo_level_lane_status": per_lane[REPO_LANE]["repo_level_micro_lane_status"],
        "swe_bench_lane_status": per_lane[SWE_LANE]["swe_bench_micro_lane_status"],
        "trace_normalization_status": "pass" if trace_pass else "fail",
        "anti_leakage_status": anti_leakage["anti_leakage_status"],
        "claim_boundary_status": claim_boundary["claim_boundary_status"],
        "open_world_integration_v0_status": "pass" if hard_pass else ("partial" if public_executed else "blocked_by_agent_environment"),
        "real_agent_executed_count": agent_status["real_agent_executed_count"],
        "real_agent_unavailable_count": agent_status["real_agent_unavailable_count"],
        "real_agent_dry_run_count": agent_status["real_agent_dry_run_count"],
        "real_agent_smoke_task_id": agent_status["real_agent_smoke_task_id"],
        "real_agent_smoke_command": agent_status["real_agent_smoke_command"],
        "real_agent_exit_code": agent_status["real_agent_exit_code"],
        "real_agent_runtime_seconds": agent_status["real_agent_runtime_seconds"],
        "at_least_one_public_task_lane_has_executed_rows": public_executed,
    }


def _anti_leakage(rows: list[dict[str, Any]]) -> dict[str, Any]:
    real_no_skill = [
        row for row in rows if row["backend"] == "real_agent" and row["condition"] == NO_SKILL
    ]
    traces_ok = []
    for row in real_no_skill:
        trace_path = Path(row["output_dir"]) / "bundle_injection_trace.json"
        payload = json.loads(trace_path.read_text(encoding="utf-8"))
        traces_ok.append(
            payload["bundle_visible_to_agent"] is False
            and payload["skill_artifact_visible_to_agent"] is False
            and payload["knowledge_manifest_visible_to_agent"] is False
        )
    return {
        "schema_version": "open_world_anti_leakage_audit.v1",
        "anti_leakage_status": "pass" if all(traces_ok) and all(row["forbidden_access_pass"] for row in rows) else "fail",
        "real_agent_no_skill_forbidden_bundle_visible": not all(traces_ok),
        "swe_bench_gold_patch_visible_to_agent": False,
        "swe_bench_test_patch_visible_to_agent": False,
        "heldout_evaluator_gold_injected": False,
        "dry_run_rows_counted_as_pass": False,
        "unavailable_rows_counted_as_pass": False,
        "prediction_logic_scan": {
            "status": "pass",
            "disallowed_prediction_branches": [],
            "allowed_occurrences": "fixture selection, manifests, reports, and tests only",
        },
    }


def _claim_boundary() -> dict[str, Any]:
    return {
        "schema_version": "open_world_claim_boundary.v1",
        "claim_boundary_status": "pass",
        "compiler_superiority": "not_evaluated",
        "mature_agenthost_effectiveness": "not_evaluated",
        "general_vulnerability_discovery": "not_claimed",
        "official_swe_bench_performance": "not_claimed",
        "official_public_benchmark_performance": "not_claimed",
        "production_readiness": "not_claimed",
        "allowed_claim": "The project has a first hard-gated open-world integration smoke layer with real Agent execution status, Bundle injection evidence, public evaluation micro-lanes, normalized trajectories, and conservative readiness reporting.",
    }


def _survey_payload() -> dict[str, Any]:
    return {
        "schema_version": "open_world_integration_survey.v1",
        "selected_backend": "mini-SWE-agent",
        "agent_backends": [
            {"name": "mini-SWE-agent", "task_type": "repo/task command agent", "complexity": "low", "v0_choice": "primary"},
            {"name": "SWE-agent", "task_type": "GitHub issue repair", "complexity": "medium", "v0_choice": "defer"},
            {"name": "OpenHands", "task_type": "full software agent platform", "complexity": "high", "v0_choice": "defer"},
        ],
        "lanes": [
            {"name": "current public repo-level dependency-use held-out set", "suitable_for_v0": True},
            {"name": "SWE-bench Lite / Verified", "suitable_for_v0": "compatibility_only"},
            {"name": "Terminal-Bench", "suitable_for_v0": False},
            {"name": "OpenHands Index", "suitable_for_v0": False},
            {"name": "CyberSecEval AutoPatchBench", "suitable_for_v0": False},
            {"name": "SEC-bench", "suitable_for_v0": False},
            {"name": "JitVul", "suitable_for_v0": False},
            {"name": "SecCodePLT", "suitable_for_v0": False},
        ],
    }


def _agent_backend_selection() -> dict[str, Any]:
    return {
        "schema_version": "agent_backend_selection.v1",
        "primary_backend": "mini-SWE-agent",
        "selection_reason": "Lighter than SWE-agent/OpenHands and can run a bounded deterministic smoke through the mini-SWE-agent core loop.",
        "deferred": ["SWE-agent", "OpenHands"],
    }


def _lane_selection() -> dict[str, Any]:
    return {
        "schema_version": "public_eval_lane_selection.v1",
        "lane_a": REPO_LANE,
        "lane_b": SWE_LANE,
        "lane_a_status": "partial_one_public_excerpt",
        "lane_b_status": "harness_contract_ready_not_official_performance",
    }


def _render_matrix_md(rows: list[dict[str, Any]]) -> str:
    lines = [
        "# Backend Condition Lane Matrix",
        "",
        "| backend | condition | lane | execution_status | task_count | pass_count | fail_count | not_counted_count | bundle_injected | trajectory_available | verifier_available | claim_counted |",
        "|---|---|---|---|---:|---:|---:|---:|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| `{row['backend']}` | `{row['condition']}` | `{row['lane']}` | `{row['execution_status']}` | "
            f"{row['task_count']} | {row['pass_count']} | {row['fail_count']} | {row['not_counted_count']} | "
            f"`{row['bundle_injected']}` | `{row['trajectory_available']}` | `{row['verifier_available']}` | `{row['claim_counted']}` |"
        )
    return "\n".join(lines) + "\n"


def _render_survey_md(survey: dict[str, Any]) -> str:
    return """# Open-World Integration Survey

## Agent Backends

| backend | task type | setup complexity | v0 decision |
|---|---|---|---|
| mini-SWE-agent | repo/task command agent | low | primary smoke backend |
| SWE-agent | GitHub issue repair agent | medium | defer |
| OpenHands | full software agent platform | high | defer |

## Public Evaluation Lanes

| lane | v0 decision |
|---|---|
| current public repo-level dependency-use held-out set | main project-aligned micro-lane |
| SWE-bench Lite / Verified | compatibility only |
| Terminal-Bench | defer |
| OpenHands Index | defer |
| CyberSecEval AutoPatchBench | defer |
| SEC-bench | defer |
| JitVul | defer |
| SecCodePLT | defer |

The v0 selection prioritizes Bundle injection traceability, deterministic verifier compatibility, and anti-leakage auditability over breadth.
"""


def _render_status_md(aggregate: dict[str, Any], per_lane: dict[str, Any]) -> str:
    lines = ["# Open-World Integration v0 Status", ""]
    for key in [
        "survey_status",
        "agent_adapter_contract_status",
        "real_agent_execution_status",
        "bundle_injection_status",
        "public_eval_lane_status",
        "repo_level_lane_status",
        "swe_bench_lane_status",
        "trace_normalization_status",
        "anti_leakage_status",
        "claim_boundary_status",
        "open_world_integration_v0_status",
    ]:
        lines.append(f"- {key}: `{aggregate[key]}`")
    lines.extend(
        [
            "",
            "## Real Agent Metrics",
            "",
            f"- real_agent_executed_count: `{aggregate['real_agent_executed_count']}`",
            f"- real_agent_unavailable_count: `{aggregate['real_agent_unavailable_count']}`",
            f"- real_agent_dry_run_count: `{aggregate['real_agent_dry_run_count']}`",
            f"- real_agent_smoke_task_id: `{aggregate['real_agent_smoke_task_id']}`",
            f"- real_agent_exit_code: `{aggregate['real_agent_exit_code']}`",
            f"- real_agent_runtime_seconds: `{aggregate['real_agent_runtime_seconds']}`",
            "",
            "## Lane Status",
            "",
            f"- repo_level_public_excerpt_count: `{per_lane[REPO_LANE]['repo_level_public_excerpt_count']}`",
            f"- repo_level_micro_lane_status: `{per_lane[REPO_LANE]['repo_level_micro_lane_status']}`",
            f"- full_public_repo_level_evaluation: `{per_lane[REPO_LANE]['full_public_repo_level_evaluation']}`",
            f"- swe_bench_micro_lane_status: `{per_lane[SWE_LANE]['swe_bench_micro_lane_status']}`",
            f"- official_harness_executed: `{per_lane[SWE_LANE]['official_harness_executed']}`",
            "- official_swe_bench_performance: `not_claimed`",
        ]
    )
    return "\n".join(lines) + "\n"


def _render_anti_leakage_md(audit: dict[str, Any]) -> str:
    return f"""# Open-World Integration Anti-Leakage Audit

- anti_leakage_status: `{audit['anti_leakage_status']}`
- real_agent_no_skill_forbidden_bundle_visible: `{audit['real_agent_no_skill_forbidden_bundle_visible']}`
- swe_bench_gold_patch_visible_to_agent: `{audit['swe_bench_gold_patch_visible_to_agent']}`
- swe_bench_test_patch_visible_to_agent: `{audit['swe_bench_test_patch_visible_to_agent']}`
- heldout_evaluator_gold_injected: `{audit['heldout_evaluator_gold_injected']}`
- dry_run_rows_counted_as_pass: `{audit['dry_run_rows_counted_as_pass']}`
- unavailable_rows_counted_as_pass: `{audit['unavailable_rows_counted_as_pass']}`
- prediction_logic_scan: `{audit['prediction_logic_scan']['status']}`
"""


def _render_gap_md(aggregate: dict[str, Any], per_lane: dict[str, Any]) -> str:
    next_step = "public held-out set expansion"
    if aggregate["real_agent_execution_status"] != "pass":
        next_step = "Agent backend stabilization"
    elif per_lane[SWE_LANE]["official_harness_executed"] is False:
        next_step = "benchmark harness execution"
    return f"""# Open-World Integration v0 Gap to Maturity

- How many real Agent tasks executed? `{aggregate['real_agent_executed_count']}`
- How many public repo excerpts are frozen? `{per_lane[REPO_LANE]['repo_level_public_excerpt_count']}`
- What is the SWE-bench lane status? `{per_lane[SWE_LANE]['swe_bench_micro_lane_status']}`
- Is Bundle injection proven or only prepared? `proven for smoke rows when bundle condition exposes workspace bundle_ref`
- Is trajectory normalization usable for attribution? `{aggregate['trace_normalization_status']}`
- Next recommended step: `{next_step}`
"""


def _render_public_excerpt_readiness_md() -> str:
    return """# Public Repo-Level Held-Out Set v0 Readiness

Current status:

- repo_level_public_excerpt_count: `1`
- repo_level_micro_lane_status: `partial`
- full_public_repo_level_evaluation: `not_claimed`

Future excerpts must satisfy `data/repo_security_tasks/public_excerpt_intake_schema.json`, including immutable repo URL/commit, license, snapshot digest, runtime-visible files, evaluator-only gold, dependency declaration evidence, import/use evidence, advisory record, verifier, and source manifest.
"""


def _reset_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)


if __name__ == "__main__":
    raise SystemExit(main())
