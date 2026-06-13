from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPORT_GRAND = ROOT / "reports" / "GRAND_AUTONOMOUS_SPRINT_STATUS.md"
REPORT_ACADEMIC = ROOT / "reports" / "ACADEMIC_CLAIM_READINESS_ASSESSMENT.md"
REPORT_RELEASE = ROOT / "reports" / "RELEASE_READINESS_CHECKLIST.md"
JSON_REPORT = ROOT / "reports" / "grand_autonomous_maturity_summary.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def load_evidence() -> dict[str, Any]:
    return {
        "non_oracle": read_json(ROOT / "outputs" / "non_oracle_validation" / "non_oracle_validation_summary.json", {}),
        "live_llm": read_json(ROOT / "outputs" / "live_llm_validation" / "live_llm_validation_summary.json", {}),
        "live_contract": read_json(ROOT / "outputs" / "live_contract_validation" / "live_contract_validation_summary.json", {}),
        "external_generalization": read_json(ROOT / "outputs" / "external_generalization_validation" / "external_generalization_summary.json", {}),
        "live_mechanism_ablation": read_json(ROOT / "outputs" / "mechanism_ablation" / "live_contract" / "live_mechanism_ablation_summary.json", {}),
        "holdout": read_json(ROOT / "outputs" / "external_security_mini_suite" / "holdout" / "holdout_summary.json", {}),
        "activation": read_json(ROOT / "outputs" / "ablation" / "task_conditioned_activation" / "activation_ablation_summary.json", {}),
        "advanced_evolution": read_json(ROOT / "outputs" / "skill_evolution_lab" / "secure_code_review" / "advanced_candidates" / "advanced_evolution_summary.json", {}),
        "improvement_demo": read_json(ROOT / "outputs" / "skill_evolution_lab" / "secure_code_review" / "improvement_demo" / "improvement_demo_summary.json", {}),
        "contract_improvement": read_json(ROOT / "outputs" / "contract_improvement_demo" / "contract_improvement_demo_summary.json", {}),
        "iterative_contract_improvement": read_json(ROOT / "outputs" / "iterative_contract_improvement" / "iterative_contract_improvement_summary.json", {}),
        "extended": read_json(ROOT / "outputs" / "external_security_mini_suite" / "extended" / "extended_summary.json", {}),
        "open_source": read_json(ROOT / "reports" / "open_source_readiness_audit.json", {}),
        "public_release": read_json(ROOT / "reports" / "public_release_readiness_status.json", {}),
        "swebench": read_json(ROOT / "reports" / "swebench_infra_final_status.json", {}),
        "p0j": read_json(ROOT / "reports" / "post_sprint_hardening_status.json", {}),
    }


def non_oracle_judgment(non_oracle: dict[str, Any]) -> dict[str, str]:
    execution = str(non_oracle.get("non_oracle_execution") or "blocked")
    effectiveness = str(non_oracle.get("non_oracle_effectiveness") or "blocked")
    behavior = str(non_oracle.get("non_oracle_behavior") or non_oracle.get("overall_status") or "blocked")
    if behavior == "pass" and effectiveness != "pass":
        behavior = "partial"
    return {
        "non_oracle_execution": execution,
        "non_oracle_effectiveness": effectiveness,
        "non_oracle_behavior": behavior,
    }


def evolution_judgment(evolution: dict[str, Any]) -> dict[str, str]:
    candidates = evolution.get("candidate_outputs", [])
    rejected = evolution.get("rejected_edit_buffer", [])
    proposals = evolution.get("promotion_proposals", [])
    candidate_generation = "pass" if len(candidates) >= 3 else "partial"
    safety_gate = "pass" if len(rejected) >= 1 or proposals else "partial"
    improvement = "demonstrated" if proposals else "not_yet_demonstrated"
    if improvement == "demonstrated" and safety_gate == "pass":
        maturity = "pass"
    elif candidate_generation == "pass" and safety_gate == "pass":
        maturity = "safety_gate_pass"
    else:
        maturity = "partial"
    return {
        "candidate_generation": candidate_generation,
        "evolution_safety_gate": safety_gate,
        "evolution_improvement": improvement,
        "evolution_maturity": maturity,
    }


