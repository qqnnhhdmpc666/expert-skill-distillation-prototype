from __future__ import annotations

import html
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from demo.streamlit_app import DEFAULT_SCENARIO, build_run


OUT_DIR = ROOT / "review_package"
ZIP_PATH = ROOT / "review_package.zip"
EXPORT_COMPAT_PATH = ROOT / "review_package_export.zip"
MULTITASK_DIR = ROOT / "outputs" / "multitask_closed_loop_001"
WSL_REAL_TASK_DIR = ROOT / "outputs" / "wsl_harbor_real_upload_001"
NON_ORACLE_LOCAL_DIR = ROOT / "outputs" / "non_oracle_local_agent_upload_001"
LIVE_LLM_DIR = ROOT / "outputs" / "live_llm_upload_001"
LIVE_LLM_LOOP_DIR = ROOT / "outputs" / "live_llm_repair_loop_upload_001"
LIVE_LLM_DATA_QUALITY_LOOP_DIR = ROOT / "outputs" / "live_llm_repair_loop_data_quality_001"
LIVE_LLM_CONFIG_DIR = ROOT / "outputs" / "live_llm_config_security_001"
LIVE_LLM_CONFIG_LOOP_DIR = ROOT / "outputs" / "live_llm_repair_loop_config_security_001"
LIVE_LLM_API_DIR = ROOT / "outputs" / "live_llm_api_review_001"
LIVE_LLM_API_LOOP_DIR = ROOT / "outputs" / "live_llm_repair_loop_api_review_001"
HARBOR_NON_ORACLE_DIR = ROOT / "outputs" / "harbor_non_oracle_upload_001"
HARBOR_NON_ORACLE_CLI_DIR = ROOT / "outputs" / "harbor_non_oracle_cli_upload_001"
HARBOR_NON_ORACLE_REPAIR_LOOP_DIR = ROOT / "outputs" / "harbor_non_oracle_repair_loop_upload_001"
HARBOR_LLM_DIR = ROOT / "outputs" / "harbor_llm_upload_001"
HARBOR_LLM_REPAIR_LOOP_DIR = ROOT / "outputs" / "harbor_llm_repair_loop_upload_001"
HARBOR_LLM_CONFIG_LOOP_DIR = ROOT / "outputs" / "harbor_llm_repair_loop_config_001"
HARBOR_LIVE_SKELETON_DIR = ROOT / "outputs" / "harbor_live_skeleton_upload_001"
SYSTEM_ACCEPTANCE_DIR = ROOT / "outputs" / "system_acceptance_001"
VALIDATION_DIR = ROOT / "outputs" / "validation"
SKILL_LIFECYCLE_EVIDENCE_DIR = ROOT / "outputs" / "skill_lifecycle_evidence"
INSTALLED_SKILLS_DIR = ROOT / "outputs" / "installed_skills"
REVIEWER_READINESS_DIR = ROOT / "outputs" / "reviewer_readiness"
DEPLOYABLE_CODEX_SKILL_DIR = ROOT / "outputs" / "deployable_codex_skill"
SKILL_EVOLUTION_LAB_DIR = ROOT / "outputs" / "skill_evolution_lab"
EXTERNAL_SECURITY_VALIDATION_DIR = ROOT / "outputs" / "external_security_validation"
SCREENSHOT_DIR = ROOT / "reports" / "screenshots"


def copy_tree(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def ensure_multitask_artifacts() -> None:
    summary_path = MULTITASK_DIR / "summary.json"
    if summary_path.exists():
        return
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "run_multitask_closed_loop.py")],
        cwd=ROOT,
        check=True,
    )


def table(rows: list[dict[str, object]]) -> str:
    if not rows:
        return "<p>No data.</p>"
    headers = list(rows[0])
    head = "".join(f"<th>{html.escape(header)}</th>" for header in headers)
    body = []
    for row in rows:
        body.append("<tr>" + "".join(f"<td>{html.escape(str(row.get(header, '')))}</td>" for header in headers) + "</tr>")
    return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(body)}</tbody></table>"


def existing_links(candidates: list[tuple[str, str]]) -> str:
    links: list[str] = []
    for label, href in candidates:
        if (OUT_DIR / href).exists():
            links.append(f'<li><a href="{html.escape(href)}">{html.escape(label)}</a></li>')
    return "\n".join(links)


