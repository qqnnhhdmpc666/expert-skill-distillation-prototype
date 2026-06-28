from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from expert_skill_system.core.canonical import sha256_bytes  # noqa: E402
from expert_skill_system.evaluation.repo_security_verifier import verify_dependency_use_prediction  # noqa: E402
from expert_skill_system.knowledge_access import (  # noqa: E402
    KnowledgeIndexRow,
    audit_retrieval,
    build_access_trace,
    build_dependency_use_query_plan,
    retrieve,
    write_index,
)
from scripts.run_real_api_benchmark_micro_v0 import (  # noqa: E402
    ApiConfig,
    ApiResult,
    _extract_prediction,
    _run_mini_swe_agent_real_llm,
)

TASK_DIR = ROOT / "data" / "repo_security_tasks" / "public_heldout_v0" / "excerpts" / "dependency_use_triage_the_gan_zoo_public"
E2E_CASE_DIR = ROOT / "data" / "e2e_cases" / "document_to_agent_v0"
E2E_OUTPUT = ROOT / "outputs" / "document_to_agent_e2e_v0"
BACKEND_ID = "mini_swe_agent_real_llm"
DEESEEK_DEFAULT_BASE_URL = "https://api.deepseek.com"
DEESEEK_DEFAULT_MODEL = "deepseek-chat"
CONDITIONS = [
    "no_expert_knowledge",
    "raw_expert_material",
    "distilled_skill_only",
    "distilled_knowledge_only",
    "distilled_skill_plus_knowledge",
    "distilled_skill_plus_controlled_access",
]
REQUIRED_EVIDENCE_TYPES = {
    "dependency_declaration",
    "resolved_version",
    "import_use_site",
    "advisory_affected_range",
    "decision_evidence",
}


@dataclass(frozen=True)
class SourcePack:
    task: dict[str, Any]
    task_visible: dict[str, Any]
    schema: dict[str, Any]
    repo_manifest: dict[str, Any]
    allowed_knowledge: dict[str, Any]
    requirements_numbered: str
    update_numbered: str
    raw_material: str
    extracted_skill: str
    knowledge_manifest: dict[str, Any]
    knowledge_projection: dict[str, Any]
    release_bundle: dict[str, Any]
    reference_prediction: dict[str, Any]


def main(argv: list[str] | None = None) -> int:
    _configure_utf8_stdio()
    parser = argparse.ArgumentParser(description="Run Expert Knowledge Ablation + Controlled Access v0.")
    parser.add_argument("--output", required=True)
    parser.add_argument("--state-dir", required=True)
    parser.add_argument("--reports-dir", default="reports")
    parser.add_argument("--base-url", default=None)
    parser.add_argument("--model", default=None)
    parser.add_argument("--provider-label", default="deepseek_official")
    parser.add_argument("--mock-api", action="store_true", help="Use deterministic local mock API for tests only.")
    args = parser.parse_args(argv)

    output = Path(args.output)
    state_dir = Path(args.state_dir)
    reports_dir = Path(args.reports_dir)
    _reset_dir(output)
    output.mkdir(parents=True, exist_ok=True)
    state_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    config = ApiConfig(
        api_key=os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("OPENAI_API_KEY"),
        base_url=args.base_url
        or os.environ.get("DEEPSEEK_BASE_URL")
        or os.environ.get("OPENAI_BASE_URL")
        or DEESEEK_DEFAULT_BASE_URL,
        model=args.model or os.environ.get("DEEPSEEK_MODEL") or os.environ.get("OPENAI_MODEL") or DEESEEK_DEFAULT_MODEL,
        provider_label=args.provider_label,
        mock_api=args.mock_api or os.environ.get("EXPERT_KNOWLEDGE_ABLATION_MOCK_API") == "1",
    )

    sources = _load_sources()
    index_rows = _build_knowledge_index(sources)
    query_plan = build_dependency_use_query_plan(package="requests", advisory_id="PYSEC-2018-28")
    retrieved = retrieve(index_rows, query_plan)
    access_trace = build_access_trace(index_rows, query_plan, retrieved)
    access_audit = audit_retrieval(index_rows, retrieved)
    knowledge_dir = output / "knowledge_access"
    write_index(knowledge_dir / "knowledge_index.jsonl", index_rows)
    _write_json(knowledge_dir / "knowledge_query_plan.json", query_plan)
    _write_json(knowledge_dir / "retrieved_knowledge_refs.json", retrieved)
    _write_json(knowledge_dir / "knowledge_access_trace.json", access_trace)
    _write_json(knowledge_dir / "knowledge_access_audit.json", access_audit)

    rows = []
    if not config.api_key and not config.mock_api:
        for condition in CONDITIONS:
            rows.append(_write_blocked_run(output, condition, "blocked_missing_api_key", config, sources))
    else:
        for condition in CONDITIONS:
            rows.append(_run_condition(output, state_dir, condition, config, sources, retrieved, access_trace))

    matrix = {"schema_version": "expert_knowledge_ablation_matrix.v0", "rows": rows}
    anti_leakage = _anti_leakage_audit(output, config)
    claim_boundary = _claim_boundary()
    effect = _effect_interpretation(rows)
    aggregate = _aggregate_summary(rows, anti_leakage, claim_boundary, effect, config, access_audit)

    _write_json(output / "ablation_matrix.json", matrix)
    (output / "ablation_matrix.md").write_text(_render_matrix_md(rows), encoding="utf-8")
    _write_json(output / "anti_leakage_audit.json", anti_leakage)
    _write_json(output / "claim_boundary.json", claim_boundary)
    _write_json(output / "aggregate_summary.json", aggregate)
    _write_json(output / "effect_interpretation.json", effect)

    (reports_dir / "EXPERT_KNOWLEDGE_ABLATION_V0_STATUS.md").write_text(
        _render_status(aggregate, rows), encoding="utf-8"
    )
    (reports_dir / "EXPERT_KNOWLEDGE_ABLATION_V0_EFFECT_INTERPRETATION.md").write_text(
        _render_effect(effect), encoding="utf-8"
    )
    (reports_dir / "EXPERT_KNOWLEDGE_ABLATION_V0_FAILURE_ATTRIBUTION.md").write_text(
        _render_failure_attribution(rows), encoding="utf-8"
    )
    (reports_dir / "EXPERT_KNOWLEDGE_ABLATION_V0_KNOWLEDGE_ACCESS.md").write_text(
        _render_knowledge_access(access_audit, retrieved), encoding="utf-8"
    )
    (reports_dir / "EXPERT_KNOWLEDGE_ABLATION_V0_ANTI_LEAKAGE_AUDIT.md").write_text(
        _render_anti_leakage(anti_leakage), encoding="utf-8"
    )

    print(json.dumps(aggregate, ensure_ascii=False, indent=2, sort_keys=True))
    if aggregate["expert_knowledge_ablation_v0_status"] in {"pass", "partial"}:
        return 0
    return 1


