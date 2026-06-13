from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import streamlit as st


ROOT = Path(__file__).resolve().parents[1]
TASK_CASES_DIR = ROOT / "data" / "task_cases"
RUNS_DIR = ROOT / "runs"
OUTPUTS_DIR = ROOT / "outputs"
REPORTS_DIR = ROOT / "reports"
DOCS_DIR = ROOT / "docs"
REVIEW_PACKAGE_ZIP = ROOT / "review_package_export.zip"
CUSTOM_RUN_DIR = RUNS_DIR / "custom_material_live_demo"
GENERALIZATION_SUMMARY_PATH = OUTPUTS_DIR / "validation" / "generalization_suite.json"
NEGATIVE_CONTROL_PATH = OUTPUTS_DIR / "validation" / "negative_controls.json"
REPEATABILITY_PATH = OUTPUTS_DIR / "validation" / "harbor_llm_repeatability_upload.json"
LOCAL_LLM_SMOKE_PATH = OUTPUTS_DIR / "live_llm_upload_001" / "summary.json"
LOCAL_LLM_LOOP_PATH = OUTPUTS_DIR / "live_llm_repair_loop_upload_001" / "summary.json"
HARBOR_UPLOAD_LOOP_PATH = OUTPUTS_DIR / "harbor_llm_repair_loop_upload_001" / "summary.json"
HARBOR_CONFIG_LOOP_PATH = OUTPUTS_DIR / "harbor_llm_repair_loop_config_001" / "summary.json"
SYSTEM_ACCEPTANCE_PATH = OUTPUTS_DIR / "system_acceptance_001" / "summary.json"
CLAIM_BOUNDARY_PATH = DOCS_DIR / "CLAIM_BOUNDARY.md"
MORNING_STATUS_PATH = REPORTS_DIR / "MORNING_STATUS_0800.md"
BACKEND_STATUS_PATH = REPORTS_DIR / "BACKEND_MATURITY_STATUS.md"
MATURITY_PLAN_PATH = DOCS_DIR / "MATURITY_GAP_CLOSURE_PLAN.md"


def _identity_cache_decorator(*_args: Any, **_kwargs: Any):
    def decorator(func):
        return func

    return decorator


cache_data = getattr(st, "cache_data", _identity_cache_decorator)


FAMILY_META: dict[str, dict[str, str]] = {
    "upload_security": {
        "label": "文件上传安全",
        "user_goal": "检查上传服务是否真的更安全",
        "user_input": "专家材料 + 上传接口/配置",
    },
    "config_security": {
        "label": "生产配置安全",
        "user_goal": "避免把干净配置误报成高风险",
        "user_input": "专家材料 + 配置文件",
    },
    "auth_access_control": {
        "label": "鉴权与对象访问",
        "user_goal": "让报告能解释谁可以访问什么对象",
        "user_input": "专家材料 + 鉴权代码/接口",
    },
    "api_or_code_review": {
        "label": "API/代码审查",
        "user_goal": "让报告结构正确而且能落到证据",
        "user_input": "专家材料 + API 或代码片段",
    },
}


CAPABILITY_LABELS: dict[str, str] = {
    "UPLOAD_TYPE_MAGIC": "上传类型与内容校验",
    "UPLOAD_PATH_ISOLATION": "上传路径隔离",
    "UPLOAD_AUDIT_RETENTION": "上传审计与保留",
    "CONFIG_AUDIT_EXPORT": "生产审计导出",
    "CONFIG_ENV_GUARD": "环境边界防误报",
    "AUTH_SCOPE_MATRIX": "权限矩阵",
    "AUTH_OBJECT_OWNERSHIP": "对象归属边界",
    "AUTH_ERROR_ENVELOPE": "鉴权错误封装",
    "API_SCHEMA_CONTRACT": "报告 schema 契约",
    "API_OVERBROAD_RISK": "过宽风险约束",
}


CUSTOM_HINT = """任务目标：
根据专家知识，生成一个可执行的安全审查 Skill，并展示它在执行后如何被反馈修正。

专家材料：
- 高风险文件上传不能只看扩展名，要联合检查 MIME、内容魔数、大小和隔离存储。
- 用户可控文件名不能直接拼接到公开路径。
- 上传、下载、删除等高风险动作必须进入审计日志并设置保留周期。
- 错误响应不能暴露内部路径、token、api_key 或 stacktrace。

目标资产：
```python
@app.post("/upload")
def upload(filename, content_type, file_bytes):
    if filename.endswith((".png", ".jpg")):
        save("/public/uploads/" + filename, file_bytes)
    return {"ok": True, "debug_path": "/public/uploads/" + filename}
```

```yaml
debug: true
audit_log_retention_days: null
SECRET_KEY: changeme
```
"""


@dataclass(frozen=True)
class TaskCase:
    case_id: str
    title: str
    task_family: str
    expected_capabilities: tuple[str, ...]
    v1_capabilities: tuple[str, ...]
    typical_feedback: str
    typical_repair: str
    case_dir: Path


@dataclass(frozen=True)
class DemoScenario:
    scenario_id: str
    name: str
    task_brief: str
    expert_material: str
    target_asset: str
    expected_capabilities: tuple[str, ...]
    v1_omits: tuple[str, ...]


DEMO_CAPABILITIES: dict[str, dict[str, str | int]] = {
    "input_validation": {
        "title": "输入校验",
        "evidence_hint": "filename, user_id, q 等用户可控字段直接进入处理流程。",
        "fix_hint": "补充类型、长度、白名单与拒绝策略。",
        "token_cost": 40,
    },
    "sensitive_leak": {
        "title": "敏感信息泄露",
        "evidence_hint": "debug_path, stacktrace, token, api_key 暴露在返回或日志中。",
        "fix_hint": "统一错误响应，并对路径、邮箱、token 和内部错误脱敏。",
        "token_cost": 39,
    },
    "upload_storage": {
        "title": "上传类型与存储隔离",
        "evidence_hint": "filename.endswith(...) 且写入 /public/uploads/。",
        "fix_hint": "联合检查 MIME、magic number、大小并使用非公开存储目录。",
        "token_cost": 47,
    },
    "audit_logging": {
        "title": "审计日志保留",
        "evidence_hint": "audit_log_retention_days: null。",
        "fix_hint": "记录 actor/object/action/result/timestamp 并配置保留周期。",
        "token_cost": 42,
    },
    "path_traversal": {
        "title": "路径穿越",
        "evidence_hint": 'save("/public/uploads/" + filename, file_bytes)',
        "fix_hint": "使用安全文件名、路径归一化和随机化存储名。",
        "token_cost": 43,
    },
    "weak_config": {
        "title": "弱密钥与调试配置",
        "evidence_hint": "debug: true, SECRET_KEY: changeme。",
        "fix_hint": "关闭生产 debug，替换强密钥，并限制敏感配置暴露。",
        "token_cost": 44,
    },
}