def multitask_rows(summary: dict[str, Any]) -> list[dict[str, object]]:
    return [
        {
            "Task": row["case_id"],
            "Family": row["task_family"],
            "A1 feedback": row["feedback_type"],
            "Repair": row["patch_operator"],
            "A2 pass": row["a2_pass"],
            "Coverage A0/A1/A2": f"{row['a0_coverage']:.2f}/{row['a1_coverage']:.2f}/{row['a2_coverage']:.2f}",
        }
        for row in summary["case_summaries"]
    ]


def build_index(run_dir: Path) -> str:
    metrics = load_json(run_dir / "summary" / "front_metrics.json")
    manifest = load_json(run_dir / "artifacts" / "skill_package_v2_manifest.json")
    a2 = load_json(run_dir / "attempts" / "A2_skill_v2.json")
    multitask = load_json(MULTITASK_DIR / "summary.json")
    wsl_real_task = load_json(WSL_REAL_TASK_DIR / "summary.json") if (WSL_REAL_TASK_DIR / "summary.json").exists() else None
    harbor_repair_loop = (
        load_json(HARBOR_NON_ORACLE_REPAIR_LOOP_DIR / "summary.json")
        if (HARBOR_NON_ORACLE_REPAIR_LOOP_DIR / "summary.json").exists()
        else None
    )
    live_llm_smoke = load_json(LIVE_LLM_DIR / "summary.json") if (LIVE_LLM_DIR / "summary.json").exists() else None
    harbor_llm = load_json(HARBOR_LLM_DIR / "summary.json") if (HARBOR_LLM_DIR / "summary.json").exists() else None
    harbor_llm_loop = load_json(HARBOR_LLM_REPAIR_LOOP_DIR / "summary.json") if (HARBOR_LLM_REPAIR_LOOP_DIR / "summary.json").exists() else None
    harbor_llm_config_loop = (
        load_json(HARBOR_LLM_CONFIG_LOOP_DIR / "summary.json")
        if (HARBOR_LLM_CONFIG_LOOP_DIR / "summary.json").exists()
        else None
    )
    harbor_llm_repeatability = (
        load_json(VALIDATION_DIR / "harbor_llm_repeatability_upload.json")
        if (VALIDATION_DIR / "harbor_llm_repeatability_upload.json").exists()
        else None
    )
    live_llm_data_quality = (
        load_json(LIVE_LLM_DATA_QUALITY_LOOP_DIR / "summary.json")
        if (LIVE_LLM_DATA_QUALITY_LOOP_DIR / "summary.json").exists()
        else None
    )
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    value_rows = [
        {"Metric": "Closed-loop result", "Value": metrics["status_chain"]},
        {"Metric": "Task success", "Value": f"{metrics['success_rate_before']}% -> {metrics['success_rate_after']}%"},
        {"Metric": "New useful findings", "Value": metrics["added_findings"]},
        {"Metric": "Token budget", "Value": f"{metrics['token_total']} / {metrics['token_budget']}"},
        {"Metric": "Multi-task A2 pass", "Value": f"{multitask['a2_pass_count']} / {multitask['case_count']}"},
        {
            "Metric": "WSL2 Harbor security task",
            "Value": f"reward {wsl_real_task['reward']}" if wsl_real_task else "not included",
        },
        {
            "Metric": "Harbor non-oracle repair loop",
            "Value": (
                f"A1 {harbor_repair_loop['A1']['reward']} -> A2 {harbor_repair_loop['A2']['reward']}"
                if harbor_repair_loop
                else "not included"
            ),
        },
        {
            "Metric": "Local live LLM upload",
            "Value": "PASS" if live_llm_smoke and live_llm_smoke["verifier"]["pass"] else "not included",
        },
        {
            "Metric": "Harbor live LLM upload",
            "Value": f"reward {harbor_llm['reward']}" if harbor_llm else "not included",
        },
        {
            "Metric": "Harbor live LLM repair loop",
            "Value": (
                f"A1 {harbor_llm_loop['A1']['reward']} -> A2 {harbor_llm_loop['A2']['reward']}"
                if harbor_llm_loop
                else "not included"
            ),
        },
        {
            "Metric": "Harbor live LLM config repair loop",
            "Value": (
                f"A1 {harbor_llm_config_loop['A1']['reward']} -> A2 {harbor_llm_config_loop['A2']['reward']}"
                if harbor_llm_config_loop
                else "not included"
            ),
        },
        {
            "Metric": "Harbor LLM upload repeatability",
            "Value": (
                f"{harbor_llm_repeatability['run_count']} runs, A1 all fail={harbor_llm_repeatability['a1_all_fail']}, A2 all pass={harbor_llm_repeatability['a2_all_pass']}"
                if harbor_llm_repeatability
                else "not included"
            ),
        },
        {
            "Metric": "Local live LLM data-quality loop",
            "Value": (
                f"A1 {live_llm_data_quality['A1']['feedback_type']} -> A2 pass"
                if live_llm_data_quality
                else "not included"
            ),
        },
    ]
    findings = [
        {
            "Finding": item["capability"],
            "Evidence": item["evidence_span"],
            "Fix": item["recommended_fix"],
        }
        for item in a2["findings"]
    ]
    artifact_links = existing_links(
        [
            ("Final user-facing report", "artifacts/reports/final_report.md"),
            ("Correction report", "artifacts/reports/correction_report.md"),
            ("Skill manifest", "artifacts/artifacts/skill_package_v2_manifest.json"),
            ("Multi-task closed-loop summary", "multitask/summary.md"),
            ("Multi-task machine-readable summary", "multitask/summary.json"),
            ("WSL2 Harbor real security task summary", "wsl_real_task/summary.md"),
            ("WSL2 Harbor real security task JSON", "wsl_real_task/summary.json"),
            ("WSL2 Harbor security report", "wsl_real_task/real-upload-security-review__dCxSUn5/artifacts/security_report.json"),
            ("WSL2 Harbor verifier result", "wsl_real_task/real-upload-security-review__dCxSUn5/artifacts/result.json"),
            ("Non-oracle local agent smoke", "non_oracle_local_agent/summary.md"),
            ("Non-oracle local agent JSON", "non_oracle_local_agent/summary.json"),
            ("Non-oracle local suite", "validation/non_oracle_local_suite.md"),
            ("Local live LLM upload smoke", "live_llm_upload/summary.md"),
            ("Local live LLM upload verifier", "live_llm_upload/verifier_report.json"),
            ("Local live LLM A1/A2 loop", "live_llm_repair_loop/summary.md"),
            ("Local live LLM A1 verifier", "live_llm_repair_loop/A1/verifier_report.json"),
            ("Local live LLM A2 verifier", "live_llm_repair_loop/A2/verifier_report.json"),
            ("Local live LLM data-quality A1/A2 loop", "live_llm_repair_loop_data_quality/summary.md"),
            ("Local live LLM data-quality validity card", "live_llm_repair_loop_data_quality/validity_card.json"),
            ("Local live LLM config smoke", "live_llm_config_security/summary.md"),
            ("Local live LLM config A1/A2 loop", "live_llm_repair_loop_config_security/summary.md"),
            ("Local live LLM config validity card", "live_llm_repair_loop_config_security/validity_card.json"),
            ("Local live LLM API-review smoke", "live_llm_api_review/summary.md"),
            ("Local live LLM API-review A1/A2 loop", "live_llm_repair_loop_api_review/summary.md"),
            ("Local live LLM API-review validity card", "live_llm_repair_loop_api_review/validity_card.json"),
            ("Harbor non-oracle upload smoke", "harbor_non_oracle_upload/summary.md"),
            ("Harbor non-oracle JSON", "harbor_non_oracle_upload/summary.json"),
            ("Harbor non-oracle CLI upload attempt", "harbor_non_oracle_cli_upload/summary.md"),
            ("Harbor non-oracle CLI security report", "harbor_non_oracle_cli_upload/security_report.json"),
            ("Harbor non-oracle CLI verifier report", "harbor_non_oracle_cli_upload/verifier_report.json"),
            ("Harbor non-oracle A1/A2 repair loop", "harbor_non_oracle_repair_loop_upload/summary.md"),
            ("Harbor repair loop A1 feedback", "harbor_non_oracle_repair_loop_upload/A1/failure_feedback.json"),
            ("Harbor repair loop patch plan", "harbor_non_oracle_repair_loop_upload/revision/patch_plan.json"),
            ("Harbor repair loop A2 verifier", "harbor_non_oracle_repair_loop_upload/A2/verifier_report.json"),
            ("Harbor live LLM upload", "harbor_llm_upload/summary.md"),
            ("Harbor live LLM verifier", "harbor_llm_upload/verifier_report.json"),
            ("Harbor live LLM target reads", "harbor_llm_upload/target_reads.json"),
            ("Harbor live LLM A1/A2 loop", "harbor_llm_repair_loop_upload/summary.md"),
            ("Harbor live LLM A1 verifier", "harbor_llm_repair_loop_upload/A1/verifier_report.json"),
            ("Harbor live LLM patch plan", "harbor_llm_repair_loop_upload/revision/patch_plan.json"),
            ("Harbor live LLM A2 verifier", "harbor_llm_repair_loop_upload/A2/verifier_report.json"),
            ("Harbor live LLM config A1/A2 loop", "harbor_llm_repair_loop_config/summary.md"),
            ("Harbor live LLM config A1 verifier", "harbor_llm_repair_loop_config/A1/verifier_report.json"),
            ("Harbor live LLM config patch plan", "harbor_llm_repair_loop_config/revision/patch_plan.json"),
            ("Harbor live LLM config A2 verifier", "harbor_llm_repair_loop_config/A2/verifier_report.json"),
            ("Project system acceptance report", "system_acceptance/summary.md"),
            ("Project system acceptance JSON", "system_acceptance/summary.json"),
            ("Generalization suite", "validation/generalization_suite.md"),
            ("Negative controls JSON", "validation/negative_controls.json"),
            ("Verifier stress checks JSON", "validation/verifier_stress_checks.json"),
            ("Repair policy alignment JSON", "validation/repair_policy_alignment.json"),
            ("Ablation summary", "validation/ablation_summary.md"),
            ("Harbor LLM upload repeatability JSON", "validation/harbor_llm_repeatability_upload.json"),
            ("Skill qualification cards JSON", "validation/skill_qualification_cards.json"),
            ("Promotion mechanism comparison JSON", "validation/promotion_mechanism_comparison.json"),
            ("Promotion mechanism challenge set JSON", "validation/promotion_mechanism_challenge_set.json"),
            ("Artifact-backed promotion challenge set JSON", "validation/artifact_backed_promotion_challenge_set.json"),
            ("Promotion mechanism fairness audit JSON", "validation/promotion_mechanism_fairness_audit.json"),
            ("Minimal metamorphic stress JSON", "validation/metamorphic_stress_minimal.json"),
            ("Agent-level metamorphic stress JSON", "validation/agent_level_metamorphic_stress_001/summary.json"),
            ("Live LLM agent-level metamorphic stress JSON", "validation/live_llm_agent_level_metamorphic_stress_001/summary.json"),
            ("Skill lifecycle evidence index", "skill_lifecycle_evidence/index.json"),
            ("Installed skills registry", "installed_skills/registry.json"),
            ("Reviewer readiness assessment", "reviewer_readiness/reviewer_assessment.json"),
            ("Skill net-effect matrix", "validation/skill_net_effect_matrix.json"),
            ("ReSkill-style marginal utility", "validation/skill_marginal_utility/skill_marginal_utility.json"),
            ("Deployable Codex Skill manifest", "deployable_codex_skill/secure_code_review/manifest.json"),
            ("Skill Evolution Lab summary", "skill_evolution_lab/secure_code_review/evolution_summary.json"),
            ("Rejected edit buffer", "skill_evolution_lab/secure_code_review/rejected_edit_buffer.json"),
            ("Retirement decisions", "skill_evolution_lab/secure_code_review/retirement_decisions.json"),
            ("Harbor live skeleton", "harbor_live_skeleton_upload/summary.json"),
            ("External security scaffold", "external_security_validation/cyberseceval_style_small_sample_scaffold.json"),
            ("Skill qualification card status", "reports/SKILL_QUALIFICATION_CARD_STATUS.md"),
            ("Promotion mechanism exploration", "reports/PROMOTION_MECHANISM_EXPLORATION.md"),
            ("Promotion mechanism challenge set status", "reports/PROMOTION_MECHANISM_CHALLENGE_SET_STATUS.md"),
            ("Artifact-backed promotion challenge set status", "reports/ARTIFACT_BACKED_PROMOTION_CHALLENGE_SET_STATUS.md"),
            ("Promotion mechanism fairness audit", "reports/PROMOTION_MECHANISM_FAIRNESS_AUDIT.md"),
            ("Qualification-Guided Skill Evolution", "reports/QUALIFICATION_GUIDED_SKILL_EVOLUTION.md"),
            ("Skill qualification schema", "reports/SKILL_QUALIFICATION_CARD_SCHEMA.md"),
            ("Failure origin taxonomy", "reports/FAILURE_ORIGIN_TAXONOMY.md"),
            ("QGSE failure case study", "reports/QGSE_FAILURE_CASE_STUDY_CONFIG_API.md"),
            ("Metamorphic verifier stress plan", "reports/METAMORPHIC_VERIFIER_STRESS_PLAN.md"),
            ("Minimal metamorphic stress status", "reports/METAMORPHIC_STRESS_STATUS.md"),
            ("Agent-level metamorphic stress status", "reports/AGENT_LEVEL_METAMORPHIC_STRESS_STATUS.md"),
            ("Live LLM agent-level metamorphic stress status", "reports/LIVE_LLM_AGENT_LEVEL_METAMORPHIC_STRESS_STATUS.md"),
            ("Morning status", "reports/MORNING_STATUS_0800.md"),
            ("Generalization audit", "reports/GENERALIZATION_AUDIT.md"),
            ("Negative control status", "reports/NEGATIVE_CONTROL_STATUS.md"),
            ("Verifier stress status", "reports/VERIFIER_STRESS_STATUS.md"),
            ("Repair policy alignment status", "reports/REPAIR_POLICY_OPERATOR_ALIGNMENT_STATUS.md"),
            ("Local agent audit", "reports/LOCAL_AGENT_AUDIT.md"),
            ("Ablation audit", "reports/ABLATION_AUDIT.md"),
            ("Non-oracle local agent status", "reports/NON_ORACLE_LOCAL_AGENT_STATUS.md"),
            ("Harbor non-oracle status", "reports/HARBOR_NON_ORACLE_STATUS.md"),
            ("Harbor LLM repair loop audit", "reports/HARBOR_LLM_REPAIR_LOOP_AUDIT.md"),
            ("Harbor LLM repeatability status", "reports/HARBOR_LLM_REPEATABILITY_STATUS.md"),
            ("LLM backend status", "reports/LLM_BACKEND_STATUS.md"),
            ("Skill lifecycle evidence status", "reports/SKILL_LIFECYCLE_EVIDENCE_STATUS.md"),
            ("Skill installation status", "reports/SKILL_INSTALLATION_STATUS.md"),
            ("Reviewer readiness status", "reports/REVIEWER_READINESS_STATUS.md"),
            ("SPARK / COLLEAGUE / SkillGen / SkillGrad gap ledger", "reports/SPARK_COLLEAGUE_SKILLGEN_SKILLGRAD_GAP_LEDGER.md"),
            ("Remaining hard-code status", "reports/REMAINING_HARDCODE_STATUS.md"),
            ("Deployable Skill Evolution status", "reports/DEPLOYABLE_SKILL_EVOLUTION_STATUS.md"),
            ("WSL2/SPARK backend note", "docs/WSL2_SPARK_BACKEND.md"),
            ("Claim boundary", "docs/CLAIM_BOUNDARY.md"),
            ("Project structure", "docs/PROJECT_STRUCTURE.md"),
            ("Reviewer guide", "docs/REVIEWER_GUIDE.md"),
            ("Implementation borrowing note", "docs/implementation_borrowing_from_spark_colleague.md"),
            ("Real agent run summary", "real_agent/run_summary.json"),
            ("Real agent trajectory", "real_agent/trajectory.jsonl"),
            ("Real agent A2 output", "real_agent/attempts/A2_skill_v2.json"),
        ]
    )
    capabilities = ", ".join(manifest["capabilities"])
    feedback_types = ", ".join(multitask["feedback_types"])
    patch_operators = ", ".join(multitask["patch_operators"])
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>专家知识蒸馏 Demo 评审包</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 0; background: #f6f7f8; color: #18202a; }}
    main {{ max-width: 1120px; margin: auto; padding: 32px 24px 56px; }}
    header {{ margin-bottom: 20px; }}
    section {{ background: white; border: 1px solid #dde3e8; border-radius: 8px; padding: 18px 20px; margin: 16px 0; }}
    .lead {{ font-size: 1.08rem; line-height: 1.7; color: #334155; }}
    .grid {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; }}
    .card {{ border: 1px solid #dde3e8; border-radius: 8px; padding: 12px; background: #fbfcfd; }}
    .card strong {{ display: block; font-size: 1.35rem; margin-top: 6px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 0.94rem; }}
    th, td {{ border: 1px solid #dde3e8; padding: 8px 10px; vertical-align: top; }}
    th {{ background: #eef3f6; text-align: left; }}
    code {{ background: #eef3f6; padding: 2px 4px; border-radius: 4px; }}
    a {{ color: #0f766e; }}
    @media (max-width: 860px) {{ .grid {{ grid-template-columns: 1fr 1fr; }} }}
  </style>
</head>
<body>
<main>
  <header>
    <h1>专家知识蒸馏与 Skill 优化 Demo</h1>
    <p class="lead">用户提供任务场景、专家材料和目标资产后，系统生成可执行 Skill，并用 A0 无 Skill、A1 初始 Skill、A2 修正后 Skill 的对比证明它是否真的帮助解决任务。</p>
    <p>生成时间：{html.escape(generated_at)}</p>
  </header>

  <section>
    <h2>先看有没有用</h2>
    <div class="grid">
      <div class="card">主任务闭环<strong>{html.escape(metrics["status_chain"])}</strong></div>
      <div class="card">成功率提升<strong>{metrics['success_rate_before']}% -> {metrics['success_rate_after']}%</strong></div>
      <div class="card">跨任务验证<strong>{multitask['a2_pass_count']} / {multitask['case_count']} A2 PASS</strong></div>
      <div class="card">WSL2 真实安全任务<strong>{"reward " + str(wsl_real_task["reward"]) if wsl_real_task else "not included"}</strong></div>
    </div>
  </section>

  <section>
    <h2>系统回答的五个问题</h2>
    {table([
        {"Question": "同一套 pipeline 能不能跨多个任务工作", "Answer": f"Yes: {multitask['case_count']} tasks / {multitask['task_family_count']} task families"},
        {"Question": "不同任务能不能触发不同反馈", "Answer": f"Yes: {feedback_types}"},
        {"Question": "反馈能不能变成不同修正", "Answer": f"Yes: {patch_operators}"},
        {"Question": "修正后能不能通过验证", "Answer": f"Yes: A2 pass {multitask['a2_pass_count']} / {multitask['case_count']}"},
        {"Question": "过程能不能记录、比较、复现、展示", "Answer": "Yes: each case has inputs, attempts, verifier feedback, patch plan, skills, trajectory"},
    ])}
  </section>

  <section>
    <h2>多任务闭环结果</h2>
    {table(multitask_rows(multitask))}
  </section>

  <section>
    <h2>生成的 Skill</h2>
    <p>Skill manifest: <code>{html.escape(manifest["skill_name"])}</code>, version <code>{html.escape(manifest["version"])}</code></p>
    <p>Included capabilities: {html.escape(capabilities)}</p>
    {table(value_rows)}
  </section>

  <section>
    <h2>最终输出摘要</h2>
    {table(findings)}
  </section>

  <section>
    <h2>评审入口</h2>
    <ul>{artifact_links}</ul>
    <p>页面只放结论和入口；完整证据链在 artifact 文件中，包括输入、A0/A1/A2 输出、verifier feedback、patch plan、Skill v1/v2 和 trajectory。</p>
  </section>
</main>
</body>
</html>
"""


def main() -> int:
    ensure_multitask_artifacts()
    run = build_run(DEFAULT_SCENARIO, "offline")
    run_dir = Path(run["session_dir"])

    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True)
    copy_tree(run_dir, OUT_DIR / "artifacts")
    copy_tree(MULTITASK_DIR, OUT_DIR / "multitask")
    if WSL_REAL_TASK_DIR.exists():
        copy_tree(WSL_REAL_TASK_DIR, OUT_DIR / "wsl_real_task")
    if NON_ORACLE_LOCAL_DIR.exists():
        copy_tree(NON_ORACLE_LOCAL_DIR, OUT_DIR / "non_oracle_local_agent")
    if LIVE_LLM_DIR.exists():
        copy_tree(LIVE_LLM_DIR, OUT_DIR / "live_llm_upload")
    if LIVE_LLM_LOOP_DIR.exists():
        copy_tree(LIVE_LLM_LOOP_DIR, OUT_DIR / "live_llm_repair_loop")
    if LIVE_LLM_DATA_QUALITY_LOOP_DIR.exists():
        copy_tree(LIVE_LLM_DATA_QUALITY_LOOP_DIR, OUT_DIR / "live_llm_repair_loop_data_quality")
    if LIVE_LLM_CONFIG_DIR.exists():
        copy_tree(LIVE_LLM_CONFIG_DIR, OUT_DIR / "live_llm_config_security")
    if LIVE_LLM_CONFIG_LOOP_DIR.exists():
        copy_tree(LIVE_LLM_CONFIG_LOOP_DIR, OUT_DIR / "live_llm_repair_loop_config_security")
    if LIVE_LLM_API_DIR.exists():
        copy_tree(LIVE_LLM_API_DIR, OUT_DIR / "live_llm_api_review")
    if LIVE_LLM_API_LOOP_DIR.exists():
        copy_tree(LIVE_LLM_API_LOOP_DIR, OUT_DIR / "live_llm_repair_loop_api_review")
    if HARBOR_NON_ORACLE_DIR.exists():
        copy_tree(HARBOR_NON_ORACLE_DIR, OUT_DIR / "harbor_non_oracle_upload")
    if HARBOR_NON_ORACLE_CLI_DIR.exists():
        copy_tree(HARBOR_NON_ORACLE_CLI_DIR, OUT_DIR / "harbor_non_oracle_cli_upload")
    if HARBOR_NON_ORACLE_REPAIR_LOOP_DIR.exists():
        copy_tree(HARBOR_NON_ORACLE_REPAIR_LOOP_DIR, OUT_DIR / "harbor_non_oracle_repair_loop_upload")
    if HARBOR_LLM_DIR.exists():
        copy_tree(HARBOR_LLM_DIR, OUT_DIR / "harbor_llm_upload")
    if HARBOR_LLM_REPAIR_LOOP_DIR.exists():
        copy_tree(HARBOR_LLM_REPAIR_LOOP_DIR, OUT_DIR / "harbor_llm_repair_loop_upload")
    if HARBOR_LLM_CONFIG_LOOP_DIR.exists():
        copy_tree(HARBOR_LLM_CONFIG_LOOP_DIR, OUT_DIR / "harbor_llm_repair_loop_config")
    if HARBOR_LIVE_SKELETON_DIR.exists():
        copy_tree(HARBOR_LIVE_SKELETON_DIR, OUT_DIR / "harbor_live_skeleton_upload")
    if SYSTEM_ACCEPTANCE_DIR.exists():
        copy_tree(SYSTEM_ACCEPTANCE_DIR, OUT_DIR / "system_acceptance")
    if VALIDATION_DIR.exists():
        copy_tree(VALIDATION_DIR, OUT_DIR / "validation")
    if SKILL_LIFECYCLE_EVIDENCE_DIR.exists():
        copy_tree(SKILL_LIFECYCLE_EVIDENCE_DIR, OUT_DIR / "skill_lifecycle_evidence")
    if INSTALLED_SKILLS_DIR.exists():
        copy_tree(INSTALLED_SKILLS_DIR, OUT_DIR / "installed_skills")
    if REVIEWER_READINESS_DIR.exists():
        copy_tree(REVIEWER_READINESS_DIR, OUT_DIR / "reviewer_readiness")
    if DEPLOYABLE_CODEX_SKILL_DIR.exists():
        copy_tree(DEPLOYABLE_CODEX_SKILL_DIR, OUT_DIR / "deployable_codex_skill")
    if SKILL_EVOLUTION_LAB_DIR.exists():
        copy_tree(SKILL_EVOLUTION_LAB_DIR, OUT_DIR / "skill_evolution_lab")
    if EXTERNAL_SECURITY_VALIDATION_DIR.exists():
        copy_tree(EXTERNAL_SECURITY_VALIDATION_DIR, OUT_DIR / "external_security_validation")
    if SCREENSHOT_DIR.exists():
        copy_tree(SCREENSHOT_DIR, OUT_DIR / "screenshots")

    real_agent_dir = ROOT / "runs" / "real_agent_loop_streamlit"
    if not real_agent_dir.exists():
        real_agent_dir = ROOT / "runs" / "real_agent_loop_rightcode"
    if real_agent_dir.exists():
        copy_tree(real_agent_dir, OUT_DIR / "real_agent")

    docs_out = OUT_DIR / "docs"
    docs_out.mkdir()
    for doc in (
        ROOT / "docs" / "review" / "implementation_borrowing_from_spark_colleague.md",
        ROOT / "docs" / "review" / "IMPLEMENTATION_BRIEF.md",
        ROOT / "docs" / "review" / "REVIEWER_GUIDE.md",
        ROOT / "docs" / "WSL2_SPARK_BACKEND.md",
        ROOT / "docs" / "CLAIM_BOUNDARY.md",
        ROOT / "docs" / "PROJECT_STRUCTURE.md",
        ROOT / "docs" / "QUICKSTART.md",
        ROOT / "docs" / "TRACE_VISUALIZATION_DESIGN.md",
    ):
        if doc.exists():
            shutil.copy2(doc, docs_out / doc.name)
    reports_out = OUT_DIR / "reports"
    reports_out.mkdir()
    for report in (
        "MORNING_STATUS_0800.md",
        "OVERNIGHT_RUN_LOG.md",
        "AUTONOMOUS_SELF_ASSESSMENT.md",
        "BACKEND_MATURITY_STATUS.md",
        "CROSS_TASK_GENERALIZATION_STATUS.md",
        "ALGORITHM_VALIDATION_STATUS.md",
        "FEEDBACK_TAXONOMY_STATUS.md",
        "TRACE_OBSERVABILITY_STATUS.md",
        "VULNERABILITY_SKILL_PRODUCT_ANALYSIS.md",
        "WSL_HARBOR_STATUS.md",
        "GENERALIZATION_AUDIT.md",
        "NEGATIVE_CONTROL_STATUS.md",
        "LOCAL_AGENT_AUDIT.md",
        "ABLATION_AUDIT.md",
        "NON_ORACLE_LOCAL_AGENT_STATUS.md",
        "HARBOR_NON_ORACLE_STATUS.md",
        "HARBOR_LLM_REPAIR_LOOP_AUDIT.md",
        "HARBOR_LLM_REPEATABILITY_STATUS.md",
        "LLM_BACKEND_STATUS.md",
        "REMAINING_HARDCODE_STATUS.md",
        "SYSTEM_ARCHITECTURE_AUDIT.md",
        "MODULE_DEPENDENCY_MAP.md",
        "SKILL_PACKAGE_DESIGN_AUDIT.md",
        "REPOSITORY_OPEN_SOURCE_READINESS.md",
        "METHOD_VALIDITY_AUDIT.md",
        "VERIFIER_GATE_LIMITATION_AUDIT.md",
        "SKILL_REVISION_VALIDITY_METRICS.md",
        "SKILL_REVISION_VALIDITY_CARD_STATUS.md",
        "SKILL_QUALIFICATION_CARD_STATUS.md",
        "PROMOTION_MECHANISM_EXPLORATION.md",
        "PROMOTION_MECHANISM_CHALLENGE_SET_STATUS.md",
        "ARTIFACT_BACKED_PROMOTION_CHALLENGE_SET_STATUS.md",
        "PROMOTION_MECHANISM_FAIRNESS_AUDIT.md",
        "QUALIFICATION_GUIDED_SKILL_EVOLUTION.md",
        "SKILL_QUALIFICATION_CARD_SCHEMA.md",
        "FAILURE_ORIGIN_TAXONOMY.md",
        "QGSE_FAILURE_CASE_STUDY_CONFIG_API.md",
        "METAMORPHIC_VERIFIER_STRESS_PLAN.md",
        "METAMORPHIC_STRESS_STATUS.md",
        "AGENT_LEVEL_METAMORPHIC_STRESS_STATUS.md",
        "LIVE_LLM_AGENT_LEVEL_METAMORPHIC_STRESS_STATUS.md",
        "SKILL_LIFECYCLE_EVIDENCE_STATUS.md",
        "SKILL_INSTALLATION_STATUS.md",
        "REVIEWER_READINESS_STATUS.md",
        "SPARK_COLLEAGUE_SKILLGEN_SKILLGRAD_GAP_LEDGER.md",
        "ALGORITHM_GAP_AND_NEXT_STEPS.md",
        "BORROWING_AND_LICENSE_AUDIT.md",
        "TASKCASE_SCHEMA_UNIFICATION_STATUS.md",
        "BACKEND_RUNNER_INTEGRATION_STATUS.md",
        "AGENT_RUNNER_HARBOR_BOUNDARY.md",
        "HARBOR_RUNNER_INTEGRATION_STATUS.md",
        "LIVE_LLM_DATA_QUALITY_STATUS.md",
        "LIVE_LLM_CONFIG_STATUS.md",
        "LIVE_LLM_API_REVIEW_STATUS.md",
        "LIVE_LLM_LOCAL_MULTITASK_STATUS.md",
        "LEAKAGE_AND_VERIFIER_VALIDITY_AUDIT.md",
        "VERIFIER_STRESS_STATUS.md",
        "REPAIR_POLICY_OPERATOR_ALIGNMENT_STATUS.md",
        "MORNING_HANDOFF_0800.md",
        "CURRENT_SYSTEM_SNAPSHOT.md",
        "CODEX_SELF_ASSESSMENT_0800.md",
        "DEPLOYABLE_SKILL_EVOLUTION_STATUS.md",
    ):
        src = ROOT / "reports" / report
        if src.exists():
            shutil.copy2(src, reports_out / report)
    shutil.copy2(ROOT / "README_DEMO.md", OUT_DIR / "README_DEMO.md")
    (OUT_DIR / "index.html").write_text(build_index(run_dir), encoding="utf-8", newline="\n")

    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    shutil.make_archive(str(ZIP_PATH.with_suffix("")), "zip", OUT_DIR)
    shutil.copy2(ZIP_PATH, EXPORT_COMPAT_PATH)
    print(json.dumps({"review_package": str(OUT_DIR), "zip": str(ZIP_PATH), "index": str(OUT_DIR / "index.html")}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