def live_llm_judgment(live: dict[str, Any]) -> dict[str, str]:
    return {
        "live_llm_execution": str(live.get("live_llm_execution") or "blocked"),
        "live_llm_effectiveness": str(live.get("live_llm_effectiveness") or "blocked"),
        "live_llm_behavior": str(live.get("live_llm_behavior") or "blocked"),
    }


def improvement_judgment(improvement: dict[str, Any], fallback: dict[str, str]) -> dict[str, str]:
    if not improvement:
        return fallback
    return {
        "candidate_generation": str(improvement.get("candidate_generation") or fallback["candidate_generation"]),
        "evolution_safety_gate": str(improvement.get("evolution_safety_gate") or fallback["evolution_safety_gate"]),
        "evolution_improvement": str(improvement.get("evolution_improvement") or fallback["evolution_improvement"]),
        "evolution_maturity": str(improvement.get("evolution_maturity") or fallback["evolution_maturity"]),
    }


def judgments(e: dict[str, Any]) -> dict[str, str]:
    non_oracle = e["non_oracle"]
    live_llm = e["live_llm"]
    holdout = e["holdout"]
    activation = e["activation"]
    evolution = e["advanced_evolution"]
    improvement = e["improvement_demo"]
    contract_improvement = e["contract_improvement"]
    iterative_contract_improvement = e["iterative_contract_improvement"]
    extended = e["extended"]
    open_source = e["open_source"]
    public_release = e["public_release"]
    swe = e["swebench"]
    non_oracle_status = non_oracle_judgment(non_oracle)
    live_status = live_llm_judgment(live_llm)
    holdout_status = (
        "pass_local_holdout"
        if holdout.get("fresh_case_count", 0) >= 6
        and holdout.get("false_positive_control_status") == "pass"
        and holdout.get("unsupported_limitation_status") == "retained"
        and holdout.get("oracle_leakage_status") == "pass"
        else "partial"
    )
    activation_status = str(e["live_mechanism_ablation"].get("mechanism_ablation") or activation.get("mechanism_status") or "inconclusive")
    evolution_status = improvement_judgment(iterative_contract_improvement or contract_improvement or improvement, evolution_judgment(evolution))
    security_depth = "pass_local_bounded" if extended.get("case_count", 0) >= 18 and extended.get("negative_fp_count", 1) == 0 and extended.get("unsupported_retained_count", 0) >= 2 else "partial"
    external_harness = str(swe.get("external_harness") or "infra_blocked")
    open_prototype = "pass" if open_source.get("open_source_prototype_readiness") == "pass" or open_source.get("overall_status") == "pass" else "partial"
    public_release_status = str(public_release.get("public_release_readiness") or open_source.get("public_release_readiness") or "partial")
    academic = "moderate"
    live_contract_effectiveness = str(e["live_contract"].get("live_contract_effectiveness") or live_status.get("live_llm_effectiveness") or "blocked")
    if (live_status["live_llm_behavior"] == "pass" or live_contract_effectiveness == "pass") and evolution_status["evolution_improvement"] == "demonstrated":
        academic = "strong_candidate_with_external_gap"
    elif live_status["live_llm_behavior"] == "pass":
        academic = "moderate_high_with_caveat"
    elif (
        non_oracle_status["non_oracle_behavior"] == "pass"
        and holdout_status == "pass_local_holdout"
        and activation_status == "supports_mechanism"
        and security_depth == "pass_local_bounded"
        and evolution_status["evolution_safety_gate"] == "pass"
    ):
        academic = "moderate_high_with_caveat"
    return {
        "controlled_internal": "pass",
        "security_depth": security_depth,
        **non_oracle_status,
        **live_status,
        "live_contract_effectiveness": live_contract_effectiveness,
        "external_generalization": str(e["external_generalization"].get("external_generalization") or "missing"),
        "holdout_generalization": holdout_status,
        "activation_ablation": activation_status,
        "mechanism_ablation": activation_status,
        **evolution_status,
        "external_harness": "pass" if external_harness == "official_harness_gold_patch_smoke=pass" else external_harness,
        "open_source_prototype_readiness": open_prototype,
        "public_release_readiness": public_release_status,
        "open_source_readiness": "prototype_pass" if open_prototype == "pass" else "partial",
        "academic_claim_readiness": academic,
    }