DEFAULT_SCENARIO = DemoScenario(
    scenario_id="upload_external_review",
    name="文件上传服务安全审查",
    task_brief="审查上传服务是否存在类型绕过、路径穿越、调试泄露、审计缺失和配置弱点。",
    expert_material=(
        "专家经验：文件上传不能只看扩展名，要联合检查 MIME、内容魔数、大小和隔离存储；"
        "用户可控文件名不能直接拼接到公开路径；上传/下载/删除要进入审计日志并设置保留周期；"
        "错误响应不能暴露内部路径、token、api_key 或 stacktrace。"
    ),
    target_asset=(
        '```python\n'
        '@app.post("/upload")\n'
        'def upload(filename, content_type, file_bytes):\n'
        '    if filename.endswith((".png", ".jpg")):\n'
        '        save("/public/uploads/" + filename, file_bytes)\n'
        '    return {"ok": True, "debug_path": "/public/uploads/" + filename}\n\n'
        '@app.get("/download")\n'
        'def download(filename: str):\n'
        '    return send_file("/public/uploads/" + filename)\n'
        '```\n\n'
        '```yaml\n'
        'debug: true\n'
        'audit_log_retention_days: null\n'
        'SECRET_KEY: changeme\n'
        '```'
    ),
    expected_capabilities=(
        "input_validation",
        "sensitive_leak",
        "upload_storage",
        "audit_logging",
        "path_traversal",
        "weak_config",
    ),
    v1_omits=("upload_storage", "audit_logging"),
)

