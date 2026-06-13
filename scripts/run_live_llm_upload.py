from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SRC_ROOT = ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from skill_deployment import RepairContext, RunnerContext, SkillPackage, VerifierReport, build_patch_and_gate, build_repair_loop_validity_card, get_backend_runner, render_single_validity_card_markdown, summarize_verifier_report
from scripts.run_generalization_suite import load_repair_policy, render_skill, select_scenarios, verify


DEFAULT_SMOKE_DIR = ROOT / "outputs" / "live_llm_upload_001"
DEFAULT_LOOP_DIR = ROOT / "outputs" / "live_llm_repair_loop_upload_001"


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def scenario_output_dirs(scenario: Any) -> tuple[Path, Path]:
    if scenario.case_id == "upload_security_001":
        return DEFAULT_SMOKE_DIR, DEFAULT_LOOP_DIR
    if scenario.case_id == "config_security_001":
        return ROOT / "outputs" / "live_llm_config_security_001", ROOT / "outputs" / "live_llm_repair_loop_config_security_001"
    if scenario.case_id == "data_quality_review_001":
        return ROOT / "outputs" / "live_llm_data_quality_001", ROOT / "outputs" / "live_llm_repair_loop_data_quality_001"
    slug = scenario.case_id.replace("-", "_")
    return ROOT / "outputs" / f"live_llm_{slug}", ROOT / "outputs" / f"live_llm_repair_loop_{slug}"


def scenario_task_label(scenario: Any) -> str:
    labels = {
        "upload_security": "file upload security review",
        "config_security": "configuration security review",
        "api_or_code_review": "API and code review",
        "data_quality_review": "training dataset quality review",
    }
    return labels.get(scenario.task_family, scenario.task_family.replace("_", " "))


def scenario_loop_contract_mode(scenario: Any, attempt_stage: str) -> tuple[str, str]:
    prompt_suffix = ""
    if scenario.case_id in {"config_security_001", "api_review_001"}:
        prompt_suffix = " Review each exposed capability_id one by one; for every capability that is concretely grounded in the target, emit a separate finding."
    if scenario.case_id in {"data_quality_review_001", "api_review_001"} and attempt_stage == "A1":
        return (
            "evidence_only",
            "In this exploratory v1 run, every finding may omit recommended_fix. Keep findings target-grounded and structured under `findings`." + prompt_suffix,
        )
    return "strict", prompt_suffix.strip()


def scenario_loop_v1_capabilities(scenario: Any) -> list[str]:
    if scenario.case_id == "config_security_001":
        return ["CONFIG_AUDIT_EXPORT"]
    return list(scenario.v1_capabilities)


def prepare_skill(
    skill_dir: Path,
    scenario: Any,
    capabilities: list[str],
    version: str,
    repair_action: str | None = None,
    extra_note: str | None = None,
) -> SkillPackage:
    if skill_dir.exists():
        shutil.rmtree(skill_dir)
    skill_dir.mkdir(parents=True)
    skill_package = SkillPackage(
        skill_id=scenario.case_id,
        version=version,
        task_family=scenario.task_family,
        capabilities=tuple(capabilities),
        output_contract=("capability_id", "evidence_span", "recommended_fix"),
        trace_contract=("event", "capability_id", "evidence_span"),
        metadata={"repair_action": repair_action} if repair_action else {},
    )
    skill_text = render_skill(scenario, capabilities, version, repair_action)
    if extra_note:
        skill_text = "\n".join([skill_text, "", "## Attempt Note", "", extra_note, ""])
    write_text(skill_dir / "SKILL.md", skill_text)
    write_json(skill_dir / "manifest.json", skill_package.to_dict())
    return skill_package


def prepare_target(target_dir: Path, scenario: Any) -> None:
    if target_dir.exists():
        shutil.rmtree(target_dir)
    target_dir.mkdir(parents=True)
    write_text(target_dir / "target.md", scenario.target_asset)


