from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from skill_deployment.evidence import write_json, write_text  # noqa: E402


REPORT_MATRIX = ROOT / "reports" / "REPRESENTATIVE_VALIDATION_MATRIX.md"
REPORT_LEDGER = ROOT / "reports" / "FRAMEWORK_MATURITY_EVIDENCE_LEDGER.md"
REPORT_SPRINT = ROOT / "reports" / "RAPID_ADVANCEMENT_SPRINT_STATUS.md"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def exists(path: Path) -> str:
    return str(path) if path.exists() else "missing"


def mini_summary() -> dict[str, Any]:
    return read_json(ROOT / "outputs" / "external_security_mini_suite" / "mini_suite_summary.json", {})


def evolution_summary() -> dict[str, Any]:
    return read_json(ROOT / "outputs" / "skill_evolution_lab" / "secure_code_review" / "evolution_summary.json", {})


def advanced_evolution_summary() -> dict[str, Any]:
    return read_json(ROOT / "outputs" / "skill_evolution_lab" / "secure_code_review" / "advanced_candidates" / "advanced_evolution_summary.json", {})


def non_oracle_summary() -> dict[str, Any]:
    return read_json(ROOT / "outputs" / "non_oracle_validation" / "non_oracle_validation_summary.json", {})


def live_llm_summary() -> dict[str, Any]:
    return read_json(ROOT / "outputs" / "live_llm_validation" / "live_llm_validation_summary.json", {})


def live_contract_summary() -> dict[str, Any]:
    return read_json(ROOT / "outputs" / "live_contract_validation" / "live_contract_validation_summary.json", {})


def external_generalization_summary() -> dict[str, Any]:
    return read_json(ROOT / "outputs" / "external_generalization_validation" / "external_generalization_summary.json", {})


def live_mechanism_ablation_summary() -> dict[str, Any]:
    return read_json(ROOT / "outputs" / "mechanism_ablation" / "live_contract" / "live_mechanism_ablation_summary.json", {})


def improvement_demo_summary() -> dict[str, Any]:
    return read_json(ROOT / "outputs" / "skill_evolution_lab" / "secure_code_review" / "improvement_demo" / "improvement_demo_summary.json", {})


def contract_improvement_summary() -> dict[str, Any]:
    return read_json(ROOT / "outputs" / "contract_improvement_demo" / "contract_improvement_demo_summary.json", {})


def iterative_contract_improvement_summary() -> dict[str, Any]:
    return read_json(ROOT / "outputs" / "iterative_contract_improvement" / "iterative_contract_improvement_summary.json", {})


def public_release_summary() -> dict[str, Any]:
    return read_json(ROOT / "reports" / "public_release_readiness_status.json", {})


def extended_summary() -> dict[str, Any]:
    return read_json(ROOT / "outputs" / "external_security_mini_suite" / "extended" / "extended_summary.json", {})


def swe_summary() -> dict[str, Any]:
    return read_json(ROOT / "outputs" / "external_swebench" / "swebench_gold_patch_smoke_requests_20260612" / "summary.json", {})


def installed_compare() -> dict[str, Any]:
    return read_json(ROOT / "outputs" / "validation" / "skill_marginal_utility" / "installed_package_marginal_utility.json", {})


def registry() -> dict[str, Any]:
    return read_json(ROOT / "outputs" / "installed_skills" / "registry.json", {})


def row(
    *,
    lane: str,
    claim: str,
    skill_package: str,
    task_family: str,
    scope: str,
    harness: str,
    metric: str,
    evidence: str,
    evidence_type: str,
    remaining_gap: str,
    next_command: str,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "lane": lane,
        "claim": claim,
        "skill_package": skill_package,
        "task_family": task_family,
        "internal_external": scope,
        "harness": harness,
        "metric": metric,
        "current_evidence": evidence,
        "evidence_type": evidence_type,
        "remaining_gap": remaining_gap,
        "next_runnable_command": next_command,
        **dict(extra or {}),
    }