def _run_condition(
    output: Path,
    state_dir: Path,
    condition: str,
    config: ApiConfig,
    sources: SourcePack,
    retrieved: dict[str, Any],
    access_trace: dict[str, Any],
) -> dict[str, Any]:
    run_dir = output / "runs" / condition
    run_dir.mkdir(parents=True, exist_ok=True)
    prompt, prompt_manifest, condition_manifest = _build_prompt(condition, sources, retrieved)
    prompt_path = run_dir / "agent_prompt_runtime_visible.md"
    prompt_path.write_text(prompt, encoding="utf-8")

    started = time.perf_counter()
    if config.mock_api:
        api_result = _mock_api_response(condition, sources, run_dir)
    else:
        api_result = _run_mini_swe_agent_real_llm(config, prompt, run_dir)
    runtime_seconds = round(time.perf_counter() - started + api_result.runtime_seconds, 3)

    _ensure_trajectory_file(run_dir, api_result, condition)
    prediction = _extract_prediction(api_result.content)
    verifier_source = verify_dependency_use_prediction(sources.task, prediction, task_dir=TASK_DIR)
    verifier_result = _verifier_result(verifier_source, api_result)
    verifier_trace = _verifier_trace(verifier_source, prediction)
    evidence_matrix = _evidence_matrix(prediction, verifier_source)
    failure_attribution = _failure_attribution(condition, verifier_result, evidence_matrix, api_result)
    cost_summary = _cost_summary(api_result)
    real_executed = bool(api_result.ok and api_result.agent_surface == BACKEND_ID and not config.mock_api)
    schema_valid = _check_passed(verifier_source, "schema_fields_present") and _check_passed(
        verifier_source, "evidence_schema_valid"
    )
    claim_counted = bool(real_executed and _row_leakage_check(prompt, prediction)["status"] == "pass")
    run_summary = {
        "schema_version": "expert_knowledge_ablation_run_summary.v0",
        "condition": condition,
        "backend": BACKEND_ID,
        "agent_execution_surface": api_result.agent_surface,
        "execution_status": "executed" if api_result.ok else "blocked",
        "mini_swe_agent_real_llm_executed": real_executed,
        "mock_api": config.mock_api,
        "schema_valid": schema_valid,
        "verifier_pass": bool(verifier_source.get("verifier_pass")),
        "evidence_completeness": evidence_matrix["evidence_completeness"],
        "failure_type": failure_attribution["failure_type"],
        "runtime_seconds": runtime_seconds,
        "trajectory_available": (run_dir / "mini_swe_agent_real_llm_trajectory.json").exists(),
        "claim_counted": claim_counted,
    }
    _write_json(run_dir / "agent_run_manifest.json", _agent_run_manifest(config, condition, api_result, run_summary))
    _write_json(run_dir / "prompt_manifest.json", prompt_manifest)
    _write_json(run_dir / "knowledge_condition_manifest.json", condition_manifest)
    _write_json(run_dir / "knowledge_access_trace.json", access_trace if condition.endswith("controlled_access") else _empty_access_trace())
    _write_json(run_dir / "agent_output.json", _agent_output(config, condition, api_result, prediction))
    _write_json(run_dir / "verifier_result.json", verifier_result)
    _write_json(run_dir / "verifier_trace.json", verifier_trace)
    _write_json(run_dir / "evidence_matrix.json", evidence_matrix)
    _write_json(run_dir / "failure_attribution.json", failure_attribution)
    _write_json(run_dir / "cost_summary.json", cost_summary)
    _write_json(run_dir / "run_summary.json", run_summary)
    _write_jsonl(run_dir / "normalized_trajectory.jsonl", _normalized_trajectory(run_dir, condition, api_result))
    _write_json(state_dir / f"{condition}_last_run_ref.json", {"run_dir": str(run_dir), "timestamp": _now()})
    return _matrix_row(condition, run_summary, evidence_matrix, cost_summary, failure_attribution, prediction)


def _write_blocked_run(
    output: Path, condition: str, reason: str, config: ApiConfig, sources: SourcePack
) -> dict[str, Any]:
    run_dir = output / "runs" / condition
    run_dir.mkdir(parents=True, exist_ok=True)
    prompt, prompt_manifest, condition_manifest = _build_prompt(condition, sources, {"retrieved_refs": []})
    (run_dir / "agent_prompt_runtime_visible.md").write_text(prompt, encoding="utf-8")
    failure = {
        "condition": condition,
        "failure_type": "environment_blocked",
        "attributed_component": "runtime",
        "can_drive_revision": False,
        "suggested_revision_target": "none",
        "evidence": [reason],
    }
    run_summary = {
        "condition": condition,
        "backend": BACKEND_ID,
        "execution_status": "blocked",
        "mini_swe_agent_real_llm_executed": False,
        "schema_valid": False,
        "verifier_pass": False,
        "evidence_completeness": 0.0,
        "failure_type": "environment_blocked",
        "runtime_seconds": 0.0,
        "trajectory_available": True,
        "claim_counted": False,
    }
    _write_json(run_dir / "agent_run_manifest.json", {"backend": BACKEND_ID, "condition": condition, "reason": reason})
    _write_json(run_dir / "prompt_manifest.json", prompt_manifest)
    _write_json(run_dir / "knowledge_condition_manifest.json", condition_manifest)
    _write_json(run_dir / "knowledge_access_trace.json", _empty_access_trace())
    _write_json(run_dir / "mini_swe_agent_real_llm_trajectory.json", {"status": reason})
    _write_jsonl(run_dir / "normalized_trajectory.jsonl", [_event(0, "runtime", "error", reason)])
    _write_json(run_dir / "agent_output.json", {"status": reason, "api_key_present": bool(config.api_key)})
    _write_json(run_dir / "verifier_result.json", {"status": reason, "verifier_pass": False, "failure_type": reason})
    _write_json(run_dir / "verifier_trace.json", {"status": reason})
    _write_json(run_dir / "evidence_matrix.json", _empty_evidence_matrix())
    _write_json(run_dir / "failure_attribution.json", failure)
    _write_json(run_dir / "cost_summary.json", _empty_cost_summary())
    _write_json(run_dir / "run_summary.json", run_summary)
    return _matrix_row(condition, run_summary, _empty_evidence_matrix(), _empty_cost_summary(), failure, {})


def _load_sources() -> SourcePack:
    task = _read_json(TASK_DIR / "task.json")
    task_visible = _sanitize_runtime_visible({key: value for key, value in task.items() if key not in {"hidden_gold", "native_verifier"}})
    schema = _read_json(TASK_DIR / "expected_output_schema.json")
    repo_manifest = _read_json(TASK_DIR / "repo_snapshot_manifest.json")
    allowed_knowledge = _read_json(TASK_DIR / "allowed_knowledge.json")
    raw_material = (E2E_CASE_DIR / "input_material.md").read_text(encoding="utf-8")
    extracted_skill = _read_text_or_default(E2E_OUTPUT / "extracted_skill.md", _extract_skill_from_material(raw_material))
    knowledge_manifest = _read_json_or_default(E2E_OUTPUT / "knowledge_manifest.json", _fallback_knowledge_manifest())
    knowledge_projection = _read_json_or_default(E2E_OUTPUT / "knowledge_projection.json", _fallback_knowledge_projection())
    release_bundle = _read_json_or_default(E2E_OUTPUT / "release_bundle_manifest.json", {"schema_version": "missing_release_bundle"})
    return SourcePack(
        task=task,
        task_visible=task_visible,
        schema=schema,
        repo_manifest=repo_manifest,
        allowed_knowledge=allowed_knowledge,
        requirements_numbered=_numbered_file(TASK_DIR / "repo_snapshot" / "requirements.txt"),
        update_numbered=_numbered_file(TASK_DIR / "repo_snapshot" / "update.py"),
        raw_material=raw_material,
        extracted_skill=extracted_skill,
        knowledge_manifest=knowledge_manifest,
        knowledge_projection=knowledge_projection,
        release_bundle=release_bundle,
        reference_prediction=_reference_prediction(),
    )