def run_llm_agent(
    *,
    scenario: Any,
    attempt_id: str,
    skill_dir: Path,
    target_dir: Path,
    out_dir: Path,
    skill_package: SkillPackage | None,
    contract_mode: str = "strict",
    prompt_addendum: str = "",
) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    for artifact_name in (
        "prompt.md",
        "raw_response.txt",
        "security_report.json",
        "verifier_report.json",
        "model_calls.json",
        "backend_metadata.json",
        "stdout.log",
        "stderr.log",
        "process.json",
    ):
        artifact_path = out_dir / artifact_name
        if artifact_path.exists():
            artifact_path.unlink()
    runner = get_backend_runner("live_llm_text", project_root=ROOT)
    result = runner.run(
        RunnerContext(
            scenario_id=scenario.case_id,
            backend="live_llm_text",
            target_dir=target_dir,
            output_dir=out_dir,
            attempt_id=attempt_id,
            skill_package=skill_package,
            task_case=scenario,
            metadata={
                "skill_dir": skill_dir,
                "task_label": scenario_task_label(scenario),
                "contract_mode": contract_mode,
                "prompt_addendum": prompt_addendum,
            },
        )
    )
    write_json(
        out_dir / "process.json",
        {
            "command": ["python", "agents/llm_security_agent.py", "--skill", "<skill>", "--target", "<target>", "--out", "<out>"],
            "output_path": str(result.output_path) if result.output_path else None,
            "stdout_path": str(result.stdout_path) if result.stdout_path else None,
            "stderr_path": str(result.stderr_path) if result.stderr_path else None,
            "metadata_path": str(result.metadata_path) if result.metadata_path else None,
        },
    )
    if not (out_dir / "security_report.json").exists():
        write_json(out_dir / "security_report.json", result.report.to_dict())
    return read_json(out_dir / "security_report.json")


def summarize_verifier(report: dict[str, Any]) -> dict[str, Any]:
    return summarize_verifier_report(report)


def repair_from_current_capabilities(
    scenario: Any,
    feedback: dict[str, Any],
    repair_policy: dict[str, str],
    current_capabilities: list[str],
) -> tuple[list[str], dict[str, Any], dict[str, Any]]:
    context = RepairContext(
        scenario_id=scenario.case_id,
        task_family=scenario.task_family,
        current_capabilities=tuple(current_capabilities),
        expected_capabilities=tuple(scenario.expected_capabilities),
        verifier_report=VerifierReport.from_dict(feedback),
        repair_policy=repair_policy,
    )
    after_capabilities, patch, gate = build_patch_and_gate(context)
    return list(after_capabilities), patch.to_dict(), gate.to_dict()


def write_loop_validity_card(loop_dir: Path, scenario: Any, a1_report: dict[str, Any], a2_report: dict[str, Any], patch: dict[str, Any], gate: dict[str, Any]) -> None:
    _, loop_dir_expected = scenario_output_dirs(scenario)
    artifact = str(loop_dir_expected.relative_to(ROOT)).replace("\\", "/")
    card_map = {
        "upload_security_001": (
            "live_llm_upload_repair_loop_validity_card",
            "Single local live-LLM repair-loop evidence on one controlled upload task; verifier and gate remain deterministic.",
            "Single controlled security slice only.",
        ),
        "config_security_001": (
            "live_llm_config_security_repair_loop_validity_card",
            "Single local live-LLM repair-loop evidence on one controlled configuration-security task; verifier and gate remain deterministic.",
            "Second local controlled security slice only; not broad multi-task live-LLM generalization.",
        ),
        "api_review_001": (
            "live_llm_api_review_repair_loop_validity_card",
            "Single local live-LLM repair-loop evidence on one controlled API/code-review task; verifier and gate remain deterministic.",
            "Third local controlled slice only; not broad multi-task live-LLM generalization.",
        ),
        "data_quality_review_001": (
            "live_llm_data_quality_repair_loop_validity_card",
            "Single local live-LLM repair-loop evidence on one controlled non-security data-quality task; verifier and gate remain deterministic.",
            "One controlled non-security slice only; not broad multi-domain generalization.",
        ),
    }
    card_id, boundary, transferability_note = card_map.get(
        scenario.case_id,
        (
            f"live_llm_{scenario.case_id}_repair_loop_validity_card",
            f"Single local live-LLM repair-loop evidence on {scenario.case_id}; verifier and gate remain deterministic.",
            "Single controlled task slice only.",
        ),
    )
    card = build_repair_loop_validity_card(
        card_id=card_id,
        artifact=artifact,
        scenario=scenario.case_id,
        backend="live_llm_text",
        a1_report=a1_report,
        a2_report=a2_report,
        patch_plan=patch,
        gate_decision=gate,
        sources=[
            f"{artifact}/A1/verifier_report.json",
            f"{artifact}/revision/patch_plan.json",
            f"{artifact}/revision/gate_decision.json",
            f"{artifact}/A2/verifier_report.json",
            f"{artifact}/A1/security_report.json",
            f"{artifact}/A2/security_report.json",
        ],
        claim_boundary=boundary,
        grounded_agent_artifacts=True,
        transferability_note=transferability_note,
    )
    write_json(loop_dir / "validity_card.json", card)
    write_text(loop_dir / "validity_card.md", render_single_validity_card_markdown(card))