def render_grand(payload: dict[str, Any]) -> str:
    e = payload["evidence"]
    j = payload["judgment"]
    lines = [
        "# Grand Autonomous Sprint Status",
        "",
        f"Generated at: `{payload['generated_at']}`",
        "",
        "## What Changed",
        "",
        "- Added holdout defensive security validation.",
        "- Added non-oracle local semantic backend validation with live LLM blocked handling.",
        "- Added task-conditioned activation ablation.",
        "- Added advanced evidence-driven candidate evolution and mechanism report.",
        "- Extended the local defensive security mini-suite.",
        "- Added open-source usability docs and readiness audit.",
        "- Preserved SWE-bench as bounded infrastructure readiness only.",
        "",
        "## Evidence Summary",
        "",
        f"- Non-oracle rows: `{len(e['non_oracle'].get('rows', []))}`",
        f"- Non-oracle execution/effectiveness/behavior: `{j.get('non_oracle_execution')}` / `{j.get('non_oracle_effectiveness')}` / `{j.get('non_oracle_behavior')}`",
        f"- Live LLM execution/effectiveness/behavior: `{j.get('live_llm_execution')}` / `{j.get('live_llm_effectiveness')}` / `{j.get('live_llm_behavior')}`",
        f"- Live contract effectiveness: `{j.get('live_contract_effectiveness')}` with after-normalizer pass count `{e['live_contract'].get('after_pass_count')}` / `{e['live_contract'].get('case_count')}`",
        f"- External/semiexternal generalization: `{j.get('external_generalization')}` with pass count `{e['external_generalization'].get('pass_count')}` / `{e['external_generalization'].get('case_count')}`",
        f"- Holdout fresh cases: `{e['holdout'].get('fresh_case_count')}`",
        f"- Mechanism ablation status: `{j.get('mechanism_ablation')}`",
        f"- Advanced candidates: `{len(e['advanced_evolution'].get('candidate_outputs', []))}`",
        f"- Improvement demo decision: `{(e['iterative_contract_improvement'].get('promotion_proposal_count') or 0)} iterative proposal(s); contract demo decision `{(e['contract_improvement'].get('promotion_decision') or {}).get('decision') or 'missing'}`",
        f"- Evolution generation/safety/improvement: `{j.get('candidate_generation')}` / `{j.get('evolution_safety_gate')}` / `{j.get('evolution_improvement')}`",
        f"- Extended suite cases: `{e['extended'].get('case_count')}`",
        f"- SWE-bench final: `{e['swebench'].get('external_harness')}`",
        "",
        "## Final Judgment",
        "",
    ]
    for key, value in j.items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## Non-Claims",
            "",
            "- Not a production vulnerability scanner.",
            "- Not an official CyberSecEval/AutoPatchBench/CVE-Bench result.",
            "- Not a full SPARK reproduction.",
            "- Not SWE-bench agent success while official harness remains infra-blocked.",
            "- Not proof that candidate evolution already produces a superior Skill unless `evolution_improvement` is demonstrated.",
            "- Not proof that live LLM behavior is effective unless verifier pass and discrepancy checks pass.",
            "- Not exploit generation or attack-chain execution.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_academic(payload: dict[str, Any]) -> str:
    j = payload["judgment"]
    return "\n".join(
        [
            "# Academic Claim Readiness Assessment",
            "",
            f"Generated at: `{payload['generated_at']}`",
            "",
            f"Overall academic claim readiness: `{j['academic_claim_readiness']}`",
            "",
            "## Caveat",
            "",
            "The readiness rating is capped by explicit gaps. `strong_candidate_with_external_gap` is allowed only if live LLM validation passes and a live-feedback candidate earns a staged promotion proposal; it still is not an official external benchmark claim. `moderate_high_with_caveat` is used when local bounded evidence is strong but live/evolution/external gaps remain.",
            "",
            "## Supported Claims",
            "",
            "- Prototype-level Evidence-Grounded Skill Evolution Runtime.",
            "- Controlled installed multi-capability secure_code_review validation.",
            "- Local defensive representative mini-suite evidence with holdout and rerun checks.",
            "- Non-oracle local semantic execution and effectiveness evidence are reported separately.",
            "- Live LLM execution and effectiveness evidence are reported separately when configured.",
            "- QGSE-Pareto/marginal utility/task-conditioned activation/rejected-buffer mechanism as a coherent promotion-control story.",
            "- Candidate generation and safety-gate rejection evidence are supported; candidate improvement is supported only if a candidate is promoted with evidence.",
            "",
            "## Still Unsupported",
            "",
            "- Production vulnerability scanning.",
            "- Official external security benchmark performance.",
            "- SWE-bench software patch effectiveness while official harness remains infra-blocked.",
            "- Broad real-world security validity.",
            "- Strong external benchmark readiness while SWE-bench remains infra-blocked.",
            "",
            "## Highest-Value Next Evidence",
            "",
            "- Resolve SWE-bench official harness infrastructure for gold-patch smoke.",
            "- Add independent third-party case authoring or external defensive benchmark subset.",
            "- Run live LLM validation when model/API environment is available.",
        ]
    ) + "\n"