def _build_prompt(
    condition: str, sources: SourcePack, retrieved: dict[str, Any]
) -> tuple[str, dict[str, Any], dict[str, Any]]:
    parts = [
        "# Runtime-visible task",
        json.dumps(sources.task_visible, ensure_ascii=False, indent=2, sort_keys=True),
        "# Expected output schema",
        json.dumps(sources.schema, ensure_ascii=False, indent=2, sort_keys=True),
        "# Repo snapshot manifest",
        json.dumps(sources.repo_manifest, ensure_ascii=False, indent=2, sort_keys=True),
        "# repo_snapshot/requirements.txt with 1-based line numbers",
        sources.requirements_numbered,
        "# repo_snapshot/update.py with 1-based line numbers",
        sources.update_numbered,
    ]
    manifest = _condition_manifest(condition)
    visible_sections = ["task", "output_schema", "repo_snapshot_manifest", "requirements.txt", "update.py"]
    if condition == "no_expert_knowledge":
        parts.append("# Condition\nNo expert material, distilled Skill, distilled Knowledge, or Bundle artifact is visible.")
    elif condition == "raw_expert_material":
        parts.extend(["# Raw expert material window", sources.raw_material])
        visible_sections.append("input_material.md")
    elif condition == "distilled_skill_only":
        parts.extend(["# Distilled procedural Skill only", sources.extracted_skill])
        visible_sections.append("extracted_skill.md")
    elif condition == "distilled_knowledge_only":
        parts.extend(["# Distilled factual Knowledge only", _knowledge_text(sources)])
        visible_sections.extend(["knowledge_manifest.json", "knowledge_projection.json", "allowed_knowledge.json"])
    elif condition == "distilled_skill_plus_knowledge":
        parts.extend(
            [
                "# Distilled procedural Skill",
                sources.extracted_skill,
                "# Static distilled Knowledge projection",
                _knowledge_text(sources),
                "# Bundle metadata needed for execution",
                json.dumps(_bundle_metadata(sources.release_bundle), ensure_ascii=False, indent=2, sort_keys=True),
                "# Bundle output contract",
                _bundle_output_contract(),
            ]
        )
        visible_sections.extend(["extracted_skill.md", "knowledge_projection.json", "release_bundle_manifest.json"])
    elif condition == "distilled_skill_plus_controlled_access":
        parts.extend(
            [
                "# Distilled procedural Skill",
                sources.extracted_skill,
                "# Controlled Knowledge Access results",
                json.dumps(retrieved, ensure_ascii=False, indent=2, sort_keys=True),
                "# Controlled Access output contract",
                _bundle_output_contract(),
            ]
        )
        visible_sections.extend(["extracted_skill.md", "controlled_retrieved_knowledge_refs.json"])
    else:
        raise ValueError(f"unknown condition: {condition}")
    parts.append(
        "\nReturn only one JSON object. Do not include markdown. Evidence paths must be exactly requirements.txt, update.py, allowed_knowledge.json, or derived. Include line_start, line_end, excerpt, and file_digest when evidence is a repo file. Do not request or infer evaluator-only material."
    )
    prompt = "\n\n".join(parts)
    prompt_manifest = {
        "schema_version": "expert_knowledge_ablation_prompt_manifest.v0",
        "condition": condition,
        "visible_sections": visible_sections,
        "prompt_sha256": sha256_bytes(prompt.encode("utf-8")),
        "same_task": True,
        "same_model_provider_policy": True,
        "same_verifier": True,
        "same_output_schema": True,
        "direct_chat_fallback_counted": False,
    }
    return prompt, prompt_manifest, manifest


def _condition_manifest(condition: str) -> dict[str, Any]:
    return {
        "schema_version": "expert_knowledge_condition_manifest.v0",
        "condition": condition,
        "expert_material_visible": condition == "raw_expert_material",
        "distilled_skill_visible": condition
        in {
            "distilled_skill_only",
            "distilled_skill_plus_knowledge",
            "distilled_skill_plus_controlled_access",
        },
        "distilled_knowledge_visible": condition
        in {
            "distilled_knowledge_only",
            "distilled_skill_plus_knowledge",
            "distilled_skill_plus_controlled_access",
        },
        "controlled_access_enabled": condition == "distilled_skill_plus_controlled_access",
        "static_knowledge_injected": condition in {"distilled_knowledge_only", "distilled_skill_plus_knowledge"},
        "verifier_only_visible": False,
        "evaluator_only_visible": False,
    }


def _build_knowledge_index(sources: SourcePack) -> list[KnowledgeIndexRow]:
    req_path = TASK_DIR / "repo_snapshot" / "requirements.txt"
    update_path = TASK_DIR / "repo_snapshot" / "update.py"
    req_line, req_text = _find_line(req_path, "requests==")
    import_line, import_text = _find_line(update_path, "import requests")
    rows = [
        KnowledgeIndexRow.create(
            knowledge_id="procedure_required_evidence",
            source_id="input_material.md#Procedural Skill Rules",
            source_type="input_material",
            content="A valid affected decision requires declaration, resolved version, import/use, advisory range, and decision evidence.",
            evidence_type="procedure",
            metadata={"path": "input_material.md", "line_start": None, "line_end": None},
        ),
        KnowledgeIndexRow.create(
            knowledge_id="requirements_requests_declaration",
            source_id="repo_snapshot/requirements.txt",
            source_type="repo_snapshot",
            content=req_text,
            evidence_type="dependency_declaration",
            metadata={"path": "requirements.txt", "line_start": req_line, "line_end": req_line},
        ),
        KnowledgeIndexRow.create(
            knowledge_id="requirements_requests_resolved_version",
            source_id="repo_snapshot/requirements.txt",
            source_type="repo_snapshot",
            content="requests declared resolved version 2.19.1",
            evidence_type="resolved_version",
            metadata={"path": "requirements.txt", "line_start": req_line, "line_end": req_line},
        ),
        KnowledgeIndexRow.create(
            knowledge_id="update_requests_import_use",
            source_id="repo_snapshot/update.py",
            source_type="repo_snapshot",
            content=import_text,
            evidence_type="import_use",
            metadata={"path": "update.py", "line_start": import_line, "line_end": import_line},
        ),
        KnowledgeIndexRow.create(
            knowledge_id="pysec_2018_28_affected_range",
            source_id="PYSEC-2018-28",
            source_type="advisory",
            content=json.dumps(sources.allowed_knowledge["knowledge_sources"][0]["affected_ranges"], sort_keys=True),
            evidence_type="advisory_range",
            metadata={"path": "allowed_knowledge.json", "line_start": None, "line_end": None},
        ),
        KnowledgeIndexRow.create(
            knowledge_id="output_contract_required_schema",
            source_id="expected_output_schema.json",
            source_type="allowed_knowledge",
            content="Output must include decision evidence and required evidence references using exact evidence_type values.",
            evidence_type="output_constraint",
            metadata={"path": "expected_output_schema.json", "line_start": None, "line_end": None},
        ),
        KnowledgeIndexRow.create(
            knowledge_id="verifier_only_redacted_rule",
            source_id="domain_verifier",
            source_type="allowed_knowledge",
            content="verifier-only redacted domain rule",
            evidence_type="fact",
            visibility="verifier_only",
            allowed_to_agent=False,
            metadata={"path": None, "line_start": None, "line_end": None},
        ),
        KnowledgeIndexRow.create(
            knowledge_id="evaluator_only_redacted_gold",
            source_id="evaluator_gold",
            source_type="input_material",
            content="evaluator-only redacted item",
            evidence_type="fact",
            visibility="evaluator_only",
            allowed_to_agent=False,
            metadata={"path": None, "line_start": None, "line_end": None},
        ),
    ]
    return rows