def write_smoke_summary(scenario: Any, out_dir: Path, verifier_report: dict[str, Any]) -> None:
    metadata = read_json(out_dir / "backend_metadata.json") if (out_dir / "backend_metadata.json").exists() else {}
    summary = {
        "run_id": out_dir.name,
        "scenario": scenario.case_id,
        "backend": "live_llm_text",
        "env_ready": all(os.environ.get(name) for name in ("OPENAI_BASE_URL", "OPENAI_API_KEY", "MODEL")),
        "model": os.environ.get("MODEL"),
        "agent_status": metadata.get("status"),
        "failure_reason": metadata.get("failure_reason"),
        "verifier": summarize_verifier(verifier_report),
        "artifacts": {
            "prompt": "prompt.md",
            "raw_response": "raw_response.txt",
            "security_report": "security_report.json",
            "verifier_report": "verifier_report.json",
            "model_calls": "model_calls.json",
            "backend_metadata": "backend_metadata.json",
        },
        "boundary": "LLM is the agent only; deterministic verifier/gate decides success.",
    }
    write_json(out_dir / "summary.json", summary)
    write_text(
        out_dir / "summary.md",
        "\n".join(
            [
                f"# Live LLM Smoke: {scenario.case_id}",
                "",
                f"- Scenario: `{scenario.case_id}`",
                f"- Agent status: `{summary['agent_status']}`",
                f"- Model: `{summary['model']}`",
                f"- Verifier pass: `{verifier_report['pass']}`",
                f"- Feedback: `{verifier_report['feedback_type']}`",
                f"- Coverage: `{summary['verifier']['coverage']}`",
                f"- Missing: `{', '.join(verifier_report['missing_capabilities']) or 'none'}`",
                "",
                "Boundary: LLM output is judged by the deterministic verifier. This is not self-graded.",
                "",
            ]
        ),
    )


def run_smoke(scenario: Any) -> dict[str, Any]:
    smoke_dir, _ = scenario_output_dirs(scenario)
    if smoke_dir.exists():
        shutil.rmtree(smoke_dir)
    skill_dir = smoke_dir / "skill"
    target_dir = smoke_dir / "target_asset"
    skill_package = prepare_skill(skill_dir, scenario, list(scenario.expected_capabilities), "v2")
    prepare_target(target_dir, scenario)
    output = run_llm_agent(scenario=scenario, attempt_id="A2_skill_v2_smoke", skill_dir=skill_dir, target_dir=target_dir, out_dir=smoke_dir, skill_package=skill_package)
    verifier_report = verify(scenario, output)
    write_json(smoke_dir / "verifier_report.json", verifier_report)
    write_smoke_summary(scenario, smoke_dir, verifier_report)
    return {"output": output, "verifier": verifier_report}


