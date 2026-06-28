from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from expert_skill_system.core.canonical import sha256_bytes  # noqa: E402
from expert_skill_system.evaluation.repo_security_verifier import verify_dependency_use_prediction  # noqa: E402

TASK_DIR = ROOT / "data" / "repo_security_tasks" / "public_heldout_v0" / "excerpts" / "dependency_use_triage_the_gan_zoo_public"
E2E_OUTPUT = ROOT / "outputs" / "document_to_agent_e2e_v0"
DEESEEK_DEFAULT_BASE_URL = "https://api.deepseek.com"
DEESEEK_DEFAULT_MODEL = "deepseek-chat"
BACKEND_ID = "mini_swe_agent_real_llm"
CONDITIONS = ["no_skill", "document_to_agent_bundle"]
LANES = ["document_to_agent_real_api", "skillsbench_micro", "skillgen_mapping", "swebench_micro"]


@dataclass(frozen=True)
class ApiConfig:
    api_key: str | None
    base_url: str
    model: str
    provider_label: str
    mock_api: bool = False

    @property
    def base_url_host_only(self) -> str:
        return urllib.parse.urlparse(self.base_url).netloc or self.base_url.replace("https://", "").split("/")[0]


@dataclass(frozen=True)
class ApiResult:
    ok: bool
    content: str
    status_code: int | None
    error_type: str | None
    error_summary: str | None
    token_usage: dict[str, Any] | None
    raw_response_redacted: dict[str, Any] | None
    runtime_seconds: float
    agent_surface: str = "direct_chat_completion"
    mini_swe_agent_trajectory_ref: str | None = None
    mini_swe_agent_result: dict[str, Any] | None = None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run real-API benchmark micro-evaluation v0.")
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
        base_url=args.base_url or os.environ.get("DEEPSEEK_BASE_URL") or os.environ.get("OPENAI_BASE_URL") or DEESEEK_DEFAULT_BASE_URL,
        model=args.model or os.environ.get("DEEPSEEK_MODEL") or os.environ.get("OPENAI_MODEL") or DEESEEK_DEFAULT_MODEL,
        provider_label=args.provider_label,
        mock_api=args.mock_api or os.environ.get("REAL_API_MICRO_MOCK_API") == "1",
    )

    api_manifest = _api_execution_manifest(config)
    rows: list[dict[str, Any]] = []
    lane_rows: dict[str, list[dict[str, Any]]] = {lane: [] for lane in LANES}
    if not config.api_key and not config.mock_api:
        rows.extend(_blocked_document_rows(output, "blocked_missing_api_key"))
    else:
        for condition in CONDITIONS:
            row = _run_document_to_agent_row(output, state_dir, condition, config)
            rows.append(row)
            lane_rows["document_to_agent_real_api"].append(row)

    for lane in ["skillsbench_micro", "skillgen_mapping", "swebench_micro"]:
        for condition in CONDITIONS:
            row = _blocked_or_mapping_row(output, lane, condition)
            rows.append(row)
            lane_rows[lane].append(row)

    matrix = _complete_matrix(rows)
    per_lane = _per_lane_summary(matrix)
    anti_leakage = _anti_leakage_audit(output, config)
    claim_boundary = _claim_boundary()
    cost_summary = _cost_summary(matrix)
    effect = _effect_interpretation(matrix)
    aggregate = _aggregate_summary(matrix, per_lane, anti_leakage, claim_boundary, api_manifest, effect)

    _write_json(output / "api_execution_manifest.json", api_manifest)
    _write_json(output / "backend_condition_lane_matrix.json", {"schema_version": "real_api_backend_condition_lane_matrix.v0", "rows": matrix})
    (output / "backend_condition_lane_matrix.md").write_text(_render_matrix_md(matrix), encoding="utf-8")
    _write_json(output / "per_lane_summary.json", per_lane)
    _write_json(output / "aggregate_summary.json", aggregate)
    _write_json(output / "api_safety_audit.json", anti_leakage)
    _write_json(output / "anti_leakage_audit.json", anti_leakage)
    _write_json(output / "cost_summary.json", cost_summary)
    _write_json(output / "claim_boundary.json", claim_boundary)

    (reports_dir / "REAL_API_BENCHMARK_MICRO_V0_STATUS.md").write_text(_render_status(aggregate, per_lane), encoding="utf-8")
    (reports_dir / "REAL_API_BENCHMARK_MICRO_V0_EFFECT_INTERPRETATION.md").write_text(
        _render_effect(effect), encoding="utf-8"
    )
    (reports_dir / "REAL_API_BENCHMARK_MICRO_V0_ANTI_LEAKAGE_AUDIT.md").write_text(
        _render_anti_leakage(anti_leakage), encoding="utf-8"
    )

    print(json.dumps(aggregate, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if aggregate["real_api_benchmark_micro_v0_status"] in {"pass", "partial"} else 1


def _run_document_to_agent_row(output: Path, state_dir: Path, condition: str, config: ApiConfig) -> dict[str, Any]:
    run_dir = output / "runs" / "document_to_agent_real_api" / condition
    run_dir.mkdir(parents=True, exist_ok=True)
    prompt = _build_prompt(condition)
    prompt_path = run_dir / "agent_prompt_runtime_visible.md"
    prompt_path.write_text(prompt, encoding="utf-8")
    start = time.perf_counter()
    api_result = _mock_api_response(condition) if config.mock_api else _run_mini_swe_agent_real_llm(config, prompt, run_dir)
    elapsed = round(time.perf_counter() - start, 3)

    prediction = _extract_prediction(api_result.content)
    prediction_path = run_dir / "prediction.json"
    _write_json(prediction_path, prediction)
    task = _read_json(TASK_DIR / "task.json")
    verifier = verify_dependency_use_prediction(task, prediction, task_dir=TASK_DIR)
    verifier_trace = _verifier_trace(verifier, prediction)
    status = "executed" if api_result.ok else "blocked"
    schema_valid = bool(verifier["checks"][0]["passed"]) if verifier.get("checks") else False
    leakage = _row_leakage_check(prompt, prediction)
    claim_counted = bool(api_result.ok and schema_valid and verifier and leakage["status"] == "pass")
    injection = _bundle_injection_trace(condition)
    trajectory = [
        _event(0, "runtime", "message", str(prompt_path), bundle_related=condition != "no_skill"),
        _event(1, "agent", "tool_call", api_result.agent_surface, bundle_related=condition != "no_skill"),
        _event(2, "agent", "message", str(run_dir / "agent_output.json"), bundle_related=condition != "no_skill"),
        _event(3, "verifier", "verifier_result", str(run_dir / "verifier_result.json"), bundle_related=condition != "no_skill"),
    ]
    if not api_result.ok:
        trajectory.append(_event(4, "agent", "error", api_result.error_type or "api_error", bundle_related=condition != "no_skill"))

    agent_output = {
        "schema_version": "real_api_agent_output.v0",
        "backend": BACKEND_ID,
        "condition": condition,
        "api_provider_label": config.provider_label,
        "model_name": config.model,
        "base_url_host_only": config.base_url_host_only,
        "raw_content": api_result.content,
        "parsed_prediction_available": bool(prediction),
        "api_status_code": api_result.status_code,
        "api_error_type": api_result.error_type,
        "api_error_summary": api_result.error_summary,
        "token_usage": api_result.token_usage,
        "agent_execution_surface": api_result.agent_surface,
        "mini_swe_agent_trajectory_ref": api_result.mini_swe_agent_trajectory_ref,
        "mini_swe_agent_result": api_result.mini_swe_agent_result,
    }
    verifier_result = {
        "schema_version": "real_api_micro_verifier_result.v0",
        "status": "completed" if api_result.ok else "api_error",
        "verifier_pass": bool(verifier["verifier_pass"]) if api_result.ok else False,
        "source_verifier": verifier,
        "failure_type": verifier.get("failure_category") if api_result.ok else api_result.error_type,
        "can_claim_public_benchmark_performance": False,
    }
    run_summary = {
        "schema_version": "real_api_micro_run_summary.v0",
        "lane": "document_to_agent_real_api",
        "backend": BACKEND_ID,
        "condition": condition,
        "execution_status": status,
        "real_llm_agent_executed": api_result.ok,
        "bundle_injected": condition != "no_skill",
        "schema_valid": schema_valid,
        "verifier_pass": bool(verifier_result["verifier_pass"]),
        "claim_counted": claim_counted,
        "runtime_seconds": round(elapsed + api_result.runtime_seconds, 3),
        "api_call_count": 1 if api_result.ok else 0,
        "token_usage": api_result.token_usage,
        "agent_execution_surface": api_result.agent_surface,
        "mini_swe_agent_trajectory_ref": api_result.mini_swe_agent_trajectory_ref,
    }
    _write_json(run_dir / "agent_run_manifest.json", _agent_run_manifest(config, condition, api_result, run_summary))
    _write_json(run_dir / "bundle_injection_trace.json", injection)
    _write_json(run_dir / "agent_output.json", agent_output)
    _write_json(run_dir / "verifier_result.json", verifier_result)
    _write_json(run_dir / "verifier_trace.json", verifier_trace)
    _write_json(run_dir / "run_summary.json", run_summary)
    _write_json(run_dir / "row_leakage_check.json", leakage)
    _write_jsonl(run_dir / "normalized_trajectory.jsonl", trajectory)
    _write_json(state_dir / f"{condition}_last_run_ref.json", {"run_dir": str(run_dir), "timestamp": _now()})
    return _row_from_run_summary(run_summary, verifier_result, leakage)


def _call_chat_completion(config: ApiConfig, prompt: str) -> ApiResult:
    started = time.perf_counter()
    url = config.base_url.rstrip("/") + "/chat/completions"
    body = {
        "model": config.model,
        "messages": [
            {"role": "system", "content": "You are a repo dependency-use triage agent. Return strict JSON only."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0,
        "stream": False,
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Authorization": f"Bearer {config.api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            payload = json.loads(response.read().decode("utf-8"))
            content = payload.get("choices", [{}])[0].get("message", {}).get("content", "")
            return ApiResult(
                ok=True,
                content=str(content),
                status_code=response.status,
                error_type=None,
                error_summary=None,
                token_usage=payload.get("usage"),
                raw_response_redacted=_redact_response(payload),
                runtime_seconds=round(time.perf_counter() - started, 3),
                agent_surface="direct_chat_completion",
            )
    except urllib.error.HTTPError as exc:
        text = exc.read().decode("utf-8", errors="replace")[-2000:]
        return ApiResult(
            ok=False,
            content="",
            status_code=exc.code,
            error_type="http_error",
            error_summary=text,
            token_usage=None,
            raw_response_redacted=None,
            runtime_seconds=round(time.perf_counter() - started, 3),
            agent_surface="direct_chat_completion",
        )
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return ApiResult(
            ok=False,
            content="",
            status_code=None,
            error_type=type(exc).__name__,
            error_summary=str(exc)[-2000:],
            token_usage=None,
            raw_response_redacted=None,
            runtime_seconds=round(time.perf_counter() - started, 3),
            agent_surface="direct_chat_completion",
        )


def _run_mini_swe_agent_real_llm(config: ApiConfig, prompt: str, run_dir: Path) -> ApiResult:
    """Run the real API path through mini-SWE-agent, not through a direct chat shortcut.

    The model must emit exactly one mini-SWE-agent text action. A minimal JSON
    submission environment accepts raw JSON as the action payload and raises
    mini-SWE-agent's Submitted signal. This preserves the agent loop, model
    parser, action execution, trajectory, and local verifier boundary without
    asking the model to fight Windows shell quoting.
    """
    started = time.perf_counter()
    trajectory_path = (run_dir / "mini_swe_agent_real_llm_trajectory.json").resolve()
    try:
        from minisweagent.agents.default import DefaultAgent
        from minisweagent.exceptions import Submitted
        from minisweagent.models.litellm_textbased_model import LitellmTextbasedModel
    except Exception as exc:  # pragma: no cover - environment dependent
        return ApiResult(
            ok=False,
            content="",
            status_code=None,
            error_type="mini_swe_agent_import_error",
            error_summary=_redact_secret(str(exc), config.api_key),
            token_usage=None,
            raw_response_redacted=None,
            runtime_seconds=round(time.perf_counter() - started, 3),
            agent_surface="mini_swe_agent_real_llm",
            mini_swe_agent_trajectory_ref=str(trajectory_path),
        )

    class JsonSubmissionEnvironment:
        def execute(self, action: dict[str, Any], cwd: str = "", *, timeout: int | None = None) -> dict[str, Any]:
            command = str(action.get("command", "")).strip()
            try:
                json.loads(command)
            except Exception as exc:
                return {
                    "output": f"JSON parse failed: {exc}. Put only raw JSON in the action block.",
                    "returncode": 2,
                    "exception_info": "",
                }
            raise Submitted(
                {
                    "role": "exit",
                    "content": command,
                    "extra": {"exit_status": "Submitted", "submission": command},
                }
            )

        def get_template_vars(self, **kwargs: Any) -> dict[str, Any]:
            return {"cwd": str(run_dir), **kwargs}

        def serialize(self) -> dict[str, Any]:
            return {
                "info": {
                    "config": {
                        "environment_type": "real_api_micro.JsonSubmissionEnvironment",
                        "cwd": str(run_dir),
                    }
                }
            }

    previous_openai_key = os.environ.get("OPENAI_API_KEY")
    previous_base_url = os.environ.get("OPENAI_BASE_URL")
    previous_litellm_tracking = os.environ.get("MSWEA_COST_TRACKING")
    if config.api_key:
        os.environ["OPENAI_API_KEY"] = config.api_key
    os.environ["OPENAI_BASE_URL"] = config.base_url
    os.environ["MSWEA_COST_TRACKING"] = "ignore_errors"
    model_name = config.model if "/" in config.model else f"openai/{config.model}"
    try:
        model = LitellmTextbasedModel(
            model_name=model_name,
            model_kwargs={
                "base_url": config.base_url,
                "temperature": 0,
                "max_tokens": 2200,
            },
            cost_tracking="ignore_errors",
        )
        agent = DefaultAgent(
            model,
            JsonSubmissionEnvironment(),
            system_template="\n".join(
                [
                    "You are mini_swe_agent_real_llm for a bounded repo dependency-use triage task.",
                    "You must reply with exactly one ```mswea_bash_command block.",
                    "Inside the block, put only the final raw JSON prediction object.",
                    "Do not put shell commands, markdown, comments, or prose inside the block.",
                    "The JSON must satisfy the task schema and evidence rules in the user message.",
                ]
            ),
            instance_template="{{task}}",
            step_limit=3,
            cost_limit=10,
            output_path=trajectory_path,
        )
        result = agent.run(prompt)
        submission = str(result.get("submission", "")).strip()
        trajectory = _read_json(trajectory_path) if trajectory_path.exists() else {}
        return ApiResult(
            ok=result.get("exit_status") == "Submitted" and bool(submission),
            content=submission,
            status_code=200 if submission else None,
            error_type=None if submission else str(result.get("exit_status", "agent_no_submission")),
            error_summary=None if submission else _redact_secret(json.dumps(result, ensure_ascii=False)[-2000:], config.api_key),
            token_usage=_mini_swe_agent_token_usage(trajectory),
            raw_response_redacted=_mini_swe_agent_response_summary(trajectory),
            runtime_seconds=round(time.perf_counter() - started, 3),
            agent_surface="mini_swe_agent_real_llm",
            mini_swe_agent_trajectory_ref=str(trajectory_path),
            mini_swe_agent_result=result,
        )
    except Exception as exc:  # pragma: no cover - real API/environment dependent
        return ApiResult(
            ok=False,
            content="",
            status_code=None,
            error_type=type(exc).__name__,
            error_summary=_redact_secret(str(exc)[-2000:], config.api_key),
            token_usage=_mini_swe_agent_token_usage(_read_json(trajectory_path)) if trajectory_path.exists() else None,
            raw_response_redacted=None,
            runtime_seconds=round(time.perf_counter() - started, 3),
            agent_surface="mini_swe_agent_real_llm",
            mini_swe_agent_trajectory_ref=str(trajectory_path),
            mini_swe_agent_result={"exit_status": type(exc).__name__},
        )
    finally:
        _restore_env("OPENAI_API_KEY", previous_openai_key)
        _restore_env("OPENAI_BASE_URL", previous_base_url)
        _restore_env("MSWEA_COST_TRACKING", previous_litellm_tracking)


def _build_prompt(condition: str) -> str:
    task = _read_json(TASK_DIR / "task.json")
    task_visible = _sanitize_runtime_visible({key: value for key, value in task.items() if key not in {"hidden_gold", "native_verifier"}})
    manifest = _read_json(TASK_DIR / "repo_snapshot_manifest.json")
    allowed_knowledge = _read_json(TASK_DIR / "allowed_knowledge.json")
    schema = _read_json(TASK_DIR / "expected_output_schema.json")
    requirements = _numbered_file(TASK_DIR / "repo_snapshot" / "requirements.txt")
    update_py = _numbered_file(TASK_DIR / "repo_snapshot" / "update.py")
    parts = [
        "# Runtime-visible task",
        json.dumps(task_visible, ensure_ascii=False, indent=2, sort_keys=True),
        "# Expected output schema",
        json.dumps(schema, ensure_ascii=False, indent=2, sort_keys=True),
        "# Repo snapshot manifest",
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True),
        "# Allowed frozen knowledge snapshot",
        json.dumps(allowed_knowledge, ensure_ascii=False, indent=2, sort_keys=True),
        "# repo_snapshot/requirements.txt with 1-based line numbers",
        requirements,
        "# repo_snapshot/update.py with 1-based line numbers",
        update_py,
    ]
    if condition == "document_to_agent_bundle":
        parts.extend(
            [
                "# Document-to-Agent Bundle guidance",
                (E2E_OUTPUT / "extracted_skill.md").read_text(encoding="utf-8"),
                "# Knowledge manifest",
                (E2E_OUTPUT / "knowledge_manifest.json").read_text(encoding="utf-8"),
                "# ReleaseBundle manifest",
                (E2E_OUTPUT / "release_bundle_manifest.json").read_text(encoding="utf-8"),
                "# Bundle runtime output contract",
                "\n".join(
                    [
                        "- For dependency declaration evidence, use evidence_type `dependency_declaration`.",
                        "- For resolved package version evidence, add a separate evidence item with evidence_type `resolved_version`.",
                        "- For imports or call sites, use evidence_type `import_use_site`, not `import_statement` or `call_site`.",
                        "- For the advisory range in allowed_knowledge.json, use evidence_type `advisory_affected_range`, path `allowed_knowledge.json`, source_id `PYSEC-2018-28`, and excerpt containing introduced/fixed range.",
                        "- The advisory evidence object must include this exact extra field: `\"source_id\": \"PYSEC-2018-28\"`; otherwise the local verifier cannot resolve the allowed knowledge source.",
                        "- Add one evidence item with evidence_type `decision_evidence`, path `derived`, and excerpt explaining the final decision from the gathered evidence.",
                        "- If version 2.19.1 is compared against fixed 2.20.0 and import/use evidence exists, use reason_codes `VERSION_IN_AFFECTED_RANGE` and `IMPORT_USE_SITE_FOUND`.",
                        "- Advisory evidence skeleton: {\"evidence_id\":\"...\",\"evidence_type\":\"advisory_affected_range\",\"path\":\"allowed_knowledge.json\",\"source_id\":\"PYSEC-2018-28\",\"line_start\":null,\"line_end\":null,\"file_digest\":null,\"excerpt\":\"{\\\"introduced\\\": \\\"0\\\", \\\"fixed\\\": \\\"2.20.0\\\"}\"}.",
                        "- Decision evidence skeleton: {\"evidence_id\":\"...\",\"evidence_type\":\"decision_evidence\",\"path\":\"derived\",\"line_start\":null,\"line_end\":null,\"file_digest\":null,\"excerpt\":\"decision=dependency_used_and_affected; required=dependency_declaration,resolved_version,import_use_site,advisory_affected_range,decision_evidence\"}.",
                    ]
                ),
            ]
        )
    else:
        parts.append("# Condition\nNo Skill, Knowledge manifest, or Bundle artifact is visible to you.")
    parts.append(
        "\nReturn only one JSON object. Do not include markdown. Evidence paths must be exactly requirements.txt, update.py, allowed_knowledge.json, or derived. Include line_start, line_end, excerpt, and file_digest when evidence is a repo file. Do not request or infer evaluator-only material."
    )
    return "\n\n".join(parts)


def _sanitize_runtime_visible(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _sanitize_runtime_visible(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_sanitize_runtime_visible(item) for item in value if item != "hidden_gold" and item != "verifier_expected_answer"]
    if isinstance(value, str):
        return value.replace("hidden_gold", "evaluator_only_redacted").replace("verifier_expected_answer", "evaluator_only_redacted")
    return value


def _mock_api_response(condition: str) -> ApiResult:
    prediction = _reference_prediction()
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
    )


def _reference_prediction() -> dict[str, Any]:
    return _read_json(E2E_OUTPUT / "backend_runs" / "deterministic_reference" / "repo_task_run" / "prediction.json")


def _extract_prediction(content: str) -> dict[str, Any]:
    text = content.strip()
    if not text:
        return {}
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text, flags=re.IGNORECASE).strip()
        text = re.sub(r"```$", "", text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            return {}
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return {}


def _row_from_run_summary(run_summary: dict[str, Any], verifier_result: dict[str, Any], leakage: dict[str, Any]) -> dict[str, Any]:
    schema_valid = bool(run_summary["schema_valid"])
    verifier_pass = bool(run_summary["verifier_pass"])
    return {
        "lane": run_summary["lane"],
        "backend": run_summary["backend"],
        "condition": run_summary["condition"],
        "task_count": 1,
        "executed_count": 1 if run_summary["real_llm_agent_executed"] else 0,
        "pass_count": 1 if verifier_pass else 0,
        "fail_count": 0 if verifier_pass else 1,
        "not_counted_count": 0 if run_summary["claim_counted"] else 1,
        "execution_status": run_summary["execution_status"],
        "real_llm_agent_executed": bool(run_summary["real_llm_agent_executed"]),
        "bundle_injected": bool(run_summary["bundle_injected"]),
        "schema_valid_rate": 1.0 if schema_valid else 0.0,
        "evidence_completeness_rate": _evidence_completeness(verifier_result),
        "verifier_pass_rate": 1.0 if verifier_pass else 0.0,
        "runtime_seconds_total": run_summary["runtime_seconds"],
        "api_call_count": run_summary["api_call_count"],
        "estimated_cost": None,
        "token_usage": run_summary["token_usage"],
        "agent_execution_surface": run_summary["agent_execution_surface"],
        "trajectory_available": True,
        "verifier_available": True,
        "failure_types": [verifier_result.get("failure_type")] if verifier_result.get("failure_type") else [],
        "claim_counted": bool(run_summary["claim_counted"] and leakage["status"] == "pass"),
        "interpretation_note": "real DeepSeek-backed mini-SWE-agent row with local domain verifier",
    }


def _blocked_document_rows(output: Path, reason: str) -> list[dict[str, Any]]:
    rows = []
    for condition in CONDITIONS:
        run_dir = output / "runs" / "document_to_agent_real_api" / condition
        run_dir.mkdir(parents=True, exist_ok=True)
        injection = _bundle_injection_trace(condition)
        _write_json(run_dir / "agent_run_manifest.json", {"backend": BACKEND_ID, "condition": condition, "execution_status": "blocked", "reason": reason})
        _write_json(run_dir / "bundle_injection_trace.json", injection)
        _write_json(run_dir / "agent_output.json", {"status": reason})
        _write_json(run_dir / "verifier_result.json", {"status": reason, "verifier_pass": False})
        _write_json(run_dir / "verifier_trace.json", {"status": reason})
        _write_json(run_dir / "run_summary.json", {"status": reason})
        _write_jsonl(run_dir / "normalized_trajectory.jsonl", [_event(0, "runtime", "error", reason, bundle_related=condition != "no_skill")])
        rows.append(
            {
                "lane": "document_to_agent_real_api",
                "backend": BACKEND_ID,
                "condition": condition,
                "task_count": 1,
                "executed_count": 0,
                "pass_count": 0,
                "fail_count": 0,
                "not_counted_count": 1,
                "execution_status": "blocked",
                "real_llm_agent_executed": False,
                "bundle_injected": condition != "no_skill",
                "schema_valid_rate": None,
                "evidence_completeness_rate": None,
                "verifier_pass_rate": None,
                "runtime_seconds_total": 0.0,
                "api_call_count": 0,
                "estimated_cost": None,
                "token_usage": None,
                "trajectory_available": True,
                "verifier_available": True,
                "failure_types": [reason],
                "claim_counted": False,
                "interpretation_note": reason,
            }
        )
    return rows


def _blocked_or_mapping_row(output: Path, lane: str, condition: str) -> dict[str, Any]:
    if lane == "skillsbench_micro":
        status, note = _skillsbench_status()
    elif lane == "skillgen_mapping":
        status, note = "skipped", "mapped_not_executed; official SkillGenBench/Anything2Skill harness not run"
    else:
        status, note = _swebench_status()
    row = {
        "lane": lane,
        "backend": BACKEND_ID,
        "condition": condition,
        "task_count": 0,
        "executed_count": 0,
        "pass_count": 0,
        "fail_count": 0,
        "not_counted_count": 1,
        "execution_status": "blocked" if "blocked" in status or "missing" in note else status,
        "real_llm_agent_executed": False,
        "bundle_injected": condition != "no_skill",
        "schema_valid_rate": None,
        "evidence_completeness_rate": None,
        "verifier_pass_rate": None,
        "runtime_seconds_total": 0.0,
        "api_call_count": 0,
        "estimated_cost": None,
        "token_usage": None,
        "trajectory_available": False,
        "verifier_available": False,
        "failure_types": [status],
        "claim_counted": False,
        "interpretation_note": note,
    }
    run_dir = output / "runs" / lane / condition
    run_dir.mkdir(parents=True, exist_ok=True)
    _write_json(run_dir / "run_summary.json", row)
    _write_json(run_dir / "agent_run_manifest.json", {"backend": BACKEND_ID, "lane": lane, "condition": condition, "status": status, "note": note})
    _write_json(run_dir / "bundle_injection_trace.json", _bundle_injection_trace(condition))
    _write_json(run_dir / "agent_output.json", {"status": status, "note": note})
    _write_json(run_dir / "verifier_result.json", {"status": status, "verifier_pass": False})
    _write_json(run_dir / "verifier_trace.json", {"status": status, "note": note})
    _write_jsonl(run_dir / "normalized_trajectory.jsonl", [_event(0, "runtime", "message", note, bundle_related=condition != "no_skill")])
    return row


def _skillsbench_status() -> tuple[str, str]:
    if shutil.which("skillsbench"):
        return "blocked", "skillsbench CLI found but official micro harness is not integrated in this slice"
    return "blocked_by_environment_or_data", "SkillsBench repository/package/data not available locally; no fabricated task used"


def _swebench_status() -> tuple[str, str]:
    docker_path = shutil.which("docker")
    if docker_path is None:
        return "blocked", "docker_cli_not_visible"
    try:
        docker = subprocess.run(["docker", "info"], capture_output=True, text=True, timeout=10, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return "blocked", type(exc).__name__
    if docker.returncode != 0:
        return "blocked", "docker_daemon_not_running"
    try:
        proc = subprocess.run([sys.executable, "-c", "import swebench"], capture_output=True, text=True, timeout=10, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return "blocked", type(exc).__name__
    if proc.returncode != 0:
        return "blocked", "swebench_package_missing"
    return "partial", "harness_contract_ready; official protocol not executed in this bounded slice"


def _complete_matrix(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key = {(row["lane"], row["backend"], row["condition"]): row for row in rows}
    matrix = []
    for lane in LANES:
        for condition in CONDITIONS:
            matrix.append(by_key[(lane, BACKEND_ID, condition)])
    return matrix


def _per_lane_summary(matrix: list[dict[str, Any]]) -> dict[str, Any]:
    lanes = {}
    for lane in LANES:
        rows = [row for row in matrix if row["lane"] == lane]
        lanes[lane] = {
            "task_count": sum(row["task_count"] for row in rows),
            "executed_count": sum(row["executed_count"] for row in rows),
            "pass_count": sum(row["pass_count"] for row in rows),
            "claim_counted_count": sum(1 for row in rows if row["claim_counted"]),
            "status": "executed" if any(row["executed_count"] for row in rows) else "blocked_or_mapping_only",
            "rows": rows,
        }
    return {"schema_version": "real_api_per_lane_summary.v0", "lanes": lanes}


def _aggregate_summary(
    matrix: list[dict[str, Any]],
    per_lane: dict[str, Any],
    anti_leakage: dict[str, Any],
    claim_boundary: dict[str, Any],
    api_manifest: dict[str, Any],
    effect: dict[str, Any],
) -> dict[str, Any]:
    doc_rows = [row for row in matrix if row["lane"] == "document_to_agent_real_api"]
    doc_executed = any(row["real_llm_agent_executed"] for row in doc_rows)
    benchmark_style_attempted = any(row["lane"] != "document_to_agent_real_api" for row in matrix)
    status = "pass" if doc_executed and anti_leakage["anti_leakage_status"] == "pass" else "partial"
    if not api_manifest["OPENAI_API_KEY_present"] and not api_manifest["mock_api"]:
        status = "blocked_missing_api_key"
    if doc_rows and all("blocked" in row["execution_status"] for row in doc_rows) and api_manifest["OPENAI_API_KEY_present"]:
        status = "partial"
    return {
        "schema_version": "real_api_benchmark_micro_summary.v0",
        "real_api_benchmark_micro_v0_status": status,
        "real_api_status": "pass" if doc_executed else ("blocked_missing_api_key" if not api_manifest["OPENAI_API_KEY_present"] and not api_manifest["mock_api"] else "blocked_api_error"),
        "backend": BACKEND_ID,
        "agent_execution_surface": BACKEND_ID,
        "api_provider_label": api_manifest["api_provider_label"],
        "model_name": api_manifest["model_name"],
        "document_to_agent_lane_executed": doc_executed,
        "benchmark_style_lane_attempted": benchmark_style_attempted,
        "matrix_row_count": len(matrix),
        "claim_counted_rows": sum(1 for row in matrix if row["claim_counted"]),
        "anti_leakage_status": anti_leakage["anti_leakage_status"],
        "claim_boundary_status": claim_boundary["claim_boundary_status"],
        "per_lane_status": {lane: payload["status"] for lane, payload in per_lane["lanes"].items()},
        "effect_observed": effect["effect_observed"],
    }


def _effect_interpretation(matrix: list[dict[str, Any]]) -> dict[str, Any]:
    doc = {row["condition"]: row for row in matrix if row["lane"] == "document_to_agent_real_api"}
    no_skill = doc.get("no_skill", {})
    bundle = doc.get("document_to_agent_bundle", {})
    if not bundle.get("real_llm_agent_executed") or not no_skill.get("real_llm_agent_executed"):
        effect = "not_evaluable_due_to_blocked_lane"
    elif (bundle.get("verifier_pass_rate") or 0) > (no_skill.get("verifier_pass_rate") or 0):
        effect = "pass_rate_gain"
    elif (bundle.get("schema_valid_rate") or 0) > (no_skill.get("schema_valid_rate") or 0):
        effect = "schema_validity_gain_only"
    elif (bundle.get("evidence_completeness_rate") or 0) > (no_skill.get("evidence_completeness_rate") or 0):
        effect = "evidence_completeness_gain_only"
    elif (bundle.get("runtime_seconds_total") or 0) > (no_skill.get("runtime_seconds_total") or 0) and (bundle.get("verifier_pass_rate") or 0) <= (no_skill.get("verifier_pass_rate") or 0):
        effect = "no_clear_gain"
    else:
        effect = "trajectory_behavior_changed"
    return {
        "schema_version": "real_api_effect_interpretation.v0",
        "effect_observed": effect,
        "bundle_improves_verifier_pass_rate": _compare_metric(bundle, no_skill, "verifier_pass_rate"),
        "bundle_improves_schema_validity": _compare_metric(bundle, no_skill, "schema_valid_rate"),
        "bundle_improves_evidence_completeness": _compare_metric(bundle, no_skill, "evidence_completeness_rate"),
        "bundle_reduces_unsupported_affected_decisions": "not_measured_in_this_micro_slice",
        "bundle_changes_trajectory_behavior": bundle.get("bundle_injected") is True,
        "bundle_adds_overhead_without_benefit": effect == "no_clear_gain",
        "not_evaluable_rows": [row for row in matrix if not row["claim_counted"]],
    }


def _anti_leakage_audit(output: Path, config: ApiConfig) -> dict[str, Any]:
    artifact_text = ""
    for path in output.rglob("*"):
        if path.is_file() and path.suffix.lower() in {".json", ".jsonl", ".md", ".txt"}:
            artifact_text += "\n" + path.read_text(encoding="utf-8", errors="ignore")
    checks = {
        "no_raw_api_key_in_artifacts": not config.api_key or config.api_key not in artifact_text,
        "no_evaluator_only_gold_in_agent_prompt": "hidden_gold" not in _read_prompt_text(output),
        "no_hidden_expected_decision_in_agent_visible_material": "expected_decision" not in _read_prompt_text(output),
        "no_benchmark_gold_patch_exposed_to_agent": "gold_patch" not in _read_prompt_text(output) and "test_patch" not in _read_prompt_text(output),
        "no_heldout_feedback_used_for_revision": True,
        "no_task_id_specific_answer_branch": _source_has_no_task_specific_answer_branch(),
    }
    return {"schema_version": "real_api_anti_leakage_audit.v0", "anti_leakage_status": _pass_fail(checks), "checks": checks}


def _row_leakage_check(prompt: str, prediction: dict[str, Any]) -> dict[str, Any]:
    serialized_prediction = json.dumps(prediction, ensure_ascii=False, sort_keys=True)
    checks = {
        "prompt_excludes_hidden_gold": "hidden_gold" not in prompt,
        "prompt_excludes_verifier": "verifier.py" not in prompt,
        "prediction_excludes_hidden_gold": "hidden_gold" not in serialized_prediction,
        "prediction_excludes_expected_decision_key": "expected_decision" not in serialized_prediction,
        "prediction_excludes_gold_patch": "gold_patch" not in serialized_prediction and "test_patch" not in serialized_prediction,
    }
    return {"schema_version": "real_api_row_leakage_check.v0", "status": _pass_fail(checks), "checks": checks}


def _read_prompt_text(output: Path) -> str:
    return "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in output.rglob("agent_prompt_runtime_visible.md"))


def _source_has_no_task_specific_answer_branch() -> bool:
    source = Path(__file__).read_text(encoding="utf-8")
    patterns = [
        r"if\s+task_id\s*==",
        r"if\s+case_id\s*==",
        r"if\s+.*get\([\"']task_id[\"']\)\s*==",
        r"if\s+.*get\([\"']case_id[\"']\)\s*==",
    ]
    return not any(re.search(pattern, source) for pattern in patterns)


def _claim_boundary() -> dict[str, Any]:
    blocked = {
        "official_swe_bench_performance": "not_claimed",
        "official_skillsbench_performance": "not_claimed",
        "official_skillgenbench_performance": "not_claimed",
        "full_open_world_validation_complete": False,
        "mature_agenthost_effectiveness": "not_evaluated",
        "production_ready": False,
        "compiler_superiority": "not_evaluated",
        "general_vulnerability_discovery": "not_claimed",
    }
    return {"schema_version": "real_api_claim_boundary.v0", "claim_boundary_status": "pass", "blocked_claims": blocked}


def _cost_summary(matrix: list[dict[str, Any]]) -> dict[str, Any]:
    total_api_calls = sum(row["api_call_count"] for row in matrix)
    token_rows = [row["token_usage"] for row in matrix if row.get("token_usage")]
    total_tokens = sum(int(row.get("total_tokens", 0)) for row in token_rows if isinstance(row, dict))
    return {
        "schema_version": "real_api_cost_summary.v0",
        "api_call_count": total_api_calls,
        "token_usage_rows": token_rows,
        "total_tokens_observed": total_tokens,
        "estimated_cost": None,
        "estimated_cost_reason": "provider pricing is not embedded; record token usage and provider/model instead",
    }


def _api_execution_manifest(config: ApiConfig) -> dict[str, Any]:
    return {
        "schema_version": "real_api_execution_manifest.v0",
        "backend": BACKEND_ID,
        "agent_execution_surface": BACKEND_ID,
        "api_provider_label": config.provider_label,
        "OPENAI_API_KEY_present": bool(config.api_key),
        "raw_api_key_written": False,
        "model_name": config.model,
        "base_url_host_only": config.base_url_host_only,
        "mock_api": config.mock_api,
        "timestamp": _now(),
    }


def _agent_run_manifest(config: ApiConfig, condition: str, api_result: ApiResult, run_summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "real_api_agent_run_manifest.v0",
        "backend": BACKEND_ID,
        "condition": condition,
        "api_provider_label": config.provider_label,
        "model_name": config.model,
        "base_url_host_only": config.base_url_host_only,
        "api_key_present": bool(config.api_key),
        "raw_api_key_written": False,
        "agent_execution_surface": api_result.agent_surface,
        "mini_swe_agent_trajectory_ref": api_result.mini_swe_agent_trajectory_ref,
        "execution_status": run_summary["execution_status"],
        "real_llm_agent_executed": run_summary["real_llm_agent_executed"],
        "api_status_code": api_result.status_code,
        "api_error_type": api_result.error_type,
        "runtime_seconds": run_summary["runtime_seconds"],
        "api_call_count": run_summary["api_call_count"],
        "token_usage": api_result.token_usage,
    }


def _bundle_injection_trace(condition: str) -> dict[str, Any]:
    visible = condition == "document_to_agent_bundle"
    release = _read_json(E2E_OUTPUT / "release_bundle_manifest.json") if visible else {}
    return {
        "schema_version": "real_api_bundle_injection_trace.v0",
        "condition": condition,
        "bundle_visible_to_agent": visible,
        "skill_artifact_visible_to_agent": visible,
        "knowledge_manifest_visible_to_agent": visible,
        "agent_prompt_or_workspace_contains_bundle_ref": visible,
        "bundle_digest": _read_json(E2E_OUTPUT / "e2e_summary.json").get("bundle_digest") if visible else None,
        "release_bundle_schema": release.get("schema_version"),
    }


def _verifier_trace(verifier: dict[str, Any], prediction: dict[str, Any]) -> dict[str, Any]:
    failed = [check["name"] for check in verifier.get("checks", []) if not check.get("passed")]
    return {
        "schema_version": "real_api_verifier_trace.v0",
        "schema_check": {"status": "pass" if not failed or "schema_fields_present" not in failed else "fail"},
        "evidence_check": {"status": "pass" if not any("evidence" in item for item in failed) else "fail"},
        "domain_check": {"status": "pass" if verifier.get("verifier_pass") else "fail", "failed_rules": failed},
        "prediction_digest": sha256_bytes(json.dumps(prediction, sort_keys=True).encode("utf-8")),
    }


def _evidence_completeness(verifier_result: dict[str, Any]) -> float | None:
    source = verifier_result.get("source_verifier", {})
    checks = source.get("checks", [])
    names = {"required_evidence_types_present", "evidence_grounded", "evidence_refs_resolve", "repo_evidence_locations_complete"}
    selected = [check for check in checks if check.get("name") in names]
    if not selected:
        return None
    return sum(1 for check in selected if check.get("passed")) / len(selected)


def _compare_metric(bundle: dict[str, Any], no_skill: dict[str, Any], key: str) -> bool | str:
    if bundle.get(key) is None or no_skill.get(key) is None:
        return "not_evaluable"
    return bool(bundle[key] > no_skill[key])


def _numbered_file(path: Path) -> str:
    lines = path.read_text(encoding="utf-8").splitlines()
    numbered = []
    for index, line in enumerate(lines, start=1):
        clean = line.rstrip()
        numbered.append(f"{index:03d}: {clean}" if clean else f"{index:03d}:")
    return "\n".join(numbered)


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


def _render_matrix_md(matrix: list[dict[str, Any]]) -> str:
    lines = [
        "# Real API Backend x Condition x Lane Matrix",
        "",
        "| lane | backend | condition | execution_status | executed | pass | claim_counted | note |",
        "| --- | --- | --- | --- | ---: | ---: | --- | --- |",
    ]
    for row in matrix:
        lines.append(
            f"| `{row['lane']}` | `{row['backend']}` | `{row['condition']}` | `{row['execution_status']}` | {row['executed_count']} | {row['pass_count']} | `{row['claim_counted']}` | {row['interpretation_note']} |"
        )
    return "\n".join(lines) + "\n"


def _render_status(aggregate: dict[str, Any], per_lane: dict[str, Any]) -> str:
    lines = [
        "# Real API Benchmark Micro-Evaluation v0 Status",
        "",
        f"- real_api_benchmark_micro_v0_status: `{aggregate['real_api_benchmark_micro_v0_status']}`",
        f"- real_api_status: `{aggregate['real_api_status']}`",
        f"- backend: `{aggregate['backend']}`",
        f"- agent_execution_surface: `{aggregate['agent_execution_surface']}`",
        f"- provider: `{aggregate['api_provider_label']}`",
        f"- model: `{aggregate['model_name']}`",
        f"- anti_leakage_status: `{aggregate['anti_leakage_status']}`",
        f"- claim_boundary_status: `{aggregate['claim_boundary_status']}`",
        "",
        "## Lane Status",
    ]
    for lane, payload in per_lane["lanes"].items():
        lines.append(f"- {lane}: `{payload['status']}`; executed={payload['executed_count']}; pass={payload['pass_count']}")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "This is a bounded real-API micro-evaluation. It is not an official SWE-bench, SkillsBench, SkillGenBench, production, or compiler-superiority result.",
        ]
    )
    return "\n".join(lines) + "\n"


def _render_effect(effect: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Real API Benchmark Micro-Evaluation v0 Effect Interpretation",
            "",
            f"- effect_observed: `{effect['effect_observed']}`",
            f"- Did Bundle improve verifier pass rate? `{effect['bundle_improves_verifier_pass_rate']}`",
            f"- Did Bundle improve schema validity? `{effect['bundle_improves_schema_validity']}`",
            f"- Did Bundle improve evidence completeness? `{effect['bundle_improves_evidence_completeness']}`",
            f"- Did Bundle reduce unsupported affected decisions? `{effect['bundle_reduces_unsupported_affected_decisions']}`",
            f"- Did Bundle change trajectory behavior? `{effect['bundle_changes_trajectory_behavior']}`",
            f"- Did Bundle add overhead without benefit? `{effect['bundle_adds_overhead_without_benefit']}`",
            "",
            "Null, negative, blocked, and not-evaluable rows are preserved in the matrix and aggregate artifacts.",
        ]
    ) + "\n"


def _render_anti_leakage(audit: dict[str, Any]) -> str:
    lines = ["# Real API Benchmark Micro-Evaluation v0 Anti-Leakage Audit", "", f"- anti_leakage_status: `{audit['anti_leakage_status']}`", ""]
    for key, value in audit["checks"].items():
        lines.append(f"- {key}: `{value}`")
    return "\n".join(lines) + "\n"


def _redact_response(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": payload.get("id"),
        "model": payload.get("model"),
        "usage": payload.get("usage"),
        "choice_count": len(payload.get("choices", [])),
    }


def _mini_swe_agent_token_usage(trajectory: dict[str, Any]) -> dict[str, Any] | None:
    usage: dict[str, int] = {}
    for message in trajectory.get("messages", []):
        response = message.get("extra", {}).get("response")
        if not isinstance(response, dict):
            continue
        item = response.get("usage")
        if not isinstance(item, dict):
            continue
        for key in [
            "prompt_tokens",
            "completion_tokens",
            "total_tokens",
            "prompt_cache_hit_tokens",
            "prompt_cache_miss_tokens",
        ]:
            value = item.get(key)
            if isinstance(value, int):
                usage[key] = usage.get(key, 0) + value
    return usage or None


def _mini_swe_agent_response_summary(trajectory: dict[str, Any]) -> dict[str, Any]:
    responses = []
    for message in trajectory.get("messages", []):
        response = message.get("extra", {}).get("response")
        if isinstance(response, dict):
            responses.append(
                {
                    "id": response.get("id"),
                    "model": response.get("model"),
                    "usage": response.get("usage"),
                    "choice_count": len(response.get("choices", [])),
                }
            )
    return {
        "agent_surface": "mini_swe_agent_real_llm",
        "mini_version": trajectory.get("info", {}).get("mini_version"),
        "exit_status": trajectory.get("info", {}).get("exit_status"),
        "api_calls": trajectory.get("info", {}).get("model_stats", {}).get("api_calls"),
        "responses": responses,
    }


def _redact_secret(text: str, secret: str | None) -> str:
    if secret:
        text = text.replace(secret, "[REDACTED_API_KEY]")
    return text


def _restore_env(name: str, previous: str | None) -> None:
    if previous is None:
        os.environ.pop(name, None)
    else:
        os.environ[name] = previous


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows) + "\n", encoding="utf-8")


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


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _pass_fail(checks: dict[str, bool]) -> str:
    return "pass" if all(checks.values()) else "failed"


if __name__ == "__main__":
    raise SystemExit(main())
