from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from agents.non_oracle_local_security_agent import run_agent
from skill_deployment.verifier import verify_controlled_execution


OUT_DIR = ROOT / "outputs" / "validation" / "agent_level_metamorphic_stress_001"
JSON_OUT = OUT_DIR / "summary.json"
MD_OUT = ROOT / "reports" / "AGENT_LEVEL_METAMORPHIC_STRESS_STATUS.md"


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def make_case(case_id: str, capabilities: tuple[str, ...], target_text: str) -> tuple[Path, Path]:
    case_root = OUT_DIR / "cases" / case_id
    skill_dir = case_root / "skill"
    target_dir = case_root / "target"
    skill_dir.mkdir(parents=True, exist_ok=True)
    target_dir.mkdir(parents=True, exist_ok=True)
    write_json(skill_dir / "manifest.json", {"skill_id": case_id, "version": "metamorphic", "capabilities": list(capabilities)})
    write_text(target_dir / "target.md", target_text)
    return skill_dir, target_dir


def run_one(
    *,
    case_id: str,
    scenario: str,
    transform: str,
    expected_relation: str,
    capabilities: tuple[str, ...],
    expected_capabilities: tuple[str, ...],
    target_text: str,
    expected_pass: bool,
) -> dict[str, Any]:
    skill_dir, target_dir = make_case(case_id, capabilities, target_text)
    agent_dir = OUT_DIR / "cases" / case_id / "agent"
    output = run_agent(skill_dir, target_dir, agent_dir)
    report = verify_controlled_execution(expected_capabilities, output, target_text=target_text).to_dict()
    return {
        "case_id": case_id,
        "scenario": scenario,
        "transform": transform,
        "expected_relation": expected_relation,
        "expected_pass": expected_pass,
        "actual_pass": report["pass"],
        "control_passed": bool(report["pass"]) == expected_pass,
        "finding_count": len(output.get("findings", [])),
        "feedback_type": report["feedback_type"],
        "agent_output": str(agent_dir / "agent_output.json"),
        "trace": str(agent_dir / "trace.jsonl"),
        "verifier_report": report,
    }


def build_cases() -> list[dict[str, Any]]:
    return [
        run_one(
            case_id="agent_upload_clean_target",
            scenario="upload_security",
            transform="clean target removes upload weaknesses",
            expected_relation="Agent should emit no upload findings on the clean transformed target.",
            capabilities=("UPLOAD_TYPE_MAGIC", "UPLOAD_PATH_ISOLATION", "UPLOAD_AUDIT_RETENTION"),
            expected_capabilities=(),
            target_text="app.py: upload() validates MIME type and file signature, stores a generated UUID name outside public roots, and returns only file_id. config.yaml: audit_log_retention_days=90.",
            expected_pass=True,
        ),
        run_one(
            case_id="agent_config_clean_target",
            scenario="config_security",
            transform="clean production config",
            expected_relation="Agent should emit no config findings on the clean production config.",
            capabilities=("CONFIG_AUDIT_EXPORT", "CONFIG_ENV_GUARD"),
            expected_capabilities=(),
            target_text="prod.audit.enabled=true retention_days=90 export_sink=s3://audit-logs. prod.debug=false. prod.api_token is loaded from ENV.",
            expected_pass=True,
        ),
        run_one(
            case_id="agent_data_quality_row_shuffle",
            scenario="data_quality",
            transform="row/order presentation shuffle",
            expected_relation="Agent should still find the three data-quality issues after row order changes.",
            capabilities=("DATA_REQUIRED_FIELD_COVERAGE", "DATA_TEMPORAL_SPLIT_GUARD", "DATA_LABEL_ENUM_ALIGNMENT"),
            expected_capabilities=("DATA_REQUIRED_FIELD_COVERAGE", "DATA_TEMPORAL_SPLIT_GUARD", "DATA_LABEL_ENUM_ALIGNMENT"),
            target_text="\n".join(
                [
                    "validation.csv sample:",
                    "- row 120: user_id=556, event_date=2025-05-05, country_code=CN, label=premium",
                    "train.csv sample:",
                    "- row 9811: user_id=112, event_date=2025-05-04, country_code=US, label=gold_plus",
                    "- row 1042: user_id=991, event_date=2025-04-11, country_code=, label=basic",
                    "dataset_contract.yaml: required_fields=[user_id,event_date,country_code,label]; allowed_labels=[basic,premium,enterprise]; validation_cutoff=2025-04-30.",
                ]
            ),
            expected_pass=True,
        ),
        run_one(
            case_id="agent_api_injected_risk",
            scenario="api_review",
            transform="inject overbroad endpoint risk",
            expected_relation="Agent should emit API schema and overbroad-risk findings when target evidence exists.",
            capabilities=("API_SCHEMA_CONTRACT", "API_OVERBROAD_RISK"),
            expected_capabilities=("API_SCHEMA_CONTRACT", "API_OVERBROAD_RISK"),
            target_text="OpenAPI GET /users accepts user_id without role check and returns debug_path. The report must include evidence_span.",
            expected_pass=True,
        ),
    ]


def render(payload: dict[str, Any]) -> str:
    lines = [
        "# Agent-Level Metamorphic Stress Status",
        "",
        f"Overall pass: `{payload['overall_pass']}`",
        "",
        "This is agent-level because the local non-oracle semantic agent reads the transformed target and Skill manifest, emits findings, and then the verifier checks the metamorphic relation. It is still deterministic and not a live LLM stress test.",
        "",
        "A failed relation is retained as useful evidence: it marks a skill-to-agent or detector-to-evidence limitation that should constrain promotion scope.",
        "",
        "| Case | Scenario | Transform | Findings | Feedback | Control passed |",
        "|---|---|---|---:|---|---|",
    ]
    for row in payload["cases"]:
        lines.append(f"| {row['case_id']} | {row['scenario']} | {row['transform']} | {row['finding_count']} | {row['feedback_type']} | {row['control_passed']} |")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    cases = build_cases()
    payload = {
        "run_id": "agent_level_metamorphic_stress_001",
        "backend": "non_oracle_local_semantic_agent",
        "case_count": len(cases),
        "overall_pass": all(case["control_passed"] for case in cases),
        "boundary": "Agent-level deterministic stress; not live LLM or Harbor metamorphic evidence. Failures are retained as behavior-limit evidence rather than hidden.",
        "cases": cases,
    }
    write_json(JSON_OUT, payload)
    write_text(MD_OUT, render(payload))
    print(json.dumps({"json": str(JSON_OUT), "report": str(MD_OUT), "overall_pass": payload["overall_pass"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