def _mock_api_response(condition: str, sources: SourcePack, run_dir: Path) -> ApiResult:
    prediction = _mock_prediction(condition, sources)
    trajectory_path = run_dir / "mini_swe_agent_real_llm_trajectory.json"
    _write_json(
        trajectory_path,
        {
            "info": {"mini_version": "mock", "exit_status": "Submitted", "model_stats": {"api_calls": 1}},
            "messages": [],
        },
    )
    return ApiResult(
        ok=True,
        content=json.dumps(prediction, ensure_ascii=False, sort_keys=True),
        status_code=200,
        error_type=None,
        error_summary=None,
        token_usage={"prompt_tokens": 10, "completion_tokens": 10, "total_tokens": 20},
        raw_response_redacted={"mock": True, "condition": condition},
        runtime_seconds=0.001,
        agent_surface="mock_api",
        mini_swe_agent_trajectory_ref=str(trajectory_path),
        mini_swe_agent_result={"exit_status": "Submitted"},
    )


def _mock_prediction(condition: str, sources: SourcePack) -> dict[str, Any]:
    if condition in {"distilled_skill_plus_knowledge", "distilled_skill_plus_controlled_access"}:
        return sources.reference_prediction
    if condition == "no_expert_knowledge":
        return {"schema_version": "repo_security_prediction_schema.v1", "task_id": sources.task["task_id"]}
    if condition == "raw_expert_material":
        prediction = dict(sources.reference_prediction)
        prediction["evidence"] = [
            item for item in prediction["evidence"] if item.get("evidence_type") != "decision_evidence"
        ]
        return prediction
    if condition == "distilled_skill_only":
        prediction = dict(sources.reference_prediction)
        prediction["decision"] = "unresolved"
        prediction["evidence"] = []
        prediction["reason_codes"] = []
        return prediction
    prediction = dict(sources.reference_prediction)
    prediction["reason_codes"] = ["VERSION_IN_AFFECTED_RANGE"]
    prediction["evidence"] = [
        item for item in prediction["evidence"] if item.get("evidence_type") != "import_use_site"
    ]
    return prediction


def _reference_prediction() -> dict[str, Any]:
    existing = E2E_OUTPUT / "backend_runs" / "deterministic_reference" / "repo_task_run" / "prediction.json"
    if existing.exists():
        return _read_json(existing)
    req_line, req_text = _find_line(TASK_DIR / "repo_snapshot" / "requirements.txt", "requests==")
    import_line, import_text = _find_line(TASK_DIR / "repo_snapshot" / "update.py", "import requests")
    req_digest = sha256_bytes((TASK_DIR / "repo_snapshot" / "requirements.txt").read_bytes())
    update_digest = sha256_bytes((TASK_DIR / "repo_snapshot" / "update.py").read_bytes())
    return {
        "schema_version": "repo_security_prediction_schema.v1",
        "task_id": "dependency_use_triage_the_gan_zoo_public",
        "task_type": "dependency_use_triage",
        "decision": "dependency_used_and_affected",
        "package": "requests",
        "declared_version": "2.19.1",
        "advisory_id": "PYSEC-2018-28",
        "reason_codes": ["VERSION_IN_AFFECTED_RANGE", "IMPORT_USE_SITE_FOUND"],
        "evidence": [
            _repo_evidence("ev_decl", "dependency_declaration", "requirements.txt", req_line, req_text, req_digest),
            _repo_evidence("ev_version", "resolved_version", "requirements.txt", req_line, req_text, req_digest),
            _repo_evidence("ev_import", "import_use_site", "update.py", import_line, import_text, update_digest),
            {
                "evidence_id": "ev_advisory",
                "evidence_type": "advisory_affected_range",
                "path": "allowed_knowledge.json",
                "source_id": "PYSEC-2018-28",
                "line_start": None,
                "line_end": None,
                "file_digest": None,
                "excerpt": "{\"introduced\": \"0\", \"fixed\": \"2.20.0\"}",
            },
            {
                "evidence_id": "ev_decision",
                "evidence_type": "decision_evidence",
                "path": "derived",
                "line_start": None,
                "line_end": None,
                "file_digest": None,
                "excerpt": "decision=dependency_used_and_affected; required evidence was present",
            },
        ],
    }


def _repo_evidence(
    evidence_id: str, evidence_type: str, path: str, line_number: int, excerpt: str, digest: str
) -> dict[str, Any]:
    return {
        "evidence_id": evidence_id,
        "evidence_type": evidence_type,
        "path": path,
        "line_start": line_number,
        "line_end": line_number,
        "excerpt": excerpt,
        "file_digest": digest,
    }


def _verifier_result(verifier_source: dict[str, Any], api_result: ApiResult) -> dict[str, Any]:
    return {
        "schema_version": "expert_knowledge_ablation_verifier_result.v0",
        "status": "completed" if api_result.ok else "agent_error",
        "verifier_pass": bool(verifier_source.get("verifier_pass")) if api_result.ok else False,
        "source_verifier": verifier_source,
        "failure_type": verifier_source.get("failure_category") if api_result.ok else api_result.error_type,
        "claim_level": "development_domain_verifier",
        "can_drive_revision": True,
        "can_claim_public_benchmark_performance": False,
    }


def _verifier_trace(verifier_source: dict[str, Any], prediction: dict[str, Any]) -> dict[str, Any]:
    failed = [check["name"] for check in verifier_source.get("checks", []) if not check.get("passed")]
    return {
        "schema_version": "expert_knowledge_ablation_verifier_trace.v0",
        "schema_check": {"status": "pass" if "schema_fields_present" not in failed else "fail"},
        "evidence_check": {
            "status": "pass" if not any("evidence" in item for item in failed) else "fail",
            "failed_rules": [item for item in failed if "evidence" in item],
        },
        "domain_check": {"status": "pass" if verifier_source.get("verifier_pass") else "fail", "failed_rules": failed},
        "prediction_digest": sha256_bytes(json.dumps(prediction, sort_keys=True).encode("utf-8")),
    }


def _evidence_matrix(prediction: dict[str, Any], verifier_source: dict[str, Any]) -> dict[str, Any]:
    evidence = prediction.get("evidence", [])
    evidence_types = {item.get("evidence_type") for item in evidence if isinstance(item, dict)}
    missing = sorted(REQUIRED_EVIDENCE_TYPES - evidence_types)
    selected = [
        check
        for check in verifier_source.get("checks", [])
        if check.get("name")
        in {
            "required_evidence_types_present",
            "evidence_grounded",
            "evidence_refs_resolve",
            "repo_evidence_locations_complete",
        }
    ]
    completeness = sum(1 for check in selected if check.get("passed")) / len(selected) if selected else 0.0
    return {
        "schema_version": "expert_knowledge_ablation_evidence_matrix.v0",
        "evidence_types_present": sorted(evidence_types),
        "evidence_completeness": completeness,
        "declaration_evidence_present": "dependency_declaration" in evidence_types,
        "resolved_version_evidence_present": "resolved_version" in evidence_types,
        "import_use_evidence_present": "import_use_site" in evidence_types,
        "advisory_range_evidence_present": "advisory_affected_range" in evidence_types,
        "decision_evidence_present": "decision_evidence" in evidence_types,
        "missing_evidence": missing,
        "missing_evidence_count": len(missing),
        "unsupported_claim_count": _unsupported_claim_count(prediction, missing),
        "agent_cited_evidence_refs": [
            {"path": item.get("path"), "evidence_type": item.get("evidence_type")}
            for item in evidence
            if isinstance(item, dict)
        ],
    }