SCENARIOS = [DEFAULT_SCENARIO]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def read_json(path: Path) -> dict[str, Any] | list[Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (json.JSONDecodeError, OSError):
        return None


def render_css() -> None:
    st.markdown(
        """
        <style>
        .block-container {
            max-width: 1180px;
            padding-top: 1.7rem;
            padding-bottom: 2rem;
        }
        .pill {
            display: inline-block;
            padding: 0.22rem 0.55rem;
            border: 1px solid #d8e0ea;
            border-radius: 999px;
            font-size: 0.83rem;
            color: #334155;
            background: #f8fafc;
            margin-right: 0.45rem;
            margin-bottom: 0.45rem;
        }
        .section-note {
            color: #52606d;
            font-size: 0.94rem;
        }
        .card {
            border: 1px solid #dbe3ec;
            border-radius: 8px;
            padding: 0.9rem 1rem;
            background: #ffffff;
            height: 100%;
        }
        .small-title {
            font-size: 0.84rem;
            color: #64748b;
            margin-bottom: 0.4rem;
        }
        .big-line {
            font-size: 1.02rem;
            color: #0f172a;
            font-weight: 600;
            margin-bottom: 0.35rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


@cache_data(show_spinner=False)
def load_task_cases() -> list[TaskCase]:
    cases: list[TaskCase] = []
    for case_file in sorted(TASK_CASES_DIR.glob("*/case.yaml")):
        payload = read_json(case_file)
        if not isinstance(payload, dict):
            continue
        if payload.get("negative_control"):
            continue
        cases.append(
            TaskCase(
                case_id=str(payload["case_id"]),
                title=str(payload["title"]),
                task_family=str(payload["task_family"]),
                expected_capabilities=tuple(payload.get("expected_capabilities", [])),
                v1_capabilities=tuple(payload.get("v1_capabilities", [])),
                typical_feedback=str(payload.get("typical_feedback", "")),
                typical_repair=str(payload.get("typical_repair", "")),
                case_dir=case_file.parent,
            )
        )
    return cases


@cache_data(show_spinner=False)
def load_generalization_summary() -> dict[str, Any]:
    payload = read_json(GENERALIZATION_SUMMARY_PATH)
    return payload if isinstance(payload, dict) else {}


@cache_data(show_spinner=False)
def load_case_bundle(case_id: str) -> dict[str, Any]:
    case = next(item for item in load_task_cases() if item.case_id == case_id)
    run_dir = RUNS_DIR / "generalization" / case_id
    generalization = load_generalization_summary()
    summary_item = next((row for row in generalization.get("results", []) if row["scenario"] == case_id), None)
    return {
        "case": case,
        "run_dir": run_dir,
        "summary_item": summary_item or {},
        "task_spec": read_json(run_dir / "task_spec" / "task_spec.json") or {},
        "expert_material": read_text(run_dir / "source_materials" / "expert_material.md")
        if (run_dir / "source_materials" / "expert_material.md").exists()
        else "",
        "target_asset": read_text(run_dir / "target_asset" / "target.md")
        if (run_dir / "target_asset" / "target.md").exists()
        else "",
        "source_mapping": read_json(run_dir / "provenance" / "source_to_skill_mapping.json") or [],
        "source_trace": read_json(run_dir / "trace" / "source_trace.json") or [],
        "feedback_trace": read_json(run_dir / "trace" / "feedback_trace_A1.json") or {},
        "revision_trace": read_json(run_dir / "trace" / "revision_trace_v1_to_v2.json") or {},
        "gate_decision": read_json(run_dir / "revision" / "gate_decision.json") or {},
        "repair_decision": read_json(run_dir / "revision" / "repair_decision.json") or {},
        "metrics": read_json(run_dir / "summary" / "metrics.json") or {},
        "a0_output": read_json(run_dir / "attempts" / "A0" / "agent_output.json") or {},
        "a1_output": read_json(run_dir / "attempts" / "A1" / "agent_output.json") or {},
        "a2_output": read_json(run_dir / "attempts" / "A2" / "agent_output.json") or {},
        "a0_report": read_json(run_dir / "verifier" / "A0_report.json") or {},
        "a1_report": read_json(run_dir / "verifier" / "A1_report.json") or {},
        "a2_report": read_json(run_dir / "verifier" / "A2_report.json") or {},
        "skill_v1": read_text(run_dir / "skills" / "skill_v1" / "SKILL.md")
        if (run_dir / "skills" / "skill_v1" / "SKILL.md").exists()
        else "",
        "skill_v2": read_text(run_dir / "skills" / "skill_v2" / "SKILL.md")
        if (run_dir / "skills" / "skill_v2" / "SKILL.md").exists()
        else "",
        "manifest_v1": read_json(run_dir / "skills" / "skill_v1" / "manifest.json") or {},
        "manifest_v2": read_json(run_dir / "skills" / "skill_v2" / "manifest.json") or {},
    }


def load_backend_evidence() -> dict[str, Any]:
    return {
        "system_acceptance": read_json(SYSTEM_ACCEPTANCE_PATH) or {},
        "negative_controls": read_json(NEGATIVE_CONTROL_PATH) or {},
        "local_llm_smoke": read_json(LOCAL_LLM_SMOKE_PATH) or {},
        "local_llm_loop": read_json(LOCAL_LLM_LOOP_PATH) or {},
        "harbor_upload_loop": read_json(HARBOR_UPLOAD_LOOP_PATH) or {},
        "harbor_config_loop": read_json(HARBOR_CONFIG_LOOP_PATH) or {},
        "repeatability": read_json(REPEATABILITY_PATH) or {},
    }


def family_label(task_family: str) -> str:
    return FAMILY_META.get(task_family, {}).get("label", task_family)


def capability_label(capability_id: str) -> str:
    return CAPABILITY_LABELS.get(capability_id, capability_id)


def format_capability_list(capabilities: list[str] | tuple[str, ...]) -> str:
    if not capabilities:
        return "none"
    return ", ".join(capability_label(item) for item in capabilities)


def changed_capabilities(bundle: dict[str, Any]) -> list[str]:
    before = set(bundle.get("manifest_v1", {}).get("capabilities", []))
    after = set(bundle.get("manifest_v2", {}).get("capabilities", []))
    return sorted(after - before)


def findings_by_capability(output: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = output.get("findings", [])
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        capability_id = row.get("capability_id")
        if capability_id:
            result[str(capability_id)] = row
    return result


def build_added_finding_rows(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    a1_findings = findings_by_capability(bundle.get("a1_output", {}))
    a2_findings = findings_by_capability(bundle.get("a2_output", {}))
    rows: list[dict[str, Any]] = []
    for capability_id in sorted(set(a2_findings) - set(a1_findings)):
        row = a2_findings[capability_id]
        rows.append(
            {
                "新增能力": capability_label(capability_id),
                "证据片段": row.get("evidence_span", ""),
                "修复建议": row.get("recommended_fix", ""),
            }
        )
    return rows


def artifact_metadata(relative_path: str) -> dict[str, str]:
    metadata = {
        "generated_by": "system",
        "depends_on": "-",
        "used_by": "-",
        "purpose": "artifact",
    }
    normalized = relative_path.replace("\\", "/")
    rules = [
        ("source_materials/", "user / expert material", "-", "skill compiler", "expert source"),
        ("target_asset/", "user / target asset", "-", "agent execution", "target under review"),
        ("task_spec/", "task case definition", "-", "runner + verifier", "scenario contract"),
        ("skills/skill_v1/SKILL.md", "distiller", "expert material + task case", "A1 agent", "initial skill"),
        ("skills/skill_v2/SKILL.md", "repair compiler", "A1 verifier feedback + repair policy", "A2 agent", "repaired skill"),
        ("skills/skill_v1/manifest.json", "distiller", "expert material + task case", "A1 agent", "skill metadata"),
        ("skills/skill_v2/manifest.json", "repair compiler", "A1 verifier feedback", "A2 agent", "skill metadata"),
        ("attempts/A1/agent_input.json", "runner", "skill_v1 + target asset", "A1 agent", "execution input"),
        ("attempts/A1/agent_output.json", "agent", "A1 input + skill_v1", "A1 verifier", "attempt report"),
        ("attempts/A2/agent_output.json", "agent", "A2 input + skill_v2", "A2 verifier", "attempt report"),
        ("verifier/A1_report.json", "deterministic verifier", "A1 agent output + verifier contract", "repair policy", "failure analysis"),
        ("verifier/A2_report.json", "deterministic verifier", "A2 agent output + verifier contract", "result view", "final validation"),
        ("trace/feedback_trace_A1.json", "trace recorder", "A1 verifier report", "revision trace", "typed feedback trace"),
        ("trace/revision_trace_v1_to_v2.json", "trace recorder", "repair decision + gate", "review UI", "revision trace"),
        ("provenance/source_to_skill_mapping.json", "compiler provenance writer", "expert material + skill_v2", "source table", "source-to-skill mapping"),
        ("revision/repair_decision.json", "repair policy", "A1 verifier report", "gate", "selected repair action"),
        ("revision/gate_decision.json", "validation gate", "repair decision + scores", "promotion to v2", "promotion decision"),
        ("summary/metrics.json", "suite runner", "A0/A1/A2 reports", "result dashboard", "scenario metrics"),
        ("inputs/task.md", "user", "-", "custom loop", "custom task text"),
        ("skills/skill_v1.md", "distiller", "custom task text", "A1 agent", "initial custom skill"),
        ("skills/skill_v2.md", "distiller", "A1 feedback", "A2 agent", "revised custom skill"),
        ("attempts/A1_skill_v1.json", "agent", "custom skill_v1 + task", "verifier", "custom attempt"),
        ("attempts/A2_skill_v2.json", "agent", "custom skill_v2 + task", "verifier", "custom attempt"),
        ("verifier/A1_feedback.json", "deterministic verifier", "A1 custom attempt", "repair step", "custom failure feedback"),
        ("verifier/A2_feedback.json", "deterministic verifier", "A2 custom attempt", "result view", "custom final validation"),
        ("revision/patch_plan.json", "repair policy", "A1 feedback", "skill_v2", "custom repair plan"),
        ("trajectory.jsonl", "runtime logger", "LLM calls or fallback steps", "debug view", "custom execution trace"),
        ("model_calls.json", "runtime logger", "LLM calls", "debug view", "model call log"),
        ("reports/correction_report.md", "report writer", "A1/A2 feedback", "review output", "human-readable correction note"),
    ]
    for prefix, generated_by, depends_on, used_by, purpose in rules:
        if normalized == prefix or normalized.startswith(prefix):
            metadata = {
                "generated_by": generated_by,
                "depends_on": depends_on,
                "used_by": used_by,
                "purpose": purpose,
            }
    return metadata


def collect_artifacts(base_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(base_dir.rglob("*")):
        if not path.is_file():
            continue
        relative_path = str(path.relative_to(base_dir))
        meta = artifact_metadata(relative_path)
        rows.append(
            {
                "path": relative_path,
                "size_bytes": path.stat().st_size,
                **meta,
            }
        )
    return rows


def preview_file(path: Path) -> None:
    suffix = path.suffix.lower()
    if suffix == ".json":
        payload = read_json(path)
        if payload is not None:
            st.json(payload)
            return
    content = read_text(path)
    language = "markdown" if suffix in {".md", ".markdown"} else "yaml" if suffix in {".yaml", ".yml"} else "text"
    st.code(content[:15000], language=language)


def write_json_file(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def scenario_by_id(scenario_id: str) -> DemoScenario:
    if scenario_id in {"upload", DEFAULT_SCENARIO.scenario_id}:
        return DEFAULT_SCENARIO
    for scenario in SCENARIOS:
        if scenario.scenario_id == scenario_id:
            return scenario
    raise KeyError(f"unknown scenario: {scenario_id}")


def package_directory_files(pkg: dict[str, Any], scenario: DemoScenario) -> dict[str, str]:
    capability_to_rule_file = {
        "input_validation": "rules/R002_input_validation.yaml",
        "sensitive_leak": "rules/R004_sensitive_information_leak.yaml",
        "upload_storage": "rules/R005_upload_type_and_storage.yaml",
        "audit_logging": "rules/R006_audit_logging_retention.yaml",
        "weak_config": "rules/R007_weak_secret_debug_config.yaml",
        "path_traversal": "rules/R008_path_traversal.yaml",
    }
    version = pkg["version"]
    package_id = f"upload/{version}" if scenario.scenario_id == DEFAULT_SCENARIO.scenario_id else f"{scenario.scenario_id}/{version}"
    files = {
        "manifest.yaml": (
            "schema_version: 0.2.0\n"
            f'package_id: "{package_id}"\n'
            "entrypoint: SKILL.md\n"
            "source_materials: source_materials/*\n"
            "target_asset: target_asset/*\n"
            "task_spec: task_spec/task_spec.json\n"
        ),
        "SKILL.md": (
            f"# {scenario.name} Skill {version}\n\n"
            "Use the listed capabilities to produce findings with evidence_span, risk_level, and recommended_fix.\n"
        ),
        "contracts/output_schema.json": json.dumps(
            {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "findings": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "finding_id": {"type": "string"},
                                "capability": {"type": "string"},
                                "evidence_span": {"type": "string"},
                                "risk_level": {"type": "string"},
                                "recommended_fix": {"type": "string"},
                            },
                            "required": ["finding_id", "capability", "evidence_span", "risk_level", "recommended_fix"],
                        },
                    }
                },
                "required": ["findings"],
            },
            ensure_ascii=False,
            indent=2,
        ),
        "contracts/verifier_contract.yaml": "checks:\n  - capability_coverage\n  - evidence_span\n  - recommended_fix\n",
        "trace_policy.yaml": "trace:\n  require_evidence_span: true\n  require_revision_reason: true\n",
        "examples/positive_example.md": "A good finding cites a concrete code/config span and gives a fix.\n",
        "examples/negative_example.md": "A weak finding says only 'security risk exists' without evidence.\n",
        "changelog.md": "v2 adds capabilities that A1 verifier marked as missing.\n",
    }
    for capability_id in pkg["included_capabilities"]:
        rel_path = capability_to_rule_file.get(capability_id)
        if not rel_path:
            continue
        meta = DEMO_CAPABILITIES[capability_id]
        files[rel_path] = (
            f"id: {capability_id}\n"
            f"title: {meta['title']}\n"
            f"evidence_hint: {meta['evidence_hint']}\n"
            f"recommended_fix: {meta['fix_hint']}\n"
        )
    return files


def target_asset_files(scenario: DemoScenario) -> dict[str, str]:
    return {
        "target_asset/task_brief.md": scenario.task_brief,
        "target_asset/api.yaml": "paths:\n  /upload:\n    post:\n      summary: upload file\n  /download:\n    get:\n      summary: download file\n",
        "target_asset/app.py": (
            "@app.post('/upload')\n"
            "def upload(filename, content_type, file_bytes):\n"
            "    if filename.endswith(('.png', '.jpg')):\n"
            "        save('/public/uploads/' + filename, file_bytes)\n"
            "    return {'ok': True, 'debug_path': '/public/uploads/' + filename}\n"
        ),
        "target_asset/config.yaml": "debug: true\naudit_log_retention_days: null\nSECRET_KEY: changeme\n",
    }


def _compat_attempt_output(included: list[str], attempt_name: str) -> dict[str, Any]:
    findings = []
    for index, capability_id in enumerate(included, start=1):
        meta = DEMO_CAPABILITIES[capability_id]
        findings.append(
            {
                "finding_id": f"{attempt_name}-F{index:02d}",
                "capability": meta["title"],
                "capability_id": capability_id,
                "evidence_span": meta["evidence_hint"],
                "risk_level": "high" if capability_id in {"upload_storage", "path_traversal", "weak_config"} else "medium",
                "recommended_fix": meta["fix_hint"],
            }
        )
    return {
        "attempt": attempt_name,
        "summary": "No skill baseline." if attempt_name == "A0" else f"{len(findings)} structured findings with evidence and fixes.",
        "findings": findings,
        "token_cost": 64 + len(findings) * 58,
        "latency_ms": 900 + len(findings) * 180,
    }


def _compat_verify(scenario: DemoScenario, attempt: dict[str, Any]) -> dict[str, Any]:
    observed = {item["capability_id"] for item in attempt.get("findings", [])}
    expected = set(scenario.expected_capabilities)
    missing_capabilities = sorted(expected - observed)
    evidence_ok = all(item.get("evidence_span") and item.get("recommended_fix") for item in attempt.get("findings", []))
    status = "PASS" if not missing_capabilities and evidence_ok else "FAIL"
    return {
        "status": status,
        "pass": status == "PASS",
        "feedback_type": "pass" if status == "PASS" else "missing_capability",
        "missing_capabilities": missing_capabilities,
        "scores": {
            "capability_coverage_score": round(len(observed & expected) / max(1, len(expected)), 4),
            "evidence_binding_score": 1.0 if evidence_ok else 0.0,
            "output_contract_score": 1.0 if evidence_ok else 0.0,
            "regression_safety_score": 1.0,
            "trace_observability_score": 1.0,
        },
        "evidence_fields_ok": evidence_ok,
    }


def build_run(scenario: DemoScenario, run_mode: str = "offline") -> dict[str, Any]:
    v1_included = [item for item in scenario.expected_capabilities if item not in set(scenario.v1_omits)]
    v2_included = list(scenario.expected_capabilities)
    a0_included = [item for item in scenario.expected_capabilities if item in {"sensitive_leak", "weak_config"}]
    a0 = _compat_attempt_output(a0_included, "A0")
    a1 = _compat_attempt_output(v1_included, "A1")
    a2 = _compat_attempt_output(v2_included, "A2")
    verifier0 = _compat_verify(scenario, a0)
    verifier1 = _compat_verify(scenario, a1)
    verifier2 = _compat_verify(scenario, a2)
    session_dir = RUNS_DIR / "public_demo_session"
    (session_dir / "summary").mkdir(parents=True, exist_ok=True)
    (session_dir / "attempts").mkdir(parents=True, exist_ok=True)
    (session_dir / "verifier").mkdir(parents=True, exist_ok=True)
    (session_dir / "reports").mkdir(parents=True, exist_ok=True)
    (session_dir / "artifacts").mkdir(parents=True, exist_ok=True)

    metrics = {
        "scenario": scenario.name,
        "mode": run_mode,
        "success_rate_before": round(verifier1["scores"]["capability_coverage_score"] * 100),
        "success_rate_after": round(verifier2["scores"]["capability_coverage_score"] * 100),
        "coverage_delta": round(
            verifier2["scores"]["capability_coverage_score"] - verifier1["scores"]["capability_coverage_score"], 4
        ),
        "added_findings": len(set(v2_included) - set(v1_included)),
        "token_total": 64 + len(a2["findings"]) * 58,
        "token_budget": 800,
        "status_chain": f"A0 {verifier0['status']} -> A1 {verifier1['status']} -> A2 {verifier2['status']}",
    }
    write_json_file(session_dir / "summary" / "front_metrics.json", metrics)
    write_json_file(session_dir / "attempts" / "A0_no_skill.json", a0)
    write_json_file(session_dir / "attempts" / "A1_skill_v1.json", a1)
    write_json_file(session_dir / "attempts" / "A2_skill_v2.json", a2)
    write_json_file(session_dir / "verifier" / "A1_feedback.json", verifier1)
    write_json_file(session_dir / "verifier" / "A2_feedback.json", verifier2)
    write_json_file(
        session_dir / "model_calls.json",
        [{"step": "compat_demo_run", "status": "replayed", "provider": "local deterministic", "total_tokens": 0}],
    )
    correction_report = (
        "# 后验纠错报告\n\n"
        "## 为什么 v1 没通过\n\n"
        f"Skill v1 缺少：{format_capability_list(verifier1['missing_capabilities']) or 'none'}\n\n"
        "## v2 做了什么\n\n"
        f"- 新增 failure-critical 能力：{format_capability_list(sorted(set(v2_included) - set(v1_included)))}\n"
    )
    final_report_lines = ["# 安全审查 Skill 运行报告", "", f"任务：{scenario.name}", "## 最终发现", ""]
    for finding in a2["findings"]:
        final_report_lines.extend(
            [
                f"### {finding['capability']}",
                f"- 证据：{finding['evidence_span']}",
                f"- 风险：{finding['risk_level']}",
                f"- 修复：{finding['recommended_fix']}",
                "",
            ]
        )
    (session_dir / "reports" / "correction_report.md").write_text(correction_report, encoding="utf-8", newline="\n")
    (session_dir / "reports" / "final_report.md").write_text(
        "\n".join(final_report_lines), encoding="utf-8", newline="\n"
    )
    write_json_file(
        session_dir / "artifacts" / "skill_package_v2_manifest.json",
        {
            "skill_name": f"{scenario.scenario_id}_skill",
            "version": "v2",
            "capabilities": v2_included,
            "output_contract": ["finding_id", "capability", "evidence_span", "risk_level", "recommended_fix"],
        },
    )
    return {
        "scenario": scenario,
        "pkg_v1": {"version": "v1", "included_capabilities": v1_included, "omitted_capabilities": list(scenario.v1_omits)},
        "pkg_v2": {"version": "v2", "included_capabilities": v2_included, "omitted_capabilities": []},
        "a0": a0,
        "a1": a1,
        "a2": a2,
        "verifier0": verifier0,
        "verifier1": verifier1,
        "verifier2": verifier2,
        "metrics": metrics,
        "session_dir": str(session_dir),
        "report_paths": {
            "front_metrics": str(session_dir / "summary" / "front_metrics.json"),
            "correction_report": str(session_dir / "reports" / "correction_report.md"),
            "final_report": str(session_dir / "reports" / "final_report.md"),
            "manifest": str(session_dir / "artifacts" / "skill_package_v2_manifest.json"),
        },
    }


def run_custom_material_loop(task_text: str) -> dict[str, Any]:
    CUSTOM_RUN_DIR.mkdir(parents=True, exist_ok=True)
    task_file = CUSTOM_RUN_DIR / "inputs" / "task.md"
    task_file.parent.mkdir(parents=True, exist_ok=True)
    task_file.write_text(task_text, encoding="utf-8", newline="\n")
    command = [
        sys.executable,
        str(ROOT / "scripts" / "run_generic_agent_loop.py"),
        "--task-file",
        str(task_file),
        "--output-dir",
        str(CUSTOM_RUN_DIR),
    ]
    completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=420)
    summary = read_json(CUSTOM_RUN_DIR / "run_summary.json")
    if not isinstance(summary, dict):
        summary = {
            "run_id": CUSTOM_RUN_DIR.name,
            "passed": False,
            "mode": "failed_before_summary",
        }
    summary["process"] = {
        "returncode": completed.returncode,
        "stdout_tail": completed.stdout[-3000:],
        "stderr_tail": completed.stderr[-3000:],
    }
    return summary


def normalize_custom_bundle(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    if "summary" in value:
        return value
    if "run_id" in value:
        loaded = load_custom_bundle()
        if loaded:
            loaded["summary"].setdefault("process", value.get("process", {}))
            return loaded
        return {"summary": value}
    return None


def load_custom_bundle() -> dict[str, Any] | None:
    summary = read_json(CUSTOM_RUN_DIR / "run_summary.json")
    if not isinstance(summary, dict):
        return None
    return {
        "summary": summary,
        "task": read_text(CUSTOM_RUN_DIR / "inputs" / "task.md") if (CUSTOM_RUN_DIR / "inputs" / "task.md").exists() else "",
        "skill_v1": read_text(CUSTOM_RUN_DIR / "skills" / "skill_v1.md") if (CUSTOM_RUN_DIR / "skills" / "skill_v1.md").exists() else "",
        "skill_v2": read_text(CUSTOM_RUN_DIR / "skills" / "skill_v2.md") if (CUSTOM_RUN_DIR / "skills" / "skill_v2.md").exists() else "",
        "a0": read_json(CUSTOM_RUN_DIR / "attempts" / "A0_no_skill.json") or {},
        "a1": read_json(CUSTOM_RUN_DIR / "attempts" / "A1_skill_v1.json") or {},
        "a2": read_json(CUSTOM_RUN_DIR / "attempts" / "A2_skill_v2.json") or {},
        "a1_feedback": read_json(CUSTOM_RUN_DIR / "verifier" / "A1_feedback.json") or {},
        "a2_feedback": read_json(CUSTOM_RUN_DIR / "verifier" / "A2_feedback.json") or {},
        "patch_plan": read_json(CUSTOM_RUN_DIR / "revision" / "patch_plan.json") or {},
        "model_calls": read_json(CUSTOM_RUN_DIR / "model_calls.json") or [],
    }


def init_state() -> None:
    st.session_state.setdefault("entry_mode", "verified")
    st.session_state.setdefault("selected_case_id", load_task_cases()[0].case_id if load_task_cases() else "")
    st.session_state.setdefault("custom_task_text", CUSTOM_HINT)
    st.session_state.setdefault("custom_run", load_custom_bundle())


def render_header() -> None:
    st.title("专家知识蒸馏与 Skill 优化 Demo")
    st.markdown(
        "这个 Demo 不主打“规则表有多长”，而主打一件更容易让人判断价值的事："
        "**给定专家材料和目标任务，系统能不能生成 Skill，执行后发现缺口，再把 Skill 修好。**"
    )
    st.markdown(
        """
        <span class="pill">结果优先</span>
        <span class="pill">artifact-backed</span>
        <span class="pill">typed posterior repair</span>
        <span class="pill">deterministic verifier/gate</span>
        <span class="pill">controlled evidence, not universal scanning</span>
        """,
        unsafe_allow_html=True,
    )


def render_entry_selector() -> tuple[str, TaskCase | None]:
    st.markdown("### 入口")
    entry_mode = st.radio(
        "选择展示入口",
        options=["verified", "custom"],
        horizontal=True,
        label_visibility="collapsed",
        format_func=lambda value: "已验证任务" if value == "verified" else "从自定义材料构建",
    )
    st.session_state.entry_mode = entry_mode

    if entry_mode == "verified":
        cases = load_task_cases()
        case_options = {case.case_id: f"{case.title} | {family_label(case.task_family)}" for case in cases}
        selected_case_id = st.selectbox(
            "选择任务",
            options=[case.case_id for case in cases],
            index=max(0, [case.case_id for case in cases].index(st.session_state.selected_case_id))
            if st.session_state.selected_case_id in case_options
            else 0,
            format_func=lambda value: case_options[value],
        )
        st.session_state.selected_case_id = selected_case_id
        selected_case = next(case for case in cases if case.case_id == selected_case_id)
        info_cols = st.columns(4)
        info_cols[0].metric("任务家族", family_label(selected_case.task_family))
        info_cols[1].metric("v1 初始能力", len(selected_case.v1_capabilities))
        info_cols[2].metric("期望能力", len(selected_case.expected_capabilities))
        info_cols[3].metric("典型修正", selected_case.typical_repair)
        return entry_mode, selected_case

    with st.container(border=True):
        st.markdown("**自定义模式的定位**")
        st.write(
            "这是一个受控编译入口，不是任意输入都能严格验证的通用漏洞扫描器。"
            "系统会从你提供的任务目标、专家材料和目标资产中抽取候选能力点，"
            "再用本地确定性 verifier/gate 检查执行前后是否真的变好。"
        )
        st.session_state.custom_task_text = st.text_area(
            "任务目标 + 专家材料 + 目标资产",
            value=st.session_state.custom_task_text,
            height=260,
        )
        control_cols = st.columns([1, 1, 2])
        if control_cols[0].button("运行自定义闭环", type="primary", use_container_width=True):
            with st.status("正在运行本地 live loop", expanded=True) as status:
                st.write("1. 写入用户材料")
                st.write("2. 生成 Skill v1")
                st.write("3. 执行 A1 并读取 verifier feedback")
                st.write("4. 生成 Skill v2 并重跑 A2")
                try:
                    run_custom_material_loop(st.session_state.custom_task_text)
                    st.session_state.custom_run = load_custom_bundle()
                    status.update(label="自定义闭环完成", state="complete", expanded=False)
                except subprocess.TimeoutExpired:
                    st.session_state.custom_run = None
                    status.update(label="自定义闭环超时", state="error", expanded=False)
        if control_cols[1].button("恢复示例输入", use_container_width=True):
            st.session_state.custom_task_text = CUSTOM_HINT
            st.rerun()
        ready = all(os.environ.get(name) for name in ("OPENAI_BASE_URL", "OPENAI_API_KEY", "MODEL"))
        control_cols[2].caption(
            "若配置了 OPENAI_BASE_URL / OPENAI_API_KEY / MODEL，会实际调用 LLM。"
            "未配置时会诚实退回本地 fallback，并记录为 not_configured。"
            + (" 当前环境已配置。" if ready else " 当前环境未配置。")
        )
    return entry_mode, None


def render_verified_overview(bundle: dict[str, Any], backend: dict[str, Any]) -> None:
    case: TaskCase = bundle["case"]
    summary = bundle.get("summary_item", {})
    metrics = bundle.get("metrics", {})
    a1_report = bundle.get("a1_report", {})
    a2_report = bundle.get("a2_report", {})
    changed = changed_capabilities(bundle)

    st.markdown("### 结果先看")
    cols = st.columns(5)
    cols[0].metric("任务是否解决", "PASS" if a2_report.get("pass") else "FAIL", "A2")
    cols[1].metric("A1 -> A2 覆盖", f"{summary.get('scores_before', {}).get('capability_coverage_score', 0):.2f}", f"{summary.get('scores_after', {}).get('capability_coverage_score', 0):.2f}")
    cols[2].metric("反馈类型", a1_report.get("feedback_type", "-"))
    cols[3].metric("修正动作", summary.get("repair_action", "-"))
    cols[4].metric("新增能力", len(changed), format_capability_list(changed) if changed else "none")

    row_left, row_right = st.columns([1.1, 1])
    with row_left:
        st.markdown("#### 这件事对用户意味着什么")
        st.markdown(
            f"- 当前任务：`{case.title}`\n"
            f"- 用户关心：{FAMILY_META.get(case.task_family, {}).get('user_goal', '把任务做对')}\n"
            f"- 用户提供：{FAMILY_META.get(case.task_family, {}).get('user_input', '专家材料 + 目标资产')}\n"
            f"- 系统输出：Skill v1 / A1 反馈 / Skill v2 / A2 结果 / 可导出 artifact"
        )
    with row_right:
        st.markdown("#### 为什么 v2 不是“写死答案”")
        st.markdown(
            f"- A1 失败类型：`{a1_report.get('feedback_type', '-')}`\n"
            f"- 缺失或问题：`{format_capability_list(a1_report.get('missing_capabilities', []))}`\n"
            f"- repair policy：`{summary.get('repair_action', '-')}`\n"
            f"- gate 决策：`{summary.get('gate_decision', '-')}`\n"
            f"- A2 是否通过：`{'yes' if a2_report.get('pass') else 'no'}`"
        )

    st.markdown("#### 一屏黄金路径")
    golden_rows = [
        {"阶段": "用户输入", "看到的内容": "专家材料 + 目标资产 + 任务规格", "系统动作": "构造 task case"},
        {"阶段": "Skill v1", "看到的内容": format_capability_list(bundle.get("manifest_v1", {}).get("capabilities", [])), "系统动作": "先部署一个紧凑版本"},
        {"阶段": "A1 反馈", "看到的内容": a1_report.get("feedback_type", "-"), "系统动作": "verifier 指出缺口"},
        {"阶段": "Skill v2", "看到的内容": format_capability_list(bundle.get("manifest_v2", {}).get("capabilities", [])), "系统动作": "typed repair + gate"},
        {"阶段": "A2 结果", "看到的内容": "PASS" if a2_report.get("pass") else "FAIL", "系统动作": "重跑并验证"},
    ]
    st.dataframe(golden_rows, use_container_width=True, hide_index=True)

    added_rows = build_added_finding_rows(bundle)
    st.markdown("#### A2 比 A1 多了什么")
    if added_rows:
        st.dataframe(added_rows, use_container_width=True, hide_index=True)
    else:
        st.info("当前选择的任务不是通过新增 capability 提升，而是通过边界/契约修正提升。")

    if case.case_id == "upload_security_001" and backend.get("harbor_upload_loop"):
        harbor_loop = backend["harbor_upload_loop"]
        st.markdown("#### Harbor 真实执行证据")
        harbor_cols = st.columns(4)
        harbor_cols[0].metric("Harbor A1", "PASS" if harbor_loop["A1"]["pass"] else "FAIL", f"reward {harbor_loop['A1']['reward']}")
        harbor_cols[1].metric("Harbor A2", "PASS" if harbor_loop["A2"]["pass"] else "FAIL", f"reward {harbor_loop['A2']['reward']}")
        harbor_cols[2].metric("A1 技能", len(harbor_loop["revision"]["before_capabilities"]), format_capability_list(harbor_loop["revision"]["before_capabilities"]))
        harbor_cols[3].metric("A2 技能", len(harbor_loop["revision"]["after_capabilities"]), format_capability_list(harbor_loop["revision"]["after_capabilities"]))
        st.caption(harbor_loop.get("boundary", ""))

    if case.case_id == "config_security_001" and backend.get("harbor_config_loop"):
        harbor_loop = backend["harbor_config_loop"]
        st.markdown("#### 第二个 Harbor 任务证明")
        harbor_cols = st.columns(4)
        harbor_cols[0].metric("Harbor A1", "PASS" if harbor_loop["A1"]["pass"] else "FAIL", harbor_loop["A1"]["feedback_type"])
        harbor_cols[1].metric("Harbor A2", "PASS" if harbor_loop["A2"]["pass"] else "FAIL", f"reward {harbor_loop['A2']['reward']}")
        harbor_cols[2].metric("修正类型", harbor_loop["revision"]["repair_action"])
        harbor_cols[3].metric("Schema 错误", len(harbor_loop["A1"].get("schema_errors", [])))
        st.caption(harbor_loop.get("boundary", ""))


def render_custom_overview(custom_bundle: dict[str, Any]) -> None:
    summary = custom_bundle.get("summary", {})
    if not isinstance(summary, dict):
        summary = {}
    a1_feedback = custom_bundle.get("a1_feedback", {})
    a2_feedback = custom_bundle.get("a2_feedback", {})

    st.markdown("### 结果先看")
    cols = st.columns(5)
    cols[0].metric("任务是否解决", "PASS" if summary.get("passed") else "FAIL", summary.get("status_chain", "-"))
    cols[1].metric("A1 分数", a1_feedback.get("score", 0.0))
    cols[2].metric("A2 分数", a2_feedback.get("score", 0.0), f"+{round(a2_feedback.get('score', 0.0) - a1_feedback.get('score', 0.0), 3)}")
    cols[3].metric("运行模式", summary.get("mode", "-"))
    cols[4].metric("模型", summary.get("model") or "not configured")

    st.markdown("#### 这个入口的边界")
    st.info(
        "这是一个受控的自定义材料编译入口。LLM 负责 distill/execute，"
        "verifier 负责看输出结构、证据项和改进项是否变得更完整。"
        "它展示的是“在线生成并优化”的感觉，不是任意任务严格安全验证。"
    )

    compare_rows = [
        {"阶段": "A0 无 Skill", "answer": custom_bundle.get("a0", {}).get("answer", ""), "通过": "-"},
        {"阶段": "A1 Skill v1", "answer": custom_bundle.get("a1", {}).get("answer", ""), "通过": a1_feedback.get("passed", False)},
        {"阶段": "A2 Skill v2", "answer": custom_bundle.get("a2", {}).get("answer", ""), "通过": a2_feedback.get("passed", False)},
    ]
    st.dataframe(compare_rows, use_container_width=True, hide_index=True)

    st.markdown("#### A1 为什么没过")
    missing = a1_feedback.get("missing", [])
    if missing:
        st.write("\n".join(f"- {item}" for item in missing))
    else:
        st.write("- 没有记录到缺口。")

    st.markdown("#### patch plan")
    st.json(custom_bundle.get("patch_plan", {}))


def render_inputs_tab(bundle: dict[str, Any], entry_mode: str) -> None:
    st.markdown("#### 哪些是用户给的，哪些是系统生成的")
    left, right = st.columns(2)
    if entry_mode == "verified":
        with left:
            st.markdown("**用户给定 / 数据集定义**")
            st.markdown(
                "- 专家材料\n"
                "- 目标资产\n"
                "- 任务规格与 verifier contract\n"
                "- 期望 capability 集合"
            )
        with right:
            st.markdown("**系统运行后生成**")
            st.markdown(
                "- Skill v1 / Skill v2\n"
                "- A0 / A1 / A2 agent outputs\n"
                "- verifier reports\n"
                "- repair decision / gate decision\n"
                "- provenance / trace / export package"
            )
        st.markdown("#### 任务输入")
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**专家材料**")
            st.code(bundle.get("expert_material", "")[:6000], language="markdown")
        with col_b:
            st.markdown("**目标资产**")
            st.code(bundle.get("target_asset", "")[:6000], language="markdown")
        if bundle.get("task_spec"):
            with st.expander("查看 task_spec/task_spec.json", expanded=False):
                st.json(bundle["task_spec"])
    else:
        st.markdown("**用户输入**")
        st.code(bundle.get("task", ""), language="markdown")
        st.caption("这个入口不会假装自己知道开放世界标准答案，它只把你的材料编译成可执行 Skill，再让 verifier 检查输出是否更完整。")


def render_skill_revision_tab(bundle: dict[str, Any], entry_mode: str) -> None:
    st.markdown("#### Skill 修正链")
    if entry_mode == "verified":
        left, right = st.columns(2)
        with left:
            st.markdown("**Skill v1**")
            st.write(format_capability_list(bundle.get("manifest_v1", {}).get("capabilities", [])))
            st.code(bundle.get("skill_v1", "")[:6000], language="markdown")
        with right:
            st.markdown("**Skill v2**")
            st.write(format_capability_list(bundle.get("manifest_v2", {}).get("capabilities", [])))
            st.code(bundle.get("skill_v2", "")[:6000], language="markdown")

        repair_cols = st.columns(3)
        repair_cols[0].metric("反馈类型", bundle.get("a1_report", {}).get("feedback_type", "-"))
        repair_cols[1].metric("repair action", bundle.get("summary_item", {}).get("repair_action", "-"))
        repair_cols[2].metric("gate", bundle.get("summary_item", {}).get("gate_decision", "-"))

        st.markdown("#### 来源映射")
        mapping_rows = []
        for row in bundle.get("source_mapping", []):
            mapping_rows.append(
                {
                    "来源文件": row.get("source", ""),
                    "候选能力": capability_label(row.get("capability_id", "")),
                    "进入 Skill": row.get("skill_file", ""),
                }
            )
        if mapping_rows:
            st.dataframe(mapping_rows, use_container_width=True, hide_index=True)

        st.markdown("#### 我们真正要讲的创新点")
        innovation_rows = [
            {
                "点": "typed posterior repair",
                "解释": "不是泛泛说失败了，而是把 failure type 映射成不同修正动作。",
            },
            {
                "点": "promotion gate",
                "解释": "不是 patch 了就升版，必须过 gate 才进入 Skill v2。",
            },
            {
                "点": "artifact-backed trace",
                "解释": "来源、反馈、修正、结果都能点到底，而不是只给一张解释图。",
            },
        ]
        st.dataframe(innovation_rows, use_container_width=True, hide_index=True)
    else:
        left, right = st.columns(2)
        with left:
            st.markdown("**Skill v1**")
            st.code(bundle.get("skill_v1", "")[:6000], language="markdown")
        with right:
            st.markdown("**Skill v2**")
            st.code(bundle.get("skill_v2", "")[:6000], language="markdown")

        st.markdown("#### verifier -> repair")
        st.json(bundle.get("a1_feedback", {}))
        st.json(bundle.get("patch_plan", {}))


def render_execution_tab(bundle: dict[str, Any], entry_mode: str) -> None:
    st.markdown("#### 执行与证据")
    if entry_mode == "verified":
        attempt_rows = [
            {
                "阶段": "A0",
                "pass": bundle.get("a0_report", {}).get("pass"),
                "feedback": bundle.get("a0_report", {}).get("feedback_type"),
                "coverage": bundle.get("a0_report", {}).get("scores", {}).get("capability_coverage_score"),
            },
            {
                "阶段": "A1",
                "pass": bundle.get("a1_report", {}).get("pass"),
                "feedback": bundle.get("a1_report", {}).get("feedback_type"),
                "coverage": bundle.get("a1_report", {}).get("scores", {}).get("capability_coverage_score"),
            },
            {
                "阶段": "A2",
                "pass": bundle.get("a2_report", {}).get("pass"),
                "feedback": bundle.get("a2_report", {}).get("feedback_type"),
                "coverage": bundle.get("a2_report", {}).get("scores", {}).get("capability_coverage_score"),
            },
        ]
        st.dataframe(attempt_rows, use_container_width=True, hide_index=True)

        artifact_rows = collect_artifacts(bundle["run_dir"])
        st.markdown("#### 文件产物与元信息")
        st.dataframe(artifact_rows, use_container_width=True, hide_index=True)
        preview_choice = st.selectbox("预览文件", options=[row["path"] for row in artifact_rows], key=f"artifact_preview_{bundle['case'].case_id}")
        preview_meta = artifact_metadata(preview_choice)
        meta_cols = st.columns(4)
        meta_cols[0].metric("Generated by", preview_meta["generated_by"])
        meta_cols[1].metric("Depends on", preview_meta["depends_on"])
        meta_cols[2].metric("Used by", preview_meta["used_by"])
        meta_cols[3].metric("Purpose", preview_meta["purpose"])
        preview_file(bundle["run_dir"] / preview_choice)
    else:
        summary = bundle["summary"]
        cols = st.columns(4)
        cols[0].metric("env_ready", "yes" if summary.get("env_ready") else "no")
        cols[1].metric("A1", bundle.get("a1_feedback", {}).get("score", 0.0))
        cols[2].metric("A2", bundle.get("a2_feedback", {}).get("score", 0.0))
        cols[3].metric("return code", summary.get("process", {}).get("returncode", "-"))
        if bundle.get("model_calls"):
            st.markdown("#### model calls")
            st.json(bundle["model_calls"])
        artifact_rows = collect_artifacts(CUSTOM_RUN_DIR)
        if artifact_rows:
            st.markdown("#### 文件产物与元信息")
            st.dataframe(artifact_rows, use_container_width=True, hide_index=True)
            preview_choice = st.selectbox("预览文件", options=[row["path"] for row in artifact_rows], key="custom_artifact_preview")
            preview_meta = artifact_metadata(preview_choice)
            meta_cols = st.columns(4)
            meta_cols[0].metric("Generated by", preview_meta["generated_by"])
            meta_cols[1].metric("Depends on", preview_meta["depends_on"])
            meta_cols[2].metric("Used by", preview_meta["used_by"])
            meta_cols[3].metric("Purpose", preview_meta["purpose"])
            preview_file(CUSTOM_RUN_DIR / preview_choice)


def render_validation_tab(generalization: dict[str, Any], backend: dict[str, Any]) -> None:
    st.markdown("#### 跨任务证据")
    cols = st.columns(4)
    cols[0].metric("任务家族", generalization.get("scenario_count", 0))
    cols[1].metric("A2 通过", f"{generalization.get('a2_pass_count', 0)}/{generalization.get('scenario_count', 0)}")
    cols[2].metric("反馈类型", len(generalization.get("feedback_types", [])))
    cols[3].metric("修正动作", len(generalization.get("repair_actions", [])))

    suite_rows = []
    for row in generalization.get("results", []):
        suite_rows.append(
            {
                "场景": row["scenario"],
                "任务家族": row["family"],
                "A1 反馈": row["feedback_type"],
                "修正动作": row["repair_action"],
                "A2": "PASS" if row["a2_pass"] else "FAIL",
                "artifact_dir": row["artifact_dir"],
            }
        )
    st.dataframe(suite_rows, use_container_width=True, hide_index=True)

    st.markdown("#### Negative controls")
    negative_rows = []
    for row in backend.get("negative_controls", {}).get("cases", []):
        negative_rows.append(
            {
                "case": row.get("case_id"),
                "purpose": row.get("purpose"),
                "expected": row.get("expected_outcome"),
                "passed": row.get("control_passed"),
            }
        )
    if negative_rows:
        st.dataframe(negative_rows, use_container_width=True, hide_index=True)

    repeatability = backend.get("repeatability", {})
    if repeatability:
        st.markdown("#### Harbor LLM repeatability smoke")
        repeat_cols = st.columns(4)
        repeat_cols[0].metric("run_count", repeatability.get("run_count", 0))
        repeat_cols[1].metric("A1 全失败", "yes" if repeatability.get("a1_all_fail") else "no")
        repeat_cols[2].metric("A2 全通过", "yes" if repeatability.get("a2_all_pass") else "no")
        repeat_cols[3].metric("failure stable", "yes" if repeatability.get("failure_reason_stable") else "no")
        run_rows = []
        for row in repeatability.get("runs", []):
            run_rows.append(
                {
                    "label": row["label"],
                    "A1 reward": row["a1_reward"],
                    "A2 reward": row["a2_reward"],
                    "A1 tokens": (row.get("a1_usage") or {}).get("total_tokens"),
                    "A2 tokens": (row.get("a2_usage") or {}).get("total_tokens"),
                    "latency_ms": ((row.get("a1_usage") or {}).get("latency_ms", 0) + (row.get("a2_usage") or {}).get("latency_ms", 0)),
                }
            )
        st.dataframe(run_rows, use_container_width=True, hide_index=True)


def render_boundary_tab(backend: dict[str, Any]) -> None:
    st.markdown("#### 借鉴边界与我们自己的东西")
    relation_rows = [
        {
            "来源": "SPARK-PDI",
            "借鉴": "posterior evidence over prior plans",
            "我们现在落地": "执行后 verifier feedback 驱动 typed repair",
            "还没做到": "完整 trajectory 级 PDI 与大规模环境评测",
        },
        {
            "来源": "COLLEAGUE.SKILL",
            "借鉴": "inspectable / versioned / correctable skill artifact",
            "我们现在落地": "Skill v1/v2、manifest、gate、artifact export",
            "还没做到": "通用 skill marketplace 与多 host 安装面",
        },
        {
            "来源": "我们自己的收束",
            "借鉴": "-",
            "我们现在落地": "typed posterior revision over deployable expert-skill packages",
            "还没做到": "开放世界多领域泛化证明",
        },
    ]
    st.dataframe(relation_rows, use_container_width=True, hide_index=True)

    st.markdown("#### 安全说法")
    safe_claims = [
        "这是一个受控的专家知识蒸馏与 Skill 修正原型。",
        "它已经证明同一套 pipeline 能跨 4 个任务家族工作。",
        "它已经证明不同任务会触发不同 feedback，并进入不同 repair action。",
        "它已经有 local live LLM 与 Harbor live LLM 的受控闭环证据。",
    ]
    unsafe_claims = [
        "它不是通用漏洞扫描器。",
        "它不是完整 SPARK-PDI 复现。",
        "它不证明任意专家材料都能自动蒸馏。",
        "它不证明开放世界真实漏洞发现。",
    ]
    left, right = st.columns(2)
    with left:
        st.success("\n".join(f"- {item}" for item in safe_claims))
    with right:
        st.warning("\n".join(f"- {item}" for item in unsafe_claims))

    if CLAIM_BOUNDARY_PATH.exists():
        with st.expander("查看完整 claim boundary", expanded=False):
            st.code(read_text(CLAIM_BOUNDARY_PATH), language="markdown")

    st.markdown("#### 导出入口")
    export_cols = st.columns(3)
    if REVIEW_PACKAGE_ZIP.exists():
        export_cols[0].download_button(
            "下载 review package",
            data=REVIEW_PACKAGE_ZIP.read_bytes(),
            file_name=REVIEW_PACKAGE_ZIP.name,
            mime="application/zip",
            use_container_width=True,
        )
    if MORNING_STATUS_PATH.exists():
        export_cols[1].download_button(
            "下载 morning status",
            data=read_text(MORNING_STATUS_PATH),
            file_name=MORNING_STATUS_PATH.name,
            mime="text/markdown",
            use_container_width=True,
        )
    if BACKEND_STATUS_PATH.exists():
        export_cols[2].download_button(
            "下载 backend maturity",
            data=read_text(BACKEND_STATUS_PATH),
            file_name=BACKEND_STATUS_PATH.name,
            mime="text/markdown",
            use_container_width=True,
        )
    if MATURITY_PLAN_PATH.exists():
        st.markdown("#### 成熟化补差计划")
        st.download_button(
            "下载 maturity gap closure plan",
            data=read_text(MATURITY_PLAN_PATH),
            file_name=MATURITY_PLAN_PATH.name,
            mime="text/markdown",
            use_container_width=True,
        )


def main() -> None:
    st.set_page_config(page_title="专家知识蒸馏与 Skill 优化 Demo", layout="wide")
    render_css()
    init_state()

    backend = load_backend_evidence()
    generalization = load_generalization_summary()

    render_header()
    entry_mode, selected_case = render_entry_selector()

    if entry_mode == "verified" and selected_case is not None:
        bundle = load_case_bundle(selected_case.case_id)
        render_verified_overview(bundle, backend)
        tab_inputs, tab_skill, tab_execution, tab_validation, tab_boundary = st.tabs(
            ["输入与对象", "Skill 修正", "执行与证据", "跨任务验证", "边界与导出"]
        )
        with tab_inputs:
            render_inputs_tab(bundle, entry_mode)
        with tab_skill:
            render_skill_revision_tab(bundle, entry_mode)
        with tab_execution:
            render_execution_tab(bundle, entry_mode)
        with tab_validation:
            render_validation_tab(generalization, backend)
        with tab_boundary:
            render_boundary_tab(backend)
        return

    custom_bundle = normalize_custom_bundle(st.session_state.get("custom_run")) or load_custom_bundle()
    if custom_bundle:
        render_custom_overview(custom_bundle)
        tab_inputs, tab_skill, tab_execution, tab_validation, tab_boundary = st.tabs(
            ["输入与对象", "Skill 修正", "执行与证据", "跨任务验证", "边界与导出"]
        )
        with tab_inputs:
            render_inputs_tab(custom_bundle, entry_mode)
        with tab_skill:
            render_skill_revision_tab(custom_bundle, entry_mode)
        with tab_execution:
            render_execution_tab(custom_bundle, entry_mode)
        with tab_validation:
            render_validation_tab(generalization, backend)
        with tab_boundary:
            render_boundary_tab(backend)
    else:
        st.info("还没有自定义运行记录。点击“运行自定义闭环”后，这里会显示 Skill v1 -> A1 feedback -> Skill v2 -> A2 的完整过程。")


if __name__ == "__main__":
    main()