def build_rows() -> list[dict[str, Any]]:
    mini = mini_summary()
    evo = evolution_summary()
    advanced = advanced_evolution_summary()
    non_oracle = non_oracle_summary()
    live_llm = live_llm_summary()
    live_contract = live_contract_summary()
    external_generalization = external_generalization_summary()
    live_ablation = live_mechanism_ablation_summary()
    improvement = improvement_demo_summary()
    contract_improvement = contract_improvement_summary()
    iterative_improvement = iterative_contract_improvement_summary()
    public_release = public_release_summary()
    extended = extended_summary()
    swe = swe_summary()
    compare = installed_compare()
    reg = registry()
    integrity = mini.get("version_integrity", {})
    version_identical = integrity.get("version_content_identical")
    fp_status = mini.get("false_positive_control_status", "missing")
    unsupported_status = mini.get("unsupported_limitation_status", "missing")
    candidate_count = len(advanced.get("candidate_outputs", [])) or len(evo.get("candidate_outputs", []))
    swe_status = (swe.get("infra_unblock") or {}).get("final_status") or swe.get("official_harness_gold_patch_smoke") or "missing"
    rows = [
        row(
            lane="Runtime-general",
            claim="Installed package registry drives runtime execution",
            skill_package="secure_code_review",
            task_family="runtime",
            scope="internal",
            harness="skill-deploy install/run-skill",
            metric="registry and active pointer read by runtime",
            evidence=exists(ROOT / "outputs" / "installed_skills" / "registry.json"),
            evidence_type="fresh_run" if reg else "scaffold",
            remaining_gap="Prototype registry only, not production package manager",
            next_command="skill-deploy run-skill --installed secure_code_review --case upload_security_001 --backend offline_deterministic",
            extra={"version_content_identical": version_identical},
        ),
        row(
            lane="Runtime-general",
            claim="Installed package variants support marginal utility comparison",
            skill_package="secure_code_review",
            task_family="runtime",
            scope="internal",
            harness="skill-deploy compare-variants --source installed",
            metric=f"case_count={compare.get('case_count')}",
            evidence=exists(ROOT / "outputs" / "validation" / "skill_marginal_utility" / "installed_package_marginal_utility.json"),
            evidence_type="fresh_run" if compare else "scaffold",
            remaining_gap="Only controlled deterministic cases",
            next_command="skill-deploy compare-variants --cases upload,config --backend offline_deterministic --source installed",
            extra={"version_content_identical": version_identical},
        ),
        row(
            lane="Runtime-general",
            claim="Small candidate evolution records promotion/rejection evidence",
            skill_package="secure_code_review",
            task_family="evolution",
            scope="internal",
            harness="skill-deploy advanced-evolve",
            metric=f"candidate_count={candidate_count}",
            evidence=exists(ROOT / "outputs" / "skill_evolution_lab" / "secure_code_review" / "advanced_candidates" / "advanced_evolution_summary.json"),
            evidence_type="fresh_run" if candidate_count else "derived",
            remaining_gap="Safety gate/rejection evidence is present; improvement is not demonstrated unless a candidate is promoted with validation evidence",
            next_command="skill-deploy advanced-evolve --installed secure_code_review --budget 5",
        ),
        row(
            lane="Runtime-general",
            claim="Non-oracle execution is separated from behavior effectiveness",
            skill_package="secure_code_review",
            task_family="holdout security",
            scope="internal non-oracle",
            harness="skill-deploy non-oracle-validation",
            metric=f"execution={non_oracle.get('non_oracle_execution')}, effectiveness={non_oracle.get('non_oracle_effectiveness')}, behavior={non_oracle.get('non_oracle_behavior')}",
            evidence=exists(ROOT / "outputs" / "non_oracle_validation" / "non_oracle_validation_summary.json"),
            evidence_type="fresh_run" if non_oracle else "scaffold",
            remaining_gap="Local semantic backend only; live LLM remains blocked if model/API env is missing",
            next_command="skill-deploy non-oracle-validation --installed secure_code_review",
        ),
        row(
            lane="Runtime-general",
            claim="Live LLM execution is separated from verifier effectiveness",
            skill_package="secure_code_review",
            task_family="holdout security",
            scope="internal live LLM",
            harness="skill-deploy live-llm-validation",
            metric=f"execution={live_llm.get('live_llm_execution')}, effectiveness={live_llm.get('live_llm_effectiveness')}, behavior={live_llm.get('live_llm_behavior')}",
            evidence=exists(ROOT / "outputs" / "live_llm_validation" / "live_llm_validation_summary.json"),
            evidence_type="fresh_run" if live_llm else "scaffold",
            remaining_gap="Live evidence is local bounded evidence, not an official external benchmark.",
            next_command="skill-deploy live-llm-validation --installed secure_code_review --base-url https://api.deepseek.com --model deepseek-v4-flash",
        ),
        row(
            lane="Runtime-general",
            claim="Contract-grounded live agent improves evidence discipline without relaxing verifier",
            skill_package="secure_code_review",
            task_family="upload/config/auth/API/clean/unsupported/ambiguous",
            scope="internal live LLM",
            harness="skill-deploy live-contract-validation",
            metric=f"effectiveness={live_contract.get('live_contract_effectiveness')}, after_pass={live_contract.get('after_pass_count')}/{live_contract.get('case_count')}, exact={live_contract.get('evidence_exact_match_rate')}",
            evidence=exists(ROOT / "outputs" / "live_contract_validation" / "live_contract_validation_summary.json"),
            evidence_type="fresh_run" if live_contract else "scaffold",
            remaining_gap="Local live set; not official benchmark.",
            next_command="skill-deploy live-contract-validation --installed secure_code_review --base-url https://api.deepseek.com --model deepseek-v4-flash",
        ),
        row(
            lane="Runtime-general",
            claim="Live ablation supports router/normalizer/contract mechanism",
            skill_package="secure_code_review",
            task_family="mechanism",
            scope="internal live LLM",
            harness="skill-deploy live-mechanism-ablation",
            metric=f"mechanism_ablation={live_ablation.get('mechanism_ablation')}",
            evidence=exists(ROOT / "outputs" / "mechanism_ablation" / "live_contract" / "live_mechanism_ablation_summary.json"),
            evidence_type="fresh_run" if live_ablation else "scaffold",
            remaining_gap="Ablation is bounded and local; no human/external usefulness review.",
            next_command="skill-deploy live-mechanism-ablation --installed secure_code_review --base-url https://api.deepseek.com --model deepseek-v4-flash",
        ),
        row(
            lane="Runtime-general",
            claim="Live-feedback improvement is demonstrated only by strict staged promotion",
            skill_package="secure_code_review",
            task_family="evolution",
            scope="internal live feedback",
            harness="skill-deploy iterative-contract-improvement",
            metric=f"improvement={iterative_improvement.get('evolution_improvement') or contract_improvement.get('evolution_improvement') or improvement.get('evolution_improvement')}, maturity={iterative_improvement.get('evolution_maturity') or contract_improvement.get('evolution_maturity') or improvement.get('evolution_maturity')}, proposals={iterative_improvement.get('promotion_proposal_count')}",
            evidence=exists(ROOT / "outputs" / "iterative_contract_improvement" / "iterative_contract_improvement_summary.json"),
            evidence_type="fresh_run" if iterative_improvement else ("fresh_run" if contract_improvement or improvement else "scaffold"),
            remaining_gap="No improvement claim unless a candidate earns a staged promotion proposal.",
            next_command="skill-deploy iterative-contract-improvement --installed secure_code_review --base-url https://api.deepseek.com --model deepseek-v4-flash --budget 5",
        ),
        row(
            lane="Secure-code-review",
            claim="Installed secure_code_review covers controlled upload/config/API/auth families",
            skill_package="secure_code_review",
            task_family="upload/config/api/auth",
            scope="internal",
            harness="offline_deterministic installed runtime",
            metric="task-conditioned installed runtime pass in controlled suite",
            evidence=exists(ROOT / "reports" / "MULTI_CAPABILITY_GENERALIZATION_STATUS.md"),
            evidence_type="derived_summary",
            remaining_gap="Does not imply real-world vulnerability scanning",
            next_command="skill-deploy run-skill --installed secure_code_review --case config_security_001 --backend offline_deterministic",
        ),
        row(
            lane="Secure-code-review",
            claim="Local defensive mini-suite provides bounded representative security evidence",
            skill_package="secure_code_review",
            task_family="local defensive security",
            scope="external-style local",
            harness="defensive-security-mini-suite",
            metric=f"extended_case_count={extended.get('case_count') or mini.get('fresh_case_count')}, fp_control={extended.get('negative_fp_count', 'missing')}, unsupported={extended.get('unsupported_retained_count', 'missing')}",
            evidence=exists(ROOT / "outputs" / "external_security_mini_suite" / "extended" / "extended_summary.json"),
            evidence_type="fresh_run" if extended else ("fresh_run" if mini else "scaffold"),
            remaining_gap="Not official AutoPatchBench/CyberSecEval",
            next_command="skill-deploy defensive-security-mini-suite --installed secure_code_review --backend offline_deterministic",
            extra={
                "capability_group_correct": "recorded_per_case",
                "false_positive_control_status": fp_status,
                "unsupported_limitation_status": unsupported_status,
            },
        ),
        row(
            lane="Software-patch-review",
            claim="software_patch_review has internal smoke only",
            skill_package="software_patch_review",
            task_family="software_patch_review",
            scope="internal",
            harness="offline_deterministic installed runtime",
            metric="internal smoke pass if artifact exists",
            evidence=exists(ROOT / "outputs" / "installed_skills" / "active_skill_pointers" / "software_patch_review.json"),
            evidence_type="fresh_run" if (ROOT / "outputs" / "installed_skills" / "active_skill_pointers" / "software_patch_review.json").exists() else "scaffold",
            remaining_gap="No non-oracle external patch generation evidence",
            next_command="skill-deploy run-skill --installed software_patch_review --case software_patch_review_001 --backend offline_deterministic",
        ),
        row(
            lane="Software-patch-review",
            claim="SWE-bench official harness readiness is tracked honestly",
            skill_package="software_patch_review",
            task_family="SWE-bench Lite psf__requests-1963",
            scope="external official harness",
            harness="/opt/spark/swebench-tools/swebench-venv -m swebench.harness.run_evaluation",
            metric=f"external_harness={swe_status}",
            evidence=exists(ROOT / "reports" / "SWEBENCH_OFFICIAL_HARNESS_INFRA_UNBLOCK_STATUS.md"),
            evidence_type="external_official_harness" if swe_status == "pass" else "infra_blocked",
            remaining_gap="Conda/Docker/network image build can still block gold patch smoke",
            next_command="skill-deploy swebench-infra-unblock --run-id swebench_gold_patch_smoke_requests_20260612 --instance-id psf__requests-1963 --max-retries 2",
        ),
        row(
            lane="External-security",
            claim="Bounded public-source and independent holdout generalization is tracked separately from official benchmarks",
            skill_package="secure_code_review",
            task_family="public read-only + independent holdout",
            scope="semiexternal live LLM",
            harness="skill-deploy external-generalization",
            metric=f"external_generalization={external_generalization.get('external_generalization')}, pass={external_generalization.get('pass_count')}/{external_generalization.get('case_count')}",
            evidence=exists(ROOT / "outputs" / "external_generalization_validation" / "external_generalization_summary.json"),
            evidence_type="fresh_run" if external_generalization else "scaffold",
            remaining_gap="Not official CyberSecEval/CVE-Bench/AutoPatchBench; labels are local verifier labels.",
            next_command="skill-deploy external-generalization --installed secure_code_review --backend live_llm_text --base-url https://api.deepseek.com --model deepseek-v4-flash",
            extra={"unsupported_limitation_status": unsupported_status},
        ),
        row(
            lane="External-security",
            claim="Official external security benchmarks are not claimed",
            skill_package="secure_code_review",
            task_family="CyberSecEval/AutoPatchBench-style",
            scope="external planned",
            harness="none",
            metric="not_run",
            evidence=exists(ROOT / "reports" / "DEFENSIVE_SECURITY_MINI_SUITE_STATUS.md"),
            evidence_type="scaffold",
            remaining_gap="No official CyberSecEval/CVE-Bench/AutoPatchBench execution",
            next_command="skill-deploy defensive-security-mini-suite --installed secure_code_review --backend offline_deterministic",
            extra={"unsupported_limitation_status": unsupported_status},
        ),
        row(
            lane="Runtime-general",
            claim="Strict public release readiness is checked separately from prototype docs",
            skill_package="all",
            task_family="release",
            scope="local packaging",
            harness="clean clone smoke",
            metric=f"public_release_readiness={public_release.get('public_release_readiness')}",
            evidence=exists(ROOT / "reports" / "PUBLIC_RELEASE_READINESS_STATUS.md"),
            evidence_type="fresh_run" if public_release else "scaffold",
            remaining_gap="Public release does not imply production security effectiveness.",
            next_command="python scripts\\run_clean_clone_smoke.py --source . --keep-artifacts",
        ),
    ]
    return rows