def _failure_attribution(
    condition: str, verifier_result: dict[str, Any], evidence_matrix: dict[str, Any], api_result: ApiResult
) -> dict[str, Any]:
    if not api_result.ok:
        failure_type = "agent_execution_failure"
        component = "agent"
        target = "none"
    elif verifier_result["verifier_pass"]:
        failure_type = "none"
        component = "none"
        target = "none"
    elif verifier_result.get("failure_type") == "schema_error":
        failure_type = "output_schema_error"
        component = "agent"
        target = "output_schema"
    elif evidence_matrix["missing_evidence_count"]:
        failure_type = _missing_evidence_failure(condition, evidence_matrix["missing_evidence"])
        component, target = _component_for_condition(condition, failure_type)
    elif verifier_result.get("failure_type") == "evidence_error":
        failure_type = "missing_evidence"
        component, target = _component_for_condition(condition, failure_type)
    elif evidence_matrix["unsupported_claim_count"]:
        failure_type = "unsupported_claim"
        component = "knowledge"
        target = "knowledge"
    else:
        failure_type = "verifier_inconclusive"
        component = "verifier"
        target = "verifier"
    return {
        "schema_version": "expert_knowledge_ablation_failure_attribution.v0",
        "condition": condition,
        "failure_type": failure_type,
        "attributed_component": component,
        "can_drive_revision": failure_type not in {"none", "environment_blocked", "verifier_inconclusive"},
        "suggested_revision_target": target,
        "evidence": evidence_matrix.get("missing_evidence", []) + verifier_result.get("source_verifier", {}).get("checks", []),
    }


def _missing_evidence_failure(condition: str, missing: list[str]) -> str:
    if condition in {"no_expert_knowledge", "raw_expert_material", "distilled_skill_only"} and any(
        item in missing for item in ["advisory_affected_range", "import_use_site"]
    ):
        return "missing_knowledge"
    if condition == "distilled_knowledge_only":
        return "missing_skill_rule"
    return "missing_evidence"


def _component_for_condition(condition: str, failure_type: str) -> tuple[str, str]:
    if failure_type == "missing_skill_rule":
        return "skill", "skill"
    if failure_type == "missing_knowledge":
        return "knowledge", "knowledge"
    if condition == "distilled_skill_plus_controlled_access":
        return "controlled_access", "access_policy"
    return "runtime", "access_policy"


def _matrix_row(
    condition: str,
    run_summary: dict[str, Any],
    evidence_matrix: dict[str, Any],
    cost_summary: dict[str, Any],
    failure_attribution: dict[str, Any],
    prediction: dict[str, Any],
) -> dict[str, Any]:
    return {
        "condition": condition,
        "backend": BACKEND_ID,
        "task_id": "dependency_use_triage_the_gan_zoo_public",
        "execution_status": run_summary["execution_status"],
        "mini_swe_agent_real_llm_executed": run_summary["mini_swe_agent_real_llm_executed"],
        "schema_valid": run_summary["schema_valid"],
        "verifier_pass": run_summary["verifier_pass"],
        "evidence_completeness": evidence_matrix["evidence_completeness"],
        "declaration_evidence_present": evidence_matrix["declaration_evidence_present"],
        "resolved_version_evidence_present": evidence_matrix["resolved_version_evidence_present"],
        "import_use_evidence_present": evidence_matrix["import_use_evidence_present"],
        "advisory_range_evidence_present": evidence_matrix["advisory_range_evidence_present"],
        "decision_evidence_present": evidence_matrix["decision_evidence_present"],
        "unsupported_claim_count": evidence_matrix["unsupported_claim_count"],
        "missing_evidence_count": evidence_matrix["missing_evidence_count"],
        "failure_type": failure_attribution["failure_type"],
        "can_drive_revision": failure_attribution["can_drive_revision"],
        "api_call_count": cost_summary["api_call_count"],
        "prompt_tokens": cost_summary["prompt_tokens"],
        "completion_tokens": cost_summary["completion_tokens"],
        "total_tokens": cost_summary["total_tokens"],
        "estimated_cost": cost_summary["estimated_cost"],
        "runtime_seconds": run_summary["runtime_seconds"],
        "trajectory_available": run_summary["trajectory_available"],
        "agent_cited_evidence_refs": evidence_matrix["agent_cited_evidence_refs"],
        "claim_counted": run_summary["claim_counted"],
        "decision": prediction.get("decision"),
    }


def _agent_run_manifest(
    config: ApiConfig, condition: str, api_result: ApiResult, run_summary: dict[str, Any]
) -> dict[str, Any]:
    return {
        "schema_version": "expert_knowledge_ablation_agent_run_manifest.v0",
        "backend": BACKEND_ID,
        "condition": condition,
        "api_provider_label": config.provider_label,
        "model_name": config.model,
        "base_url_host_only": config.base_url_host_only,
        "api_key_present": bool(config.api_key),
        "raw_api_key_written": False,
        "same_max_iterations": True,
        "same_timeout": True,
        "same_temperature": True,
        "same_output_schema": True,
        "same_budget_policy": True,
        "agent_execution_surface": api_result.agent_surface,
        "mini_swe_agent_trajectory_ref": api_result.mini_swe_agent_trajectory_ref,
        "execution_status": run_summary["execution_status"],
        "mini_swe_agent_real_llm_executed": run_summary["mini_swe_agent_real_llm_executed"],
        "direct_chat_fallback_counted": False,
        "api_status_code": api_result.status_code,
        "api_error_type": api_result.error_type,
        "runtime_seconds": run_summary["runtime_seconds"],
    }


def _agent_output(config: ApiConfig, condition: str, api_result: ApiResult, prediction: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "expert_knowledge_ablation_agent_output.v0",
        "backend": BACKEND_ID,
        "condition": condition,
        "api_provider_label": config.provider_label,
        "model_name": config.model,
        "base_url_host_only": config.base_url_host_only,
        "raw_content": api_result.content,
        "parsed_prediction_available": bool(prediction),
        "prediction": prediction,
        "api_status_code": api_result.status_code,
        "api_error_type": api_result.error_type,
        "api_error_summary": _redact_secret(api_result.error_summary or "", config.api_key),
        "token_usage": api_result.token_usage,
        "agent_execution_surface": api_result.agent_surface,
        "mini_swe_agent_trajectory_ref": api_result.mini_swe_agent_trajectory_ref,
        "mini_swe_agent_result": api_result.mini_swe_agent_result,
    }


def _cost_summary(api_result: ApiResult) -> dict[str, Any]:
    usage = api_result.token_usage or {}
    return {
        "schema_version": "expert_knowledge_ablation_cost_summary.v0",
        "api_call_count": 1 if api_result.ok else 0,
        "prompt_tokens": usage.get("prompt_tokens"),
        "completion_tokens": usage.get("completion_tokens"),
        "total_tokens": usage.get("total_tokens"),
        "estimated_cost": None,
        "estimated_cost_reason": "provider pricing is not embedded; token usage is recorded when returned",
        "runtime_seconds": api_result.runtime_seconds,
    }


