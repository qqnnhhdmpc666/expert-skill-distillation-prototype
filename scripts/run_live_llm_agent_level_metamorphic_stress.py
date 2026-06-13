from __future__ import annotations

import json
import os
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

from agents.llm_security_agent import run_agent
from skill_deployment.verifier import summarize_verifier_report, verify_controlled_execution


OUT_DIR = ROOT / "outputs" / "validation" / "live_llm_agent_level_metamorphic_stress_001"
JSON_OUT = OUT_DIR / "summary.json"
MD_OUT = ROOT / "reports" / "LIVE_LLM_AGENT_LEVEL_METAMORPHIC_STRESS_STATUS.md"


CAPABILITIES = (
    "DATA_REQUIRED_FIELD_COVERAGE",
    "DATA_TEMPORAL_SPLIT_GUARD",
    "DATA_LABEL_ENUM_ALIGNMENT",
)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def target_text() -> str:
    return "\n".join(
        [
            "validation.csv sample:",
            "- row 120: user_id=556, event_date=2025-05-05, country_code=CN, label=premium",
            "train.csv sample:",
            "- row 9811: user_id=112, event_date=2025-05-04, country_code=US, label=gold_plus",
            "- row 1042: user_id=991, event_date=2025-04-11, country_code=, label=basic",
            "dataset_contract.yaml: required_fields=[user_id,event_date,country_code,label]; allowed_labels=[basic,premium,enterprise]; validation_cutoff=2025-04-30.",
        ]
    )


def prepare() -> tuple[Path, Path, Path]:
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    skill_dir = OUT_DIR / "skill"
    target_dir = OUT_DIR / "target"
    agent_dir = OUT_DIR / "agent"
    skill_dir.mkdir(parents=True)
    target_dir.mkdir(parents=True)
    write_json(
        skill_dir / "manifest.json",
        {
            "skill_id": "live_llm_data_quality_row_shuffle_metamorphic",
            "version": "metamorphic",
            "capabilities": list(CAPABILITIES),
        },
    )
    write_text(
        skill_dir / "SKILL.md",
        "\n".join(
            [
                "# Data Quality Review Skill",
                "",
                "Return one finding per grounded capability.",
                "Use only capability IDs from the manifest.",
                "Every finding must include capability_id, evidence_span, and recommended_fix.",
                "",
                "- DATA_REQUIRED_FIELD_COVERAGE: check required fields such as country_code.",
                "- DATA_TEMPORAL_SPLIT_GUARD: check dates against validation_cutoff.",
                "- DATA_LABEL_ENUM_ALIGNMENT: check labels against allowed_labels.",
                "",
            ]
        ),
    )
    write_text(target_dir / "target.md", target_text())
    return skill_dir, target_dir, agent_dir


def render(payload: dict[str, Any]) -> str:
    lines = [
        "# Live LLM Agent-Level Metamorphic Stress Status",
        "",
        f"- Status: `{payload['status']}`",
        f"- Model: `{payload.get('model')}`",
        f"- Verifier pass: `{payload.get('verifier', {}).get('pass')}`",
        f"- Feedback: `{payload.get('verifier', {}).get('feedback_type')}`",
        "",
        "Boundary: this is one live LLM data-quality row-shuffle stress. It is not Harbor evidence, not hidden validation, and not broad LLM robustness.",
        "",
    ]
    if payload.get("failure_reason"):
        lines.append(f"Failure reason: `{payload['failure_reason']}`")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    skill_dir, target_dir, agent_dir = prepare()
    code = run_agent(
        skill_dir=skill_dir,
        target_dir=target_dir,
        out_dir=agent_dir,
        base_url=os.environ.get("OPENAI_BASE_URL"),
        api_key=os.environ.get("OPENAI_API_KEY"),
        model=os.environ.get("MODEL") or os.environ.get("OPENAI_MODEL"),
        temperature=0.0,
        timeout=90.0,
        task_label="training dataset quality review",
        contract_mode="strict",
        prompt_addendum="This is a metamorphic row-shuffle target. Preserve conclusions that are invariant to row order.",
    )
    report_payload = json.loads((agent_dir / "security_report.json").read_text(encoding="utf-8"))
    verifier = verify_controlled_execution(CAPABILITIES, report_payload, target_text=target_text()).to_dict()
    write_json(agent_dir / "verifier_report.json", verifier)
    metadata = json.loads((agent_dir / "backend_metadata.json").read_text(encoding="utf-8"))
    payload = {
        "run_id": "live_llm_agent_level_metamorphic_stress_001",
        "status": metadata.get("status"),
        "failure_reason": metadata.get("failure_reason"),
        "model": metadata.get("model"),
        "agent_exit_code": code,
        "verifier": summarize_verifier_report(verifier),
        "artifacts": {
            "prompt": "agent/prompt.md",
            "raw_response": "agent/raw_response.txt",
            "security_report": "agent/security_report.json",
            "verifier_report": "agent/verifier_report.json",
            "model_calls": "agent/model_calls.json",
            "backend_metadata": "agent/backend_metadata.json",
        },
        "boundary": "One live LLM agent-level data-quality row-shuffle stress; not hidden external validation.",
    }
    write_json(JSON_OUT, payload)
    write_text(MD_OUT, render(payload))
    print(json.dumps({"json": str(JSON_OUT), "report": str(MD_OUT), "status": payload["status"], "verifier_pass": payload["verifier"]["pass"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