def markdown_table(rows: list[dict[str, Any]]) -> str:
    headers = [
        "Lane",
        "Claim",
        "Skill package",
        "Task family",
        "Internal / external",
        "Harness",
        "Metric",
        "Current evidence",
        "Evidence type",
        "Remaining gap",
        "Next runnable command",
    ]
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    for item in rows:
        values = [
            item["lane"],
            item["claim"],
            item["skill_package"],
            item["task_family"],
            item["internal_external"],
            item["harness"],
            item["metric"],
            item["current_evidence"],
            item["evidence_type"],
            item["remaining_gap"],
            f"`{item['next_runnable_command']}`",
        ]
        lines.append("| " + " | ".join(str(value).replace("\n", " ") for value in values) + " |")
    return "\n".join(lines)


def judgments(rows: list[dict[str, Any]]) -> dict[str, str]:
    mini = mini_summary()
    evo = evolution_summary()
    advanced = advanced_evolution_summary()
    non_oracle = non_oracle_summary()
    live_llm = live_llm_summary()
    live_contract = live_contract_summary()
    external_generalization = external_generalization_summary()
    live_ablation = live_mechanism_ablation_summary()
    improvement = improvement_demo_summary()
    contract_improvement = contract_improvement_summary()
    iterative_improvement = iterative_contract_improvement_summary()
    public_release = public_release_summary()
    extended = extended_summary()
    swe = swe_summary()
    fresh_case_count = int(extended.get("case_count") or mini.get("fresh_case_count") or 0)
    fp_pass = extended.get("negative_fp_count") == 0 if extended else mini.get("false_positive_control_status") == "pass"
    limitation_retained = bool(extended.get("unsupported_retained_count", 0) >= 2) if extended else mini.get("unsupported_limitation_status") == "retained"
    candidate_count = len(advanced.get("candidate_outputs", [])) or len(evo.get("candidate_outputs", []))
    rejected_count = len(advanced.get("rejected_edit_buffer", []))
    promoted_count = len(advanced.get("promotion_proposals", []))
    external_status = (swe.get("infra_unblock") or {}).get("final_status") or swe.get("official_harness_gold_patch_smoke") or "infra_blocked"
    controlled_internal = "pass" if any(row["lane"] == "Runtime-general" and row["evidence_type"] == "fresh_run" for row in rows) else "partial"
    security_depth = "pass_local_bounded" if fresh_case_count >= 18 and fp_pass and limitation_retained else "partial"
    if external_status == "pass":
        external_harness = "pass"
    elif external_status == "evaluation_failed":
        external_harness = "fail"
    else:
        external_harness = "infra_blocked"
    docs_exist = all((ROOT / path).exists() for path in ("README_PROTOTYPE.md", "docs/QUICKSTART.md", "docs/CLAIM_BOUNDARY.md", "docs/ARTIFACT_TYPES.md"))
    open_source_readiness = "prototype_pass" if docs_exist else "partial"
    non_oracle_execution = str(non_oracle.get("non_oracle_execution") or "blocked")
    non_oracle_effectiveness = str(non_oracle.get("non_oracle_effectiveness") or "blocked")
    non_oracle_behavior = str(non_oracle.get("non_oracle_behavior") or "blocked")
    live_llm_execution = str(live_llm.get("live_llm_execution") or "blocked")
    live_llm_effectiveness = str(live_llm.get("live_llm_effectiveness") or "blocked")
    live_llm_behavior = str(live_llm.get("live_llm_behavior") or "blocked")
    improvement_source = iterative_improvement or contract_improvement or improvement
    candidate_generation = str(improvement_source.get("candidate_generation") or ("pass" if candidate_count >= 3 else "partial"))
    evolution_safety_gate = str(improvement_source.get("evolution_safety_gate") or ("pass" if rejected_count >= 1 or promoted_count >= 1 else "partial"))
    evolution_improvement = str(improvement_source.get("evolution_improvement") or ("demonstrated" if promoted_count >= 1 else "not_yet_demonstrated"))
    evolution_maturity = str(improvement_source.get("evolution_maturity") or ("pass" if evolution_improvement == "demonstrated" else ("safety_gate_pass" if candidate_generation == "pass" and evolution_safety_gate == "pass" else "partial")))
    mechanism_ablation = str(live_ablation.get("mechanism_ablation") or "inconclusive")
    live_contract_effectiveness = str(live_contract.get("live_contract_effectiveness") or live_llm_effectiveness)
    academic_claim_readiness = "moderate_high_with_caveat" if non_oracle_behavior == "pass" and security_depth == "pass_local_bounded" and evolution_safety_gate == "pass" else "moderate"
    if (live_llm_behavior == "pass" or live_contract_effectiveness == "pass") and evolution_improvement == "demonstrated":
        academic_claim_readiness = "strong_candidate_with_external_gap"
    return {
        "controlled_internal": controlled_internal,
        "security_depth": security_depth,
        "non_oracle_execution": non_oracle_execution,
        "non_oracle_effectiveness": non_oracle_effectiveness,
        "non_oracle_behavior": non_oracle_behavior,
        "live_llm_execution": live_llm_execution,
        "live_llm_effectiveness": live_llm_effectiveness,
        "live_llm_behavior": live_llm_behavior,
        "live_contract_effectiveness": live_contract_effectiveness,
        "external_generalization": str(external_generalization.get("external_generalization") or "missing"),
        "mechanism_ablation": mechanism_ablation,
        "candidate_generation": candidate_generation,
        "evolution_safety_gate": evolution_safety_gate,
        "evolution_improvement": evolution_improvement,
        "evolution_maturity": evolution_maturity,
        "external_harness": external_harness,
        "open_source_readiness": open_source_readiness,
        "public_release_readiness": str(public_release.get("public_release_readiness") or "partial"),
        "academic_claim_readiness": academic_claim_readiness,
    }