def run_loop(scenario: Any) -> dict[str, Any]:
    _, loop_dir = scenario_output_dirs(scenario)
    if loop_dir.exists():
        shutil.rmtree(loop_dir)
    target_dir = loop_dir / "target_asset"
    prepare_target(target_dir, scenario)
    repair_policy = load_repair_policy()

    a1_contract_mode, a1_prompt_addendum = scenario_loop_contract_mode(scenario, "A1")
    a1_skill = loop_dir / "skills" / "skill_v1"
    a1_extra_note = None
    if a1_contract_mode == "evidence_only":
        a1_extra_note = "Exploratory v1: findings may omit recommended_fix so the verifier can test output-contract repair."
    a1_skill_package = prepare_skill(a1_skill, scenario, scenario_loop_v1_capabilities(scenario), "v1", extra_note=a1_extra_note)
    a1_output = run_llm_agent(
        scenario=scenario,
        attempt_id="A1_skill_v1",
        skill_dir=a1_skill,
        target_dir=target_dir,
        out_dir=loop_dir / "A1",
        skill_package=a1_skill_package,
        contract_mode=a1_contract_mode,
        prompt_addendum=a1_prompt_addendum,
    )
    a1_report = verify(scenario, a1_output)
    write_json(loop_dir / "A1" / "verifier_report.json", a1_report)
    write_json(loop_dir / "A1" / "failure_feedback.json", a1_report)

    v2_caps, patch, gate = repair_from_current_capabilities(
        scenario,
        a1_report,
        repair_policy,
        list(a1_skill_package.capabilities),
    )
    write_json(loop_dir / "revision" / "patch_plan.json", patch)
    write_json(loop_dir / "revision" / "gate_decision.json", gate)
    write_text(
        loop_dir / "revision" / "skill_diff.md",
        "\n".join(
            [
                "# Live LLM Skill Diff",
                "",
                "```diff",
                *[f"-{capability}" for capability in scenario.v1_capabilities if capability not in v2_caps],
                *[f" {capability}" for capability in scenario.v1_capabilities if capability in v2_caps],
                *[f"+{capability}" for capability in v2_caps if capability not in scenario.v1_capabilities],
                "```",
                "",
            ]
        ),
    )

    a2_skill = loop_dir / "skills" / "skill_v2"
    a2_skill_package = prepare_skill(a2_skill, scenario, v2_caps, "v2", patch["repair_action"])
    a2_output = run_llm_agent(
        scenario=scenario,
        attempt_id="A2_skill_v2",
        skill_dir=a2_skill,
        target_dir=target_dir,
        out_dir=loop_dir / "A2",
        skill_package=a2_skill_package,
    )
    a2_report = verify(scenario, a2_output)
    write_json(loop_dir / "A2" / "verifier_report.json", a2_report)

    summary = {
        "run_id": loop_dir.name,
        "scenario": scenario.case_id,
        "backend": "live_llm_text",
        "env_ready": all(os.environ.get(name) for name in ("OPENAI_BASE_URL", "OPENAI_API_KEY", "MODEL")),
        "model": os.environ.get("MODEL"),
        "A1": summarize_verifier(a1_report),
        "revision": {
            "feedback_type": patch["feedback_type"],
            "repair_action": patch["repair_action"],
            "before_capabilities": patch["before_capabilities"],
            "after_capabilities": patch["after_capabilities"],
            "gate_decision": gate["decision"],
        },
        "A2": summarize_verifier(a2_report),
        "reward_delta": float(a2_report["pass"]) - float(a1_report["pass"]),
        "boundary": "LLM is the non-oracle agent; verifier/gate remain deterministic.",
    }
    write_json(loop_dir / "summary.json", summary)
    write_text(
        loop_dir / "summary.md",
        "\n".join(
            [
                f"# Live LLM Repair Loop: {scenario.case_id}",
                "",
                "| Attempt | Pass | Feedback | Coverage | Missing |",
                "|---|---:|---|---:|---|",
                f"| A1 | {a1_report['pass']} | {a1_report['feedback_type']} | {summary['A1']['coverage']} | {', '.join(a1_report['missing_capabilities']) or 'none'} |",
                f"| A2 | {a2_report['pass']} | {a2_report['feedback_type']} | {summary['A2']['coverage']} | {', '.join(a2_report['missing_capabilities']) or 'none'} |",
                "",
                "## Boundary",
                "",
                "The LLM is only the agent that reads target/skill and emits `security_report.json`. The verifier/gate are deterministic and do not ask the LLM to grade itself.",
                "",
            ]
        ),
    )
    write_loop_validity_card(loop_dir, scenario, a1_report, a2_report, patch, gate)
    return summary