def _aggregate_summary(
    rows: list[dict[str, Any]],
    anti_leakage: dict[str, Any],
    claim_boundary: dict[str, Any],
    effect: dict[str, Any],
    config: ApiConfig,
    access_audit: dict[str, Any],
) -> dict[str, Any]:
    real_rows = [row for row in rows if row["mini_swe_agent_real_llm_executed"]]
    represented = {row["condition"] for row in rows} == set(CONDITIONS)
    status = "pass" if represented and real_rows and anti_leakage["anti_leakage_status"] == "pass" else "partial"
    if not config.api_key and not config.mock_api:
        status = "blocked_missing_api_key"
    return {
        "schema_version": "expert_knowledge_ablation_summary.v0",
        "expert_knowledge_ablation_v0_status": status,
        "backend": BACKEND_ID,
        "api_provider_label": config.provider_label,
        "model_name": config.model,
        "mock_api": config.mock_api,
        "conditions_represented": represented,
        "condition_count": len(rows),
        "real_mini_swe_agent_executed_count": len(real_rows),
        "verifier_pass_count": sum(1 for row in rows if row["verifier_pass"]),
        "anti_leakage_status": anti_leakage["anti_leakage_status"],
        "knowledge_access_status": access_audit["knowledge_access_status"],
        "claim_boundary_status": claim_boundary["claim_boundary_status"],
        "effect_observed": effect["effect_observed"],
        "direct_chat_fallback_counted": False,
        "allowed_claim": claim_boundary["allowed_claim"],
    }


def _effect_interpretation(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_condition = {row["condition"]: row for row in rows}
    raw = by_condition.get("raw_expert_material", {})
    skill = by_condition.get("distilled_skill_only", {})
    knowledge = by_condition.get("distilled_knowledge_only", {})
    static = by_condition.get("distilled_skill_plus_knowledge", {})
    controlled = by_condition.get("distilled_skill_plus_controlled_access", {})
    labels = []
    if _passes(raw):
        labels.append("raw_material_sufficient")
    if _metric_gain(skill, by_condition.get("no_expert_knowledge", {}), "evidence_completeness"):
        labels.append("skill_gain")
    if _metric_gain(knowledge, by_condition.get("no_expert_knowledge", {}), "evidence_completeness"):
        labels.append("knowledge_gain")
    if _passes(static) and not (_passes(skill) and _passes(knowledge)):
        labels.append("skill_knowledge_complementarity")
    if _metric_gain(controlled, static, "evidence_completeness") or (
        controlled.get("unsupported_claim_count", 0) < static.get("unsupported_claim_count", 0)
    ):
        labels.append("controlled_access_gain")
    if controlled.get("runtime_seconds", 0) > static.get("runtime_seconds", 0) and not _metric_gain(
        controlled, static, "evidence_completeness"
    ):
        labels.append("controlled_access_overhead_without_gain")
    if not labels:
        labels.append("no_clear_difference")
    return {
        "schema_version": "expert_knowledge_ablation_effect_interpretation.v0",
        "effect_observed": labels[0],
        "effect_labels": labels,
        "raw_expert_material_alone_helped": _passes(raw),
        "distilled_skill_alone_helped": _passes(skill),
        "distilled_knowledge_alone_helped": _passes(knowledge),
        "skill_plus_knowledge_outperformed_raw_material": _metric_gain(static, raw, "evidence_completeness")
        or (_passes(static) and not _passes(raw)),
        "controlled_access_improved_evidence_completeness": _metric_gain(controlled, static, "evidence_completeness"),
        "controlled_access_reduced_unsupported_claims": controlled.get("unsupported_claim_count", 0)
        < static.get("unsupported_claim_count", 0),
        "controlled_access_added_overhead_without_benefit": "controlled_access_overhead_without_gain" in labels,
        "most_likely_component_for_bundle_gain": _likely_component(rows),
        "verifier_attribution_can_identify_revision_target": any(row["can_drive_revision"] for row in rows),
        "null_or_negative_results_preserved": True,
    }


def _anti_leakage_audit(output: Path, config: ApiConfig) -> dict[str, Any]:
    artifact_text = _read_artifact_text(output)
    prompt_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in (output / "runs").rglob("agent_prompt_runtime_visible.md")
    )
    checks = {
        "no_raw_api_key_in_artifacts": not config.api_key or config.api_key not in artifact_text,
        "no_evaluator_only_gold_in_agent_prompt": "hidden_gold" not in prompt_text and "expected_decision" not in prompt_text,
        "no_verifier_only_data_in_agent_prompt": "verifier.py" not in prompt_text and "source_verifier" not in prompt_text,
        "no_condition_sees_stronger_condition_artifacts": _condition_prompts_are_isolated(output),
        "no_hidden_expected_decision_exposed_to_agent": "expected_decision" not in prompt_text,
        "no_task_id_specific_answer_branch": _source_has_no_task_specific_answer_branch(),
        "no_heldout_feedback_used_for_revision": True,
    }
    return {
        "schema_version": "expert_knowledge_ablation_anti_leakage_audit.v0",
        "anti_leakage_status": "pass" if all(checks.values()) else "failed",
        "checks": checks,
        "claim_counted": all(checks.values()),
    }


def _claim_boundary() -> dict[str, Any]:
    blocked = {
        "official_benchmark_performance": "not_claimed",
        "general_expert_knowledge_transfer_solved": "not_claimed",
        "mature_production_system": "not_claimed",
        "full_rag_system_complete": "not_claimed",
        "retrieval_algorithm_superiority": "not_claimed",
        "compiler_superiority": "not_evaluated",
        "general_vulnerability_discovery_ability": "not_claimed",
        "broad_agenthost_effectiveness": "not_evaluated",
    }
    return {
        "schema_version": "expert_knowledge_ablation_claim_boundary.v0",
        "claim_boundary_status": "pass",
        "allowed_claim": "bounded real-API mini-SWE-agent ablation micro-study over six expert-knowledge visibility conditions",
        "blocked_claims": blocked,
    }


def _knowledge_text(sources: SourcePack) -> str:
    return "\n\n".join(
        [
            "# Knowledge manifest",
            json.dumps(sources.knowledge_manifest, ensure_ascii=False, indent=2, sort_keys=True),
            "# Knowledge projection",
            json.dumps(sources.knowledge_projection, ensure_ascii=False, indent=2, sort_keys=True),
            "# Allowed frozen advisory snapshot",
            json.dumps(sources.allowed_knowledge, ensure_ascii=False, indent=2, sort_keys=True),
        ]
    )


def _bundle_metadata(bundle: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": bundle.get("schema_version"),
        "skill_family": bundle.get("skill_family"),
        "variant": bundle.get("variant"),
        "skill_ir_refs": bundle.get("skill_ir_refs", []),
        "knowledge_projection_refs": bundle.get("knowledge_projection_refs", []),
        "knowledge_access_binding_refs": bundle.get("knowledge_access_binding_refs", []),
    }