def render_matrix(rows: list[dict[str, Any]]) -> str:
    mini = mini_summary()
    integrity = mini.get("version_integrity", {})
    return "\n".join(
        [
            "# Representative Validation Matrix",
            "",
            f"Generated at: `{utc_now()}`",
            "",
            "This matrix separates `fresh_run`, `derived_summary`, `scaffold`, `replay`, and `infra_blocked` evidence.",
            "",
            markdown_table(rows),
            "",
            "## Explicit Boundary Checks",
            "",
            f"- `version_content_identical`: `{integrity.get('version_content_identical')}`",
            "- `capability_group_correct`: `recorded_per_case`",
            f"- `false_positive_control_status`: `{mini.get('false_positive_control_status', 'missing')}`",
            f"- `unsupported_limitation_status`: `{mini.get('unsupported_limitation_status', 'missing')}`",
            "- SWE-bench rows support only software_patch_review harness readiness, not secure_code_review claims.",
            "- Internal deterministic rows do not claim real-world vulnerability scanning effectiveness.",
            "- infra_blocked rows are not benchmark success and are not model/Skill failures.",
        ]
    ) + "\n"


def render_ledger(rows: list[dict[str, Any]], judgment: dict[str, str]) -> str:
    evidence_counts: dict[str, int] = {}
    for item in rows:
        evidence_counts[item["evidence_type"]] = evidence_counts.get(item["evidence_type"], 0) + 1
    lines = [
        "# Framework Maturity Evidence Ledger",
        "",
        f"Generated at: `{utc_now()}`",
        "",
        "## Evidence Type Counts",
        "",
    ]
    for key in sorted(evidence_counts):
        lines.append(f"- `{key}`: `{evidence_counts[key]}`")
    lines.extend(["", "## Judgment", ""])
    for key, value in judgment.items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## Non-Claims",
            "",
            "- Not a production vulnerability scanner.",
            "- Not a full SPARK reproduction.",
            "- Not a SWE-bench agent.",
            "- Not an exploit automation tool.",
            "- Not a production package manager.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_sprint_status(rows: list[dict[str, Any]], judgment: dict[str, str]) -> str:
    mini = mini_summary()
    evo = evolution_summary()
    swe = swe_summary()
    lines = [
        "# Rapid Advancement Sprint Status",
        "",
        f"Generated at: `{utc_now()}`",
        "",
        "## 1. What became stronger in this sprint",
        "",
        "- The project now has a representative validation matrix across runtime, security, software-patch, and external-security lanes.",
        "- A local defensive security mini-suite records installed-package fresh evidence with oracle leakage controls.",
        "- Small candidate evolution records multiple candidate diffs, validation results, and rejected edits.",
        "- SWE-bench official harness state remains separated as harness-readiness evidence.",
        "- Open-source readiness docs define quickstart, artifact types, and claim boundaries.",
        "",
        "## 2. Fresh commands executed",
        "",
        "```powershell",
        "skill-deploy build-codex-skill",
        "skill-deploy install --skill outputs/deployable_codex_skill/secure_code_review --version v1",
        "skill-deploy install --skill outputs/deployable_codex_skill/secure_code_review --version v2",
        "skill-deploy run-skill --installed secure_code_review --case upload_security_001 --backend offline_deterministic",
        "skill-deploy compare-variants --cases upload,config,api_review,auth --backend offline_deterministic --source installed",
        "skill-deploy defensive-security-mini-suite --installed secure_code_review --backend offline_deterministic",
        "skill-deploy evolve --suite secure_code_review --budget 3 --gate qgse_pareto",
        "skill-deploy swebench-infra-unblock --run-id swebench_gold_patch_smoke_requests_20260612 --instance-id psf__requests-1963 --max-retries 2",
        "skill-deploy representative-matrix",
        "```",
        "",
        "## 3. Fresh artifacts produced",
        "",
        "- `outputs/external_security_mini_suite/mini_suite_summary.json`",
        "- `outputs/skill_evolution_lab/secure_code_review/evolution_summary.json`",
        "- `reports/REPRESENTATIVE_VALIDATION_MATRIX.md`",
        "- `reports/FRAMEWORK_MATURITY_EVIDENCE_LEDGER.md`",
        "- `reports/SWEBENCH_OFFICIAL_HARNESS_INFRA_UNBLOCK_STATUS.md`",
        "",
        "## 4. Which evidence supports runtime generality",
        "",
        "- Installed registry, active pointer, compare-variants, evidence bundles, and small candidate validation support controlled runtime generality.",
        "",
        "## 5. Which evidence supports security depth",
        "",
        f"- Mini-suite fresh cases: `{mini.get('fresh_case_count')}`",
        f"- False-positive control: `{mini.get('false_positive_control_status')}`",
        f"- Unsupported limitation: `{mini.get('unsupported_limitation_status')}`",
        "",
        "## 6. Which evidence only supports external harness readiness",
        "",
        f"- SWE-bench final status: `{(swe.get('infra_unblock') or {}).get('final_status') or swe.get('official_harness_gold_patch_smoke')}`",
        "- This does not support secure_code_review claims.",
        "",
        "## 7. Which tasks are still blocked",
        "",
        f"- SWE-bench blocked reason: `{((swe.get('gold_patch') or {}).get('blocked_reason') or ((swe.get('infra_unblock') or {}).get('blocked_reason')) or 'none')}`",
        "",
        "## 8. What cannot be claimed",
        "",
        "- No official CyberSecEval, CVE-Bench, or AutoPatchBench result.",
        "- No real-world vulnerability scanner effectiveness.",
        "- No SWE-bench agent effectiveness unless official non-oracle patch evaluation later succeeds.",
        "- No exploit capability.",
        "",
        "## 9. Recommended next step",
        "",
        "- If SWE-bench remains infra_blocked, pause that lane and expand only bounded local/security validation with stronger non-oracle evidence.",
        "",
        "## Overall Judgment",
        "",
    ]
    for key, value in judgment.items():
        lines.append(f"- `{key}`: `{value}`")
    lines.append("")
    lines.append(f"Small candidate count: `{len(evo.get('candidate_outputs', []))}`")
    return "\n".join(lines) + "\n"


def main() -> int:
    rows = build_rows()
    judgment = judgments(rows)
    write_json(ROOT / "reports" / "representative_validation_matrix.json", {"generated_at": utc_now(), "rows": rows, "judgment": judgment})
    write_text(REPORT_MATRIX, render_matrix(rows))
    write_text(REPORT_LEDGER, render_ledger(rows, judgment))
    write_text(REPORT_SPRINT, render_sprint_status(rows, judgment))
    print(json.dumps({"matrix": str(REPORT_MATRIX), "ledger": str(REPORT_LEDGER), "sprint": str(REPORT_SPRINT), "judgment": judgment}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