def write_scenario_status_report(scenario: Any, loop_summary: dict[str, Any], loop_dir: Path) -> None:
    if scenario.case_id == "data_quality_review_001":
        report_path = ROOT / "reports" / "LIVE_LLM_DATA_QUALITY_STATUS.md"
        title = "Live LLM Data Quality Status"
        boundary = "This is one controlled non-security local live-LLM repair loop. It shows the system is not only shaped for security tasks, but it is still narrow evidence rather than broad multi-domain generalization."
    elif scenario.case_id == "config_security_001":
        report_path = ROOT / "reports" / "LIVE_LLM_CONFIG_STATUS.md"
        title = "Live LLM Config Security Status"
        boundary = "This is one controlled second local security slice for the live-LLM backend. It improves beyond upload-only evidence, but it is still narrow controlled evidence rather than broad security-task generalization."
    elif scenario.case_id == "api_review_001":
        report_path = ROOT / "reports" / "LIVE_LLM_API_REVIEW_STATUS.md"
        title = "Live LLM API Review Status"
        boundary = "This is one controlled local API/code-review repair loop for the live-LLM backend. It broadens beyond upload-only evidence, but it is still narrow controlled evidence rather than broad live-LLM task generalization."
    else:
        return
    a1 = loop_summary["A1"]
    a2 = loop_summary["A2"]
    lines = [
        f"# {title}",
        "",
        f"- Scenario: `{scenario.case_id}`",
        f"- Backend: `{loop_summary['backend']}`",
        f"- Model: `{loop_summary['model']}`",
        f"- Artifact dir: `{loop_dir.relative_to(ROOT)}`",
        "",
        "| Attempt | Pass | Feedback | Coverage | Schema | Weak Evidence |",
        "|---|---:|---|---:|---:|---:|",
        f"| A1 | {a1['pass']} | {a1['feedback_type']} | {a1['coverage']} | {a1['schema_correctness']} | {a1['evidence_binding']} |",
        f"| A2 | {a2['pass']} | {a2['feedback_type']} | {a2['coverage']} | {a2['schema_correctness']} | {a2['evidence_binding']} |",
        "",
        "## What happened",
        "",
        f"A1 feedback was `{loop_summary['revision']['feedback_type']}` and the typed repair selected `{loop_summary['revision']['repair_action']}`.",
        f"Capabilities before repair: `{', '.join(loop_summary['revision']['before_capabilities']) or 'none'}`.",
        f"Capabilities after repair: `{', '.join(loop_summary['revision']['after_capabilities']) or 'none'}`.",
        f"Gate decision: `{loop_summary['revision']['gate_decision']}`.",
        "",
        "## Boundary",
        "",
        boundary,
        "",
    ]
    write_text(report_path, "\n".join(lines))


def main() -> int:
    parser = argparse.ArgumentParser(description="Run controlled live LLM smoke and A1/A2 loop.")
    parser.add_argument("--scenario", default="upload")
    parser.add_argument("--skip-smoke", action="store_true")
    parser.add_argument("--skip-loop", action="store_true")
    args = parser.parse_args()

    scenario = select_scenarios(args.scenario)[0]
    smoke_dir, loop_dir = scenario_output_dirs(scenario)
    results: dict[str, Any] = {}
    if not args.skip_smoke:
        results["smoke"] = run_smoke(scenario)
    if not args.skip_loop:
        results["loop"] = run_loop(scenario)
        write_scenario_status_report(scenario, results["loop"], loop_dir)

    print(
        json.dumps(
            {
                "smoke": str(smoke_dir) if "smoke" in results else None,
                "loop": str(loop_dir) if "loop" in results else None,
                "env_ready": all(os.environ.get(name) for name in ("OPENAI_BASE_URL", "OPENAI_API_KEY", "MODEL")),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