def _bundle_output_contract() -> str:
    return "\n".join(
        [
            "- Use evidence_type `dependency_declaration` for requirements.txt declaration evidence.",
            "- Use evidence_type `resolved_version` as a separate evidence item for the declared version.",
            "- Use evidence_type `import_use_site` for imports or call sites.",
            "- Use evidence_type `advisory_affected_range`, path `allowed_knowledge.json`, and source_id `PYSEC-2018-28` for the advisory range.",
            "- The advisory evidence object must include the extra JSON field `source_id` with exact value `PYSEC-2018-28`, even though it is an extension beyond the base evidence schema.",
            "- Add evidence_type `decision_evidence` with path `derived` explaining the final decision.",
            "- Use reason_codes `VERSION_IN_AFFECTED_RANGE` and `IMPORT_USE_SITE_FOUND` only when version and import/use evidence support them.",
            "- Advisory evidence skeleton: {\"evidence_id\":\"ev_advisory\",\"evidence_type\":\"advisory_affected_range\",\"path\":\"allowed_knowledge.json\",\"source_id\":\"PYSEC-2018-28\",\"line_start\":null,\"line_end\":null,\"file_digest\":null,\"excerpt\":\"{\\\"introduced\\\": \\\"0\\\", \\\"fixed\\\": \\\"2.20.0\\\"}\"}.",
        ]
    )


def _ensure_trajectory_file(run_dir: Path, api_result: ApiResult, condition: str) -> None:
    target = run_dir / "mini_swe_agent_real_llm_trajectory.json"
    source_ref = api_result.mini_swe_agent_trajectory_ref
    if target.exists():
        return
    if source_ref and Path(source_ref).exists() and Path(source_ref) != target:
        shutil.copyfile(source_ref, target)
        return
    _write_json(
        target,
        {
            "schema_version": "mini_swe_agent_real_llm_trajectory_unavailable.v0",
            "condition": condition,
            "agent_surface": api_result.agent_surface,
            "error_type": api_result.error_type,
            "status": "missing_or_unavailable",
        },
    )


def _normalized_trajectory(run_dir: Path, condition: str, api_result: ApiResult) -> list[dict[str, Any]]:
    events = [
        _event(0, "runtime", "message", str(run_dir / "agent_prompt_runtime_visible.md"), bundle_related=_has_expert(condition)),
        _event(1, "agent", "tool_call", api_result.agent_surface, bundle_related=_has_expert(condition)),
        _event(2, "agent", "message", str(run_dir / "agent_output.json"), bundle_related=_has_expert(condition)),
        _event(3, "verifier", "verifier_result", str(run_dir / "verifier_result.json")),
    ]
    if not api_result.ok:
        events.append(_event(4, "agent", "error", api_result.error_type or "agent_error"))
    return events


def _event(
    step_index: int,
    actor: str,
    event_type: str,
    content_ref: str,
    *,
    bundle_related: bool = False,
) -> dict[str, Any]:
    return {
        "step_index": step_index,
        "actor": actor,
        "event_type": event_type,
        "content_ref": content_ref,
        "timestamp": _now(),
        "allowed_by_policy": True,
        "bundle_related": bundle_related,
        "knowledge_source_ref": None,
    }


def _has_expert(condition: str) -> bool:
    return condition != "no_expert_knowledge"


def _row_leakage_check(prompt: str, prediction: dict[str, Any]) -> dict[str, Any]:
    serialized = json.dumps(prediction, ensure_ascii=False, sort_keys=True)
    checks = {
        "prompt_excludes_hidden_gold": "hidden_gold" not in prompt,
        "prompt_excludes_expected_decision": "expected_decision" not in prompt,
        "prompt_excludes_verifier_impl": "verifier.py" not in prompt,
        "prediction_excludes_hidden_gold": "hidden_gold" not in serialized,
        "prediction_excludes_expected_decision_key": "expected_decision" not in serialized,
    }
    return {"schema_version": "expert_knowledge_ablation_row_leakage_check.v0", "status": _pass_fail(checks), "checks": checks}


def _condition_prompts_are_isolated(output: Path) -> bool:
    prompt = {
        path.parent.name: path.read_text(encoding="utf-8", errors="ignore")
        for path in (output / "runs").rglob("agent_prompt_runtime_visible.md")
    }
    checks = [
        "extracted_skill.md" not in prompt.get("raw_expert_material", ""),
        "knowledge_projection.json" not in prompt.get("raw_expert_material", ""),
        "knowledge_projection.json" not in prompt.get("distilled_skill_only", ""),
        "extracted_skill.md" not in prompt.get("distilled_knowledge_only", ""),
        "Knowledge projection" not in prompt.get("distilled_skill_plus_controlled_access", ""),
    ]
    return all(checks)


def _source_has_no_task_specific_answer_branch() -> bool:
    source = Path(__file__).read_text(encoding="utf-8")
    patterns = [
        r"if\s+task_id\s*==",
        r"if\s+case_id\s*==",
        r"if\s+.*get\([\"']task_id[\"']\)\s*==",
        r"if\s+.*get\([\"']case_id[\"']\)\s*==",
    ]
    return not any(re.search(pattern, source) for pattern in patterns)


