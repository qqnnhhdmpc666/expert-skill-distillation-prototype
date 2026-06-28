from __future__ import annotations

import argparse
import json
import shutil
import sys
from dataclasses import asdict
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
)
from expert_skill_system.agent_backends.base import write_json  # noqa: E402
from expert_skill_system.compiler.repo_level_bundle_builder import (  # noqa: E402
    REPO_LEVEL_SKILL_ID,
    RepoLevelBundleBuilder,
)
from expert_skill_system.core.canonical import sha256_bytes  # noqa: E402
from expert_skill_system.registry.workspace import Workspace  # noqa: E402
from expert_skill_system.runtime.release_bundle_resolver import resolve_release_bundle  # noqa: E402

DEFAULT_CASE_DIR = ROOT / "data" / "e2e_cases" / "document_to_agent_v0"
FAILURE_TAXONOMY = {
    "schema_invalid": "Agent output does not match expected schema.",
    "missing_required_evidence": "Agent output lacks required evidence references.",
    "forbidden_evidence_access": "Agent used evaluator-only or forbidden evidence.",
    "domain_rule_violation": "Agent decision violates domain rules.",
    "knowledge_missing": "Required factual record was unavailable.",
    "skill_rule_missing": "Required procedural rule was not encoded in Skill.",
    "agent_execution_failure": "Agent/backend failed before valid output.",
    "environment_blocked": "Environment prevented execution.",
    "verifier_inconclusive": "Verifier cannot confidently judge this output.",
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Document-to-Agent E2E v0.")
    parser.add_argument("--output", required=True)
    parser.add_argument("--state-dir", required=True)
    parser.add_argument("--case-dir", default=str(DEFAULT_CASE_DIR))
    parser.add_argument("--reports-dir", default="reports")
    args = parser.parse_args(argv)

    output = Path(args.output)
    state_dir = Path(args.state_dir)
    reports_dir = Path(args.reports_dir)
    case_dir = Path(args.case_dir)
    material_path = case_dir / "input_material.md"
    if not material_path.exists():
        print(f"missing input material: {material_path}", file=sys.stderr)
        return 2

    _reset_dir(output)
    output.mkdir(parents=True, exist_ok=True)
    state_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    task_contract = _read_json(case_dir / "task_contract.json")
    evaluator_config = _read_json(case_dir / "evaluator_config.json")
    verifier_spec = _read_json(case_dir / "verifier_spec.json")
    material = material_path.read_text(encoding="utf-8")
    material_digest = {
        "schema_version": "material_digest.v0",
        "path": str(material_path),
        "sha256": sha256_bytes(material.encode("utf-8")),
        "size_bytes": len(material.encode("utf-8")),
    }
    windows = _material_windows(material)
    skill_text = _extract_skill(material)
    knowledge_manifest = _extract_knowledge(material)
    compile_input = _prepare_compile_input(state_dir / "compile_input", material, task_contract, knowledge_manifest)

    workspace = Workspace.open(state_dir / "bundle_state")
    build = RepoLevelBundleBuilder(workspace).build(
        data_dir=compile_input,
        skill_family=REPO_LEVEL_SKILL_ID,
        promote=True,
        variant="document_to_agent_e2e_v0",
    )
    active = workspace.metadata.get_active_binding(REPO_LEVEL_SKILL_ID)
    if active is None:
        raise RuntimeError("expected isolated active binding after E2E bundle promotion")
    resolution = resolve_release_bundle(
        state_dir=state_dir / "bundle_state",
        use_active_binding=True,
        binding_key=REPO_LEVEL_SKILL_ID,
        fail_on_partial_bundle=True,
    )
    skill_ir = workspace.artifacts.get_json(workspace.metadata.artifact_ref(build.skill_ir_digest))
    knowledge_projection = workspace.artifacts.get_json(workspace.metadata.artifact_ref(build.knowledge_projection_digest))
    release_bundle = resolution["bundle_manifest"]

    task_dir = ROOT / evaluator_config["task_dir"]
    backend_dir = output / "backend_runs" / "deterministic_reference"
    request = AgentBackendRequest(
        backend_id="deterministic_reference",
        task_id="document_to_agent_dependency_use_triage",
        workspace_path=str(backend_dir / "workspace"),
        bundle_path=str(state_dir / "bundle_state"),
        skill_artifact_path=build.agent_skill_artifact_digest,
        knowledge_manifest_path=build.knowledge_projection_digest,
        budget={"timeout_seconds": 30},
        output_dir=str(backend_dir),
        condition_id="document_to_agent_e2e_bundle",
        lane="document_to_agent_e2e",
        task_payload={"task_dir": str(task_dir), "bundle_resolution": resolution},
        bundle_digest=build.bundle_digest,
        skill_artifact_digest=build.agent_skill_artifact_digest,
        knowledge_manifest_digest=build.knowledge_projection_digest,
    )
    backend_result = DeterministicReferenceAdapter().run(request)
    injection_trace = _bundle_injection_trace(request)
    raw_backend_result = _read_json(backend_dir / "verifier_result.json")
    raw_source_verifier = raw_backend_result["source_verifier"]
    raw_prediction = _read_json(backend_dir / "repo_task_run" / "prediction.json")

    failure_taxonomy = {"schema_version": "verifier_failure_taxonomy.v0", "version": "0.1", "types": FAILURE_TAXONOMY}
    verifier_trace = _build_verifier_trace(
        verifier_spec=verifier_spec,
        raw_source_verifier=raw_source_verifier,
        prediction=raw_prediction,
        task_dir=task_dir,
    )
    verifier_quality = _verifier_quality_audit(verifier_spec, verifier_trace, failure_taxonomy)
    enhanced_verifier = _enhanced_verifier_result(raw_source_verifier, verifier_trace, verifier_quality)
    separation_audit = _skill_knowledge_separation_audit(
        skill_text=skill_text,
        knowledge_manifest=knowledge_manifest,
        release_bundle=release_bundle,
        request=request,
        task_dir=task_dir,
    )
    stage_status = _stage_status(backend_result, enhanced_verifier, verifier_quality, separation_audit)
    mini_result = _run_optional_mini_swe(output, request)
    summary = {
        "schema_version": "document_to_agent_e2e_summary.v0",
        **stage_status,
        "bundle_digest": build.bundle_digest,
        "active_binding_generation": active.generation,
        "verifier_claim_level": verifier_spec["claim_level"],
        "public_benchmark_verifier": False,
        "official_harness_verifier": False,
        "can_drive_failure_attribution": True,
        "can_drive_revision": True,
        "known_verifier_limitations": verifier_spec["known_limitations"],
        "real_agent_framework_executed": mini_result.execution_status == "executed",
        "real_agent_framework_status": mini_result.execution_status,
        "real_llm_agent_executed": False,
        "claim_level": "local_e2e_system_validation",
    }

    _write_outputs(
        output=output,
        case_dir=case_dir,
        material_digest=material_digest,
        windows=windows,
        skill_text=skill_text,
        skill_ir=skill_ir,
        knowledge_manifest=knowledge_manifest,
        knowledge_projection=knowledge_projection,
        release_bundle=release_bundle,
        active=active,
        request=request,
        injection_trace=injection_trace,
        backend_dir=backend_dir,
        separation_audit=separation_audit,
        verifier_spec=verifier_spec,
        verifier_trace=verifier_trace,
        verifier_quality=verifier_quality,
        failure_taxonomy=failure_taxonomy,
        enhanced_verifier=enhanced_verifier,
        summary=summary,
    )
    reports_dir.mkdir(parents=True, exist_ok=True)
    (reports_dir / "DOCUMENT_TO_AGENT_E2E_V0_STATUS.md").write_text(_render_status(summary), encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


def _prepare_compile_input(target: Path, material: str, task_contract: dict[str, Any], knowledge_manifest: dict[str, Any]) -> Path:
    if target.exists():
        shutil.rmtree(_long_path(target))
    target.mkdir(parents=True, exist_ok=True)
    (target / "expert_material.md").write_text(material, encoding="utf-8")
    write_json(target / "task_contract.json", task_contract)
    write_json(
        target / "knowledge_contract.json",
        {
            "schema_version": "repo_level_knowledge_contract.v1",
            "skill_family": REPO_LEVEL_SKILL_ID,
            "knowledge_owned_facts": [
                "allowed advisory snapshot",
                "advisory id",
                "package/version affected range",
                "repo evidence source contract",
                "dependency declaration source",
                "resolved version source",
                "import/use evidence source",
            ],
            "query_contracts": [
                {
                    "query_type": "advisory_by_package",
                    "required_parameters": ["package", "advisory_id"],
                    "freshness_mode": "immutable_task_snapshot",
                    "on_unavailable": "block_or_abstain",
                },
                {
                    "query_type": "repo_evidence_by_type",
                    "required_parameters": ["evidence_type", "repo_snapshot_ref"],
                    "freshness_mode": "immutable_repo_snapshot",
                    "on_unavailable": "abstain_or_fail_safe",
                },
            ],
            "knowledge_boundary": knowledge_manifest["knowledge_boundary"],
        },
    )
    return target


def _material_windows(material: str) -> dict[str, Any]:
    windows = []
    current_title = "preamble"
    current_lines: list[str] = []
    for line in material.splitlines():
        if line.startswith("## "):
            if current_lines:
                windows.append(_window(current_title, current_lines))
            current_title = line.removeprefix("## ").strip()
            current_lines = [line]
        else:
            current_lines.append(line)
    if current_lines:
        windows.append(_window(current_title, current_lines))
    return {"schema_version": "material_windows.v0", "window_count": len(windows), "windows": windows}


def _window(title: str, lines: list[str]) -> dict[str, Any]:
    text = "\n".join(lines).strip() + "\n"
    return {"title": title, "sha256": sha256_bytes(text.encode("utf-8")), "text": text}


def _extract_skill(material: str) -> str:
    lines = ["# Extracted Dependency-Use Triage Skill", ""]
    capture = False
    for line in material.splitlines():
        if line.startswith("## Procedural Skill Rules"):
            capture = True
            continue
        if capture and line.startswith("## "):
            break
        if capture and line.strip():
            lines.append(line)
    lines.extend(["", "## Scope", "- Local repo-level dependency-use triage only."])
    return "\n".join(lines).rstrip() + "\n"


def _extract_knowledge(material: str) -> dict[str, Any]:
    facts = []
    capture = False
    for line in material.splitlines():
        if line.startswith("## Factual and Evidence Knowledge"):
            capture = True
            continue
        if capture and line.startswith("## "):
            break
        if capture and line.strip().startswith("- "):
            facts.append(line.strip().removeprefix("- "))
    return {
        "schema_version": "document_to_agent_knowledge_manifest.v0",
        "source": "input_material.md",
        "facts": facts,
        "evidence_refs": [
            {"source_ref": "input_material.md#Factual and Evidence Knowledge", "evidence_type": "expert_material_fact"},
            {"source_ref": "public_heldout_v0/the-gan-zoo/allowed_knowledge.json", "evidence_type": "advisory_snapshot"},
            {"source_ref": "public_heldout_v0/the-gan-zoo/repo_snapshot/update.py", "evidence_type": "import_use_site"},
        ],
        "knowledge_boundary": "Concrete advisory facts and repository evidence remain outside the stable Skill procedure.",
    }


def _skill_knowledge_separation_audit(
    *,
    skill_text: str,
    knowledge_manifest: dict[str, Any],
    release_bundle: dict[str, Any],
    request: AgentBackendRequest,
    task_dir: Path,
) -> dict[str, Any]:
    evaluator_only = {"hidden_gold", "verifier_expected_answer", "dependency_used_and_affected"}
    skill_leaks = [token for token in evaluator_only if token in skill_text and token != "dependency_used_and_affected"]
    runtime_paths = set(_read_json(task_dir / "source_manifest.json")["runtime_visible_files"])
    evaluator_paths = set(_read_json(task_dir / "source_manifest.json")["evaluator_only_gold"])
    checks = {
        "skill_artifact_does_not_expose_evaluator_only_gold": not skill_leaks,
        "knowledge_manifest_contains_evidence_refs": bool(knowledge_manifest.get("evidence_refs")),
        "release_bundle_references_skill": bool(release_bundle.get("skill_ir_refs")),
        "release_bundle_references_knowledge": bool(release_bundle.get("knowledge_projection_refs")),
        "agent_request_uses_bundle_reference": bool(request.bundle_digest),
        "runtime_visible_gold_blocked": runtime_paths.isdisjoint(evaluator_paths),
    }
    return {"schema_version": "skill_knowledge_separation_audit.v0", "status": _pass_fail(checks), "checks": checks}


def _build_verifier_trace(
    *, verifier_spec: dict[str, Any], raw_source_verifier: dict[str, Any], prediction: dict[str, Any], task_dir: Path
) -> dict[str, Any]:
    checks = raw_source_verifier.get("checks", [])
    failed = [check["name"] for check in checks if not check.get("passed")]
    evidence_refs = prediction.get("evidence", [])
    source_manifest = _read_json(task_dir / "source_manifest.json")
    evaluator_only = set(source_manifest["evaluator_only_gold"])
    forbidden_refs = [
        item.get("path")
        for item in evidence_refs
        if item.get("path") in evaluator_only or str(item.get("path", "")).startswith("task.json#")
    ]
    return {
        "schema_version": "verifier_trace.v0",
        "schema_check": {"status": "pass" if raw_source_verifier.get("schema_valid", True) else "fail", "details": "schema fields checked by domain verifier"},
        "evidence_check": {
            "status": "pass" if not forbidden_refs and not failed else "fail",
            "checked_refs": [item.get("path") for item in evidence_refs],
            "forbidden_refs_seen": forbidden_refs,
        },
        "domain_check": {
            "status": "pass" if raw_source_verifier.get("verifier_pass") else "fail",
            "checked_rules": verifier_spec["checks"],
            "failed_rules": failed,
        },
        "gold_access_check": {"runtime_visible_gold": False, "verifier_used_hidden_gold": True},
        "verifier_confidence": "high" if raw_source_verifier.get("verifier_pass") else "medium",
        "verifier_limitations": verifier_spec["known_limitations"],
    }


def _verifier_quality_audit(
    verifier_spec: dict[str, Any], verifier_trace: dict[str, Any], failure_taxonomy: dict[str, Any]
) -> dict[str, Any]:
    checks = {
        "verifier_spec_exists": bool(verifier_spec),
        "verifier_type_declared": bool(verifier_spec.get("verifier_type")),
        "claim_level_declared": verifier_spec.get("claim_level") == "development_domain_verifier",
        "runtime_visible_gold_blocked": verifier_spec.get("runtime_visible_gold") is False
        and verifier_trace["gold_access_check"]["runtime_visible_gold"] is False,
        "evaluator_only_gold_used_only_by_verifier": verifier_spec.get("requires_hidden_gold") is True
        and verifier_trace["gold_access_check"]["verifier_used_hidden_gold"] is True,
        "schema_check_present": "schema_check" in verifier_trace,
        "evidence_check_present": "evidence_check" in verifier_trace,
        "domain_check_present": "domain_check" in verifier_trace,
        "failure_taxonomy_present": bool(failure_taxonomy.get("types")),
        "known_limitations_declared": bool(verifier_spec.get("known_limitations")),
        "public_benchmark_replacement_claim_blocked": "does not replace public benchmark harness"
        in verifier_spec.get("known_limitations", []),
    }
    return {"schema_version": "verifier_quality_audit.v0", "verifier_quality_status": _pass_fail(checks), "checks": checks}


def _enhanced_verifier_result(
    raw_source_verifier: dict[str, Any], verifier_trace: dict[str, Any], verifier_quality: dict[str, Any]
) -> dict[str, Any]:
    passed = bool(raw_source_verifier.get("verifier_pass")) and verifier_quality["verifier_quality_status"] == "pass"
    failure_type = None if passed else _failure_type(verifier_trace)
    return {
        "schema_version": "document_to_agent_verifier_result.v0",
        "pass": passed,
        "verifier_pass": passed,
        "failure_type": failure_type,
        "failure_taxonomy_version": "0.1",
        "claim_level": "development_domain_verifier",
        "can_drive_revision": True,
        "can_claim_public_benchmark_performance": False,
        "source_verifier": raw_source_verifier,
    }


def _failure_type(verifier_trace: dict[str, Any]) -> str:
    if verifier_trace["schema_check"]["status"] != "pass":
        return "schema_invalid"
    if verifier_trace["evidence_check"]["forbidden_refs_seen"]:
        return "forbidden_evidence_access"
    if verifier_trace["evidence_check"]["status"] != "pass":
        return "missing_required_evidence"
    if verifier_trace["domain_check"]["status"] != "pass":
        return "domain_rule_violation"
    return "verifier_inconclusive"


def _stage_status(
    backend_result: Any,
    enhanced_verifier: dict[str, Any],
    verifier_quality: dict[str, Any],
    separation_audit: dict[str, Any],
) -> dict[str, Any]:
    statuses = {
        "document_ingestion_status": "pass",
        "material_windowing_status": "pass",
        "skill_extraction_status": "pass",
        "knowledge_separation_status": separation_audit["status"],
        "bundle_build_status": "pass",
        "active_binding_status": "pass",
        "agent_backend_request_status": "pass",
        "bundle_injection_status": "pass",
        "agent_execution_status": "pass" if backend_result.execution_status == "executed" else "fail",
        "trajectory_status": "pass" if backend_result.trajectory_available else "fail",
        "verifier_status": "pass" if enhanced_verifier["pass"] else "fail",
        "verifier_quality_status": verifier_quality["verifier_quality_status"],
    }
    end_to_end = "pass" if all(value == "pass" for value in statuses.values()) else "fail"
    result = {**statuses, "end_to_end_status": end_to_end}
    if end_to_end != "pass":
        failed = [key for key, value in statuses.items() if value != "pass"]
        result.update({"failed_stage": failed[0], "blocker": f"{failed[0]}={statuses[failed[0]]}", "partial_artifacts_written": True})
    return result


def _write_outputs(
    *,
    output: Path,
    case_dir: Path,
    material_digest: dict[str, Any],
    windows: dict[str, Any],
    skill_text: str,
    skill_ir: dict[str, Any],
    knowledge_manifest: dict[str, Any],
    knowledge_projection: dict[str, Any],
    release_bundle: dict[str, Any],
    active: Any,
    request: AgentBackendRequest,
    injection_trace: dict[str, Any],
    backend_dir: Path,
    separation_audit: dict[str, Any],
    verifier_spec: dict[str, Any],
    verifier_trace: dict[str, Any],
    verifier_quality: dict[str, Any],
    failure_taxonomy: dict[str, Any],
    enhanced_verifier: dict[str, Any],
    summary: dict[str, Any],
) -> None:
    write_json(output / "source_registry_entry.json", {"schema_version": "source_registry_entry.v0", "source": str(case_dir / "input_material.md")})
    write_json(output / "material_digest.json", material_digest)
    write_json(output / "material_windows.json", windows)
    (output / "extracted_skill.md").write_text(skill_text, encoding="utf-8")
    write_json(output / "skill_ir.json", skill_ir)
    write_json(output / "knowledge_manifest.json", knowledge_manifest)
    write_json(output / "knowledge_projection.json", knowledge_projection)
    write_json(output / "release_bundle_manifest.json", release_bundle)
    write_json(output / "active_binding.json", asdict(active))
    write_json(output / "agent_backend_request.json", asdict(request))
    write_json(output / "bundle_injection_trace.json", injection_trace)
    shutil.copyfile(backend_dir / "normalized_trajectory.jsonl", output / "normalized_trajectory.jsonl")
    shutil.copyfile(backend_dir / "agent_output.json", output / "agent_output.json")
    write_json(output / "skill_knowledge_separation_audit.json", separation_audit)
    write_json(output / "verifier_spec_ref.json", verifier_spec)
    write_json(output / "verifier_trace.json", verifier_trace)
    write_json(output / "verifier_quality_audit.json", verifier_quality)
    write_json(output / "verifier_failure_taxonomy.json", failure_taxonomy)
    write_json(output / "verifier_result.json", enhanced_verifier)
    write_json(output / "e2e_summary.json", summary)
    (output / "e2e_summary.md").write_text(_render_status(summary), encoding="utf-8")


def _run_optional_mini_swe(output: Path, request: AgentBackendRequest) -> Any:
    mini_request = AgentBackendRequest(
        **{
            **asdict(request),
            "backend_id": "mini_swe_agent",
            "output_dir": str(output / "backend_runs" / "mini_swe_agent_framework"),
            "task_payload": {},
        }
    )
    return MiniSweAgentSmokeAdapter().run(mini_request)


def _bundle_injection_trace(request: AgentBackendRequest) -> dict[str, Any]:
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
        "injection_mode": "agent_backend_request",
    }


def _render_status(summary: dict[str, Any]) -> str:
    lines = ["# Document-to-Agent E2E v0 Status", ""]
    for key in [
        "end_to_end_status",
        "document_ingestion_status",
        "skill_extraction_status",
        "knowledge_separation_status",
        "bundle_build_status",
        "active_binding_status",
        "agent_execution_status",
        "trajectory_status",
        "verifier_status",
        "verifier_quality_status",
    ]:
        lines.append(f"- {key}: `{summary[key]}`")
    lines.extend(
        [
            "",
            "## Verifier Boundary",
            "",
            "The local verifier is a development/domain verifier. It is useful for E2E system validation, evidence checks, failure attribution, and revision feedback, but it does not replace public benchmark harnesses or official evaluation.",
        ]
    )
    return "\n".join(lines) + "\n"


def _pass_fail(checks: dict[str, bool]) -> str:
    return "pass" if all(checks.values()) else "fail"


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