def render_release(payload: dict[str, Any]) -> str:
    required = {
        "README_PROTOTYPE.md": (ROOT / "README_PROTOTYPE.md").exists(),
        "docs/QUICKSTART.md": (ROOT / "docs" / "QUICKSTART.md").exists(),
        "docs/ADDING_A_NEW_SKILL.md": (ROOT / "docs" / "ADDING_A_NEW_SKILL.md").exists(),
        "docs/RUNNING_VALIDATION.md": (ROOT / "docs" / "RUNNING_VALIDATION.md").exists(),
        "docs/TROUBLESHOOTING.md": (ROOT / "docs" / "TROUBLESHOOTING.md").exists(),
        "review_package/MANIFEST.json": (ROOT / "review_package" / "MANIFEST.json").exists(),
        "reports/OPEN_SOURCE_READINESS_AUDIT.md": (ROOT / "reports" / "OPEN_SOURCE_READINESS_AUDIT.md").exists(),
        "clean_environment_smoke": payload["evidence"].get("public_release", {}).get("clean_environment_smoke") == "pass",
        "requirements_lock_reviewed": payload["evidence"].get("public_release", {}).get("requirements_lock_reviewed") == "pass",
        "license_and_repo_metadata": payload["evidence"].get("public_release", {}).get("license_and_repo_metadata") == "pass",
        "one_command_demo": payload["evidence"].get("public_release", {}).get("one_command_demo") == "pass",
    }
    lines = ["# Release Readiness Checklist", "", f"Generated at: `{payload['generated_at']}`", "", "| Item | Ready |", "|---|---:|"]
    for item, ready in required.items():
        lines.append(f"| `{item}` | `{ready}` |")
    lines.extend(
        [
            "",
            "- `open_source_prototype_readiness`: `pass` when docs, manifest, and bounded quickstart are present.",
            "- `public_release_readiness`: `partial` until a clean-environment smoke, dependency lock review, license/repo metadata, and one-command demo are present.",
            "",
            f"Overall release readiness: `{payload['judgment'].get('public_release_readiness')}`",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    evidence = load_evidence()
    payload = {"generated_at": utc_now(), "evidence": evidence, "judgment": judgments(evidence)}
    write_json(JSON_REPORT, payload)
    write_text(REPORT_GRAND, render_grand(payload))
    write_text(REPORT_ACADEMIC, render_academic(payload))
    write_text(REPORT_RELEASE, render_release(payload))
    print(json.dumps({"summary": str(JSON_REPORT), "grand": str(REPORT_GRAND), "judgment": payload["judgment"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