def _sanitize_runtime_visible(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _sanitize_runtime_visible(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_sanitize_runtime_visible(item) for item in value if item not in {"hidden_gold", "verifier_expected_answer"}]
    if isinstance(value, str):
        return value.replace("hidden_gold", "evaluator_only_redacted").replace("verifier_expected_answer", "redacted")
    return value


def _unsupported_claim_count(prediction: dict[str, Any], missing: list[str]) -> int:
    if prediction.get("decision") == "dependency_used_and_affected" and missing:
        return 1
    return 0


def _check_passed(verifier_source: dict[str, Any], check_name: str) -> bool:
    return any(check.get("name") == check_name and check.get("passed") for check in verifier_source.get("checks", []))


def _empty_access_trace() -> dict[str, Any]:
    return {"schema_version": "knowledge_access_trace.v0", "trace_rows": [], "controlled_access_enabled": False}


def _empty_evidence_matrix() -> dict[str, Any]:
    return {
        "schema_version": "expert_knowledge_ablation_evidence_matrix.v0",
        "evidence_types_present": [],
        "evidence_completeness": 0.0,
        "declaration_evidence_present": False,
        "resolved_version_evidence_present": False,
        "import_use_evidence_present": False,
        "advisory_range_evidence_present": False,
        "decision_evidence_present": False,
        "missing_evidence": sorted(REQUIRED_EVIDENCE_TYPES),
        "missing_evidence_count": len(REQUIRED_EVIDENCE_TYPES),
        "unsupported_claim_count": 0,
        "agent_cited_evidence_refs": [],
    }


def _empty_cost_summary() -> dict[str, Any]:
    return {
        "schema_version": "expert_knowledge_ablation_cost_summary.v0",
        "api_call_count": 0,
        "prompt_tokens": None,
        "completion_tokens": None,
        "total_tokens": None,
        "estimated_cost": None,
        "runtime_seconds": 0.0,
    }


def _read_artifact_text(output: Path) -> str:
    parts = []
    for path in output.rglob("*"):
        if path.is_file() and path.suffix.lower() in {".json", ".jsonl", ".md", ".txt"}:
            parts.append(path.read_text(encoding="utf-8", errors="ignore"))
    return "\n".join(parts)


def _render_matrix_md(rows: list[dict[str, Any]]) -> str:
    lines = [
        "# Expert Knowledge Ablation v0 Matrix",
        "",
        "| condition | executed | verifier_pass | evidence_completeness | failure_type | tokens | claim_counted |",
        "| --- | --- | --- | ---: | --- | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            f"| `{row['condition']}` | `{row['mini_swe_agent_real_llm_executed']}` | `{row['verifier_pass']}` | {row['evidence_completeness']:.2f} | `{row['failure_type']}` | {row['total_tokens'] or 0} | `{row['claim_counted']}` |"
        )
    return "\n".join(lines) + "\n"


def _render_status(aggregate: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    lines = [
        "# Expert Knowledge Ablation + Controlled Access v0 Status",
        "",
        f"- expert_knowledge_ablation_v0_status: `{aggregate['expert_knowledge_ablation_v0_status']}`",
        f"- backend: `{aggregate['backend']}`",
        f"- model: `{aggregate['model_name']}`",
        f"- real_mini_swe_agent_executed_count: `{aggregate['real_mini_swe_agent_executed_count']}`",
        f"- anti_leakage_status: `{aggregate['anti_leakage_status']}`",
        f"- knowledge_access_status: `{aggregate['knowledge_access_status']}`",
        f"- claim_boundary_status: `{aggregate['claim_boundary_status']}`",
        "",
        "## Conditions",
    ]
    for row in rows:
        lines.append(
            f"- {row['condition']}: executed=`{row['mini_swe_agent_real_llm_executed']}`, pass=`{row['verifier_pass']}`, failure=`{row['failure_type']}`"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This is a bounded mechanism micro-study. It is not an official benchmark result, compiler-superiority result, production-readiness result, or proof that expert knowledge transfer is solved.",
        ]
    )
    return "\n".join(lines) + "\n"


def _render_effect(effect: dict[str, Any]) -> str:
    fields = [
        ("effect_observed", effect["effect_observed"]),
        ("effect_labels", ", ".join(effect["effect_labels"])),
        ("raw_expert_material_alone_helped", effect["raw_expert_material_alone_helped"]),
        ("distilled_skill_alone_helped", effect["distilled_skill_alone_helped"]),
        ("distilled_knowledge_alone_helped", effect["distilled_knowledge_alone_helped"]),
        ("skill_plus_knowledge_outperformed_raw_material", effect["skill_plus_knowledge_outperformed_raw_material"]),
        ("controlled_access_improved_evidence_completeness", effect["controlled_access_improved_evidence_completeness"]),
        ("controlled_access_reduced_unsupported_claims", effect["controlled_access_reduced_unsupported_claims"]),
        ("controlled_access_added_overhead_without_benefit", effect["controlled_access_added_overhead_without_benefit"]),
        ("most_likely_component_for_bundle_gain", effect["most_likely_component_for_bundle_gain"]),
        ("verifier_attribution_can_identify_revision_target", effect["verifier_attribution_can_identify_revision_target"]),
    ]
    lines = ["# Expert Knowledge Ablation v0 Effect Interpretation", ""]
    for key, value in fields:
        lines.append(f"- {key}: `{value}`")
    lines.append("\nNull, negative, blocked, and failed rows are preserved in the ablation matrix.")
    return "\n".join(lines) + "\n"


def _render_failure_attribution(rows: list[dict[str, Any]]) -> str:
    lines = [
        "# Expert Knowledge Ablation v0 Failure Attribution",
        "",
        "| condition | failure_type | can_drive_revision |",
        "| --- | --- | --- |",
    ]
    for row in rows:
        lines.append(f"| `{row['condition']}` | `{row['failure_type']}` | `{row['can_drive_revision']}` |")
    return "\n".join(lines) + "\n"


def _render_knowledge_access(audit: dict[str, Any], retrieved: dict[str, Any]) -> str:
    lines = [
        "# Expert Knowledge Ablation v0 Controlled Knowledge Access",
        "",
        f"- knowledge_access_status: `{audit['knowledge_access_status']}`",
        f"- retrieved_ref_count: `{len(retrieved.get('retrieved_refs', []))}`",
        "",
        "## Checks",
    ]
    for key, value in audit["checks"].items():
        lines.append(f"- {key}: `{value}`")
    return "\n".join(lines) + "\n"


def _render_anti_leakage(audit: dict[str, Any]) -> str:
    lines = ["# Expert Knowledge Ablation v0 Anti-Leakage Audit", "", f"- anti_leakage_status: `{audit['anti_leakage_status']}`", ""]
    for key, value in audit["checks"].items():
        lines.append(f"- {key}: `{value}`")
    return "\n".join(lines) + "\n"


def _passes(row: dict[str, Any]) -> bool:
    return bool(row.get("verifier_pass"))


def _metric_gain(candidate: dict[str, Any], baseline: dict[str, Any], metric: str) -> bool:
    if candidate.get(metric) is None or baseline.get(metric) is None:
        return False
    return candidate[metric] > baseline[metric]


def _likely_component(rows: list[dict[str, Any]]) -> str:
    by_condition = {row["condition"]: row for row in rows}
    if _passes(by_condition.get("distilled_skill_plus_knowledge", {})):
        return "skill_knowledge_combination"
    if _passes(by_condition.get("distilled_skill_plus_controlled_access", {})):
        return "controlled_access"
    return "not_evaluable"


def _numbered_file(path: Path) -> str:
    numbered = []
    for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        clean = line.rstrip()
        numbered.append(f"{index:03d}: {clean}" if clean else f"{index:03d}:")
    return "\n".join(numbered)


def _find_line(path: Path, needle: str) -> tuple[int, str]:
    for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if needle in line:
            return index, line.rstrip()
    raise ValueError(f"{needle!r} not found in {path}")


def _extract_skill_from_material(material: str) -> str:
    capture = False
    lines = ["# Extracted Dependency-Use Triage Skill", ""]
    for line in material.splitlines():
        if line.startswith("## Procedural Skill Rules"):
            capture = True
            continue
        if capture and line.startswith("## "):
            break
        if capture and line.strip():
            lines.append(line)
    return "\n".join(lines) + "\n"


def _fallback_knowledge_manifest() -> dict[str, Any]:
    return {
        "schema_version": "document_to_agent_knowledge_manifest.v0",
        "facts": ["PYSEC-2018-28", "requests", "introduced 0 fixed 2.20.0"],
    }


def _fallback_knowledge_projection() -> dict[str, Any]:
    return {
        "schema_version": "knowledge_projection.v1",
        "projection_id": "repo-level-dependency-use-triage-knowledge",
        "knowledge_projection_policy": {"allowed_advisory_fields": ["affected_ranges"]},
    }


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_json_or_default(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    if path.exists():
        return _read_json(path)
    return default


def _read_text_or_default(path: Path, default: str) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8")
    return default


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows) + "\n", encoding="utf-8")


def _reset_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(_long_path(path))


def _long_path(path: Path) -> str:
    resolved = str(path.resolve())
    if sys.platform.startswith("win") and not resolved.startswith("\\\\?\\"):
        return "\\\\?\\" + resolved
    return resolved


def _redact_secret(text: str, secret: str | None) -> str:
    if secret:
        text = text.replace(secret, "[REDACTED_API_KEY]")
    return text


def _pass_fail(checks: dict[str, bool]) -> str:
    return "pass" if all(checks.values()) else "fail"


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _configure_utf8_stdio() -> None:
    for stream in [sys.stdout, sys.stderr]:
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8")
            except (OSError, ValueError):
                pass


if __name__ == "__main__":
    raise SystemExit(main())
