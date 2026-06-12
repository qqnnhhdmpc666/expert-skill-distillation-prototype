from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def run_script(args: list[str]) -> int:
    return subprocess.call([sys.executable, *args], cwd=ROOT)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Lightweight CLI wrapper for the skill deployment prototype.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("health", help="Run the P0 health checks for deployable Skill usage.")
    subparsers.add_parser("check-existing", help="Run the demo artifact health check.")
    subparsers.add_parser("audit-claims", help="Run artifact claim audit.")
    subparsers.add_parser("validate-cases", help="Validate API-review holdout task cases.")
    subparsers.add_parser("validate-review-package", help="Validate exported review-package integrity.")
    subparsers.add_parser("build-codex-skill", help="Build the deployable Codex Skill package.")
    subparsers.add_parser("build-software-patch-skill", help="Build the deployable Software Patch Review Skill package.")
    install = subparsers.add_parser("install", help="Install one deployable Skill package into the runtime registry.")
    install.add_argument("--skill", required=True)
    install.add_argument("--version", default=None)
    rollback = subparsers.add_parser("rollback", help="Rollback one installed Skill package to a previous version.")
    rollback.add_argument("--installed", required=True)
    rollback.add_argument("--to-version", required=True)
    subparsers.add_parser("qualify", help="Generate QGSE Skill Qualification Cards.")
    subparsers.add_parser("run-validity-cards", help="Generate multi-axis Skill Revision Validity Cards from current artifacts.")
    run_suite = subparsers.add_parser("run-suite", help="Run the shared controlled task suite.")
    run_suite.add_argument("--backend", default="offline_deterministic")
    run_suite.add_argument("--scenarios", default="upload,auth,config,api_review,data_quality")
    run_skill = subparsers.add_parser("run-skill", help="Run one controlled case through the shared Skill pipeline.")
    run_skill.add_argument("--installed", required=True)
    run_skill.add_argument("--case", default="upload_security_001")
    run_skill.add_argument("--backend", default="offline_deterministic")
    compare = subparsers.add_parser("compare-variants", help="Run no-skill/v1/v2/upper-bound marginal utility comparison.")
    compare.add_argument("--cases", default="upload,data_quality")
    compare.add_argument("--backend", default="offline_deterministic")
    compare.add_argument("--source", default="constructed")
    compare.add_argument("--installed-skill", default="secure_code_review")
    mini = subparsers.add_parser("defensive-security-mini-suite", help="Run the local defensive security mini-suite through installed packages.")
    mini.add_argument("--installed", default="secure_code_review")
    mini.add_argument("--backend", default="offline_deterministic")
    holdout = subparsers.add_parser("holdout-security-mini-suite", help="Run the local holdout defensive security suite through installed packages.")
    holdout.add_argument("--installed", default="secure_code_review")
    holdout.add_argument("--backend", default="offline_deterministic")
    non_oracle = subparsers.add_parser("non-oracle-validation", help="Run non-oracle validation for installed secure_code_review.")
    non_oracle.add_argument("--installed", default="secure_code_review")
    live_validation = subparsers.add_parser("live-llm-validation", help="Run live LLM validation for installed secure_code_review.")
    live_validation.add_argument("--installed", default="secure_code_review")
    live_validation.add_argument("--base-url", default="https://api.deepseek.com")
    live_validation.add_argument("--model", default="deepseek-v4-flash")
    live_validation.add_argument("--timeout-seconds", default="45")
    live_contract = subparsers.add_parser("live-contract-validation", help="Run contract-grounded live validation with evidence normalization.")
    live_contract.add_argument("--installed", default="secure_code_review")
    live_contract.add_argument("--base-url", default="https://api.deepseek.com")
    live_contract.add_argument("--model", default="deepseek-v4-flash")
    live_contract.add_argument("--timeout-seconds", default="60")
    improvement = subparsers.add_parser("improvement-demo", help="Run a live-feedback-driven improvement demo.")
    improvement.add_argument("--installed", default="secure_code_review")
    improvement.add_argument("--source", default="live_llm_feedback")
    improvement.add_argument("--budget", default="2")
    improvement.add_argument("--base-url", default="https://api.deepseek.com")
    improvement.add_argument("--model", default="deepseek-v4-flash")
    improvement.add_argument("--timeout-seconds", default="45")
    contract_improvement = subparsers.add_parser("contract-improvement-demo", help="Attempt a live contract-driven improvement candidate.")
    contract_improvement.add_argument("--installed", default="secure_code_review")
    contract_improvement.add_argument("--base-url", default="https://api.deepseek.com")
    contract_improvement.add_argument("--model", default="deepseek-v4-flash")
    contract_improvement.add_argument("--timeout-seconds", default="60")
    iterative_improvement = subparsers.add_parser("iterative-contract-improvement", help="Run narrow iterative live-contract improvement candidates.")
    iterative_improvement.add_argument("--installed", default="secure_code_review")
    iterative_improvement.add_argument("--base-url", default="https://api.deepseek.com")
    iterative_improvement.add_argument("--model", default="deepseek-v4-flash")
    iterative_improvement.add_argument("--timeout-seconds", default="60")
    iterative_improvement.add_argument("--budget", default="5")
    ablation = subparsers.add_parser("activation-ablation", help="Run task-conditioned activation ablations.")
    ablation.add_argument("--installed", default="secure_code_review")
    ablation.add_argument("--backend", default="offline_deterministic")
    live_ablation = subparsers.add_parser("live-mechanism-ablation", help="Run bounded live ablations for router/normalizer/contract mechanisms.")
    live_ablation.add_argument("--installed", default="secure_code_review")
    live_ablation.add_argument("--base-url", default="https://api.deepseek.com")
    live_ablation.add_argument("--model", default="deepseek-v4-flash")
    live_ablation.add_argument("--timeout-seconds", default="60")
    advanced = subparsers.add_parser("advanced-evolve", help="Run advanced evidence-driven candidate evolution.")
    advanced.add_argument("--installed", default="secure_code_review")
    advanced.add_argument("--budget", default="5")
    extended = subparsers.add_parser("defensive-security-mini-suite-extended", help="Run the extended local defensive security suite.")
    extended.add_argument("--installed", default="secure_code_review")
    extended.add_argument("--backend", default="offline_deterministic")
    external_gen = subparsers.add_parser("external-generalization", help="Run bounded public-source/independent-holdout generalization validation.")
    external_gen.add_argument("--installed", default="secure_code_review")
    external_gen.add_argument("--backend", default="live_llm_text")
    external_gen.add_argument("--base-url", default="https://api.deepseek.com")
    external_gen.add_argument("--model", default="deepseek-v4-flash")
    external_gen.add_argument("--timeout-seconds", default="60")
    subparsers.add_parser("open-source-readiness", help="Audit open-source prototype readiness.")
    subparsers.add_parser("public-release-readiness", help="Audit strict public release readiness.")
    subparsers.add_parser("swebench-infra-final", help="Finalize SWE-bench infra status from bounded official harness attempts.")
    subparsers.add_parser("grand-maturity-report", help="Build final grand autonomous maturity reports.")
    evolve = subparsers.add_parser("evolve", help="Run the minimal evidence-gated Skill Evolution Lab.")
    evolve.add_argument("--suite", default="secure_code_review")
    evolve.add_argument("--budget", default="3")
    evolve.add_argument("--gate", default="qgse_pareto")
    unblock = subparsers.add_parser("swebench-infra-unblock", help="Run a bounded SWE-bench official harness infrastructure unblock attempt.")
    unblock.add_argument("--run-id", default="swebench_gold_patch_smoke_requests_20260612")
    unblock.add_argument("--instance-id", default="psf__requests-1963")
    unblock.add_argument("--max-retries", default="2")
    subparsers.add_parser("representative-matrix", help="Generate the representative validation matrix and maturity ledger.")
    harbor = subparsers.add_parser("harbor-skeleton", help="Write a P0 Harbor live-runner skeleton evidence bundle.")
    harbor.add_argument("--case", default="upload_security_001")
    external = subparsers.add_parser("external-security-scaffold", help="Build the P2 defensive external benchmark scaffold.")
    external.add_argument("--target-sample-count", default="30")
    swe = subparsers.add_parser("external-swebench", help="Run the narrow SWE-bench Lite smoke adapter.")
    swe.add_argument("external_command", choices=["prepare", "run", "summarize", "gold-smoke"])
    swe.add_argument("--dataset", default="SWE-bench/SWE-bench_Lite")
    swe.add_argument("--limit", default="5")
    swe.add_argument("--selection", default="stable")
    swe.add_argument("--seed", default="20260612")
    swe.add_argument("--run-id", default="swebench_lite_smoke_20260612")
    swe.add_argument("--variants", default="empty_patch,gold_patch,skill_llm_patch")
    swe.add_argument("--installed", default="software_patch_review")
    swe.add_argument("--max-workers", default="1")
    swe.add_argument("--backend", default="official_docker")
    swe.add_argument("--instance-id", default="astropy__astropy-12907")
    swe.add_argument("--timeout-seconds", default="1800")
    swe.add_argument("--attempt-mirrors", action="store_true")
    harbor_swe = subparsers.add_parser("harbor-swebench-smoke", help="Gate a SWE-bench-to-Harbor smoke bridge.")
    harbor_swe.add_argument("--source-run", required=True)
    harbor_swe.add_argument("--instances", default="1")
    harbor_swe.add_argument("--variants", default="empty_patch,gold_patch")
    subparsers.add_parser("export-review-package", help="Rebuild the external review package zip.")
    subparsers.add_parser("run-holdout", help="Run the small controlled holdout evaluation.")
    subparsers.add_parser("compare-baselines", help="Run the component baseline attribution slice.")
    subparsers.add_parser("compare-trace-policy", help="Run the risk-vs-random selective trace baseline.")
    subparsers.add_parser("trace-robustness", help="Enumerate all size-2 trace policy allocations.")
    subparsers.add_parser("analyze-summary-miss", help="Analyze direct-summary residual misses.")
    subparsers.add_parser("revision-matrix", help="Run the constrained post-execution revision matrix.")
    subparsers.add_parser("posterior-signal-audit", help="Audit posterior revision signal diagnostics.")
    subparsers.add_parser("naive-revision-ablation", help="Run naive revision strategy pressure-test ablation.")
    subparsers.add_parser("second-domain-config", help="Run the config-security second-domain method probe.")
    subparsers.add_parser("operator-transfer-audit", help="Audit typed operator transfer between API-review and config-security.")
    subparsers.add_parser("prior-posterior-split", help="Split prior vs posterior revision signals across controlled domains.")
    args = parser.parse_args(argv)

    if args.command == "health":
        commands = [
            ["scripts/validate_task_cases.py"],
            ["scripts/run_generalization_suite.py", "--backend", "offline_deterministic", "--scenarios", "upload,auth,config,api_review,data_quality"],
            ["scripts/validate_review_package.py"],
            ["scripts/build_deployable_codex_skill.py"],
        ]
        for command in commands:
            code = run_script(command)
            if code != 0:
                return code
        return 0
    if args.command == "check-existing":
        return run_script(["scripts/run_demo_pipeline.py", "--check-existing"])
    if args.command == "audit-claims":
        return run_script(["scripts/run_artifact_claim_audit.py"])
    if args.command == "validate-cases":
        return run_script(["scripts/validate_task_cases.py"])
    if args.command == "validate-review-package":
        return run_script(["scripts/validate_review_package.py"])
    if args.command == "build-codex-skill":
        return run_script(["scripts/build_deployable_codex_skill.py"])
    if args.command == "build-software-patch-skill":
        return run_script(["scripts/build_software_patch_review_skill.py"])
    if args.command == "install":
        command = ["scripts/install_skill_package.py", "--skill", args.skill]
        if args.version:
            command.extend(["--version", args.version])
        return run_script(command)
    if args.command == "rollback":
        return run_script(["scripts/rollback_installed_skill.py", "--installed", args.installed, "--to-version", args.to_version])
    if args.command == "qualify":
        return run_script(["scripts/run_skill_qualification_cards.py"])
    if args.command == "run-validity-cards":
        return run_script(["scripts/run_skill_revision_validity_cards.py"])
    if args.command == "run-suite":
        return run_script(["scripts/run_generalization_suite.py", "--backend", args.backend, "--scenarios", args.scenarios])
    if args.command == "run-skill":
        return run_script(["scripts/run_installed_skill.py", "--installed", args.installed, "--case", args.case, "--backend", args.backend])
    if args.command == "compare-variants":
        return run_script(["scripts/run_skill_marginal_utility.py", "--backend", args.backend, "--cases", args.cases, "--source", args.source, "--installed-skill", args.installed_skill])
    if args.command == "defensive-security-mini-suite":
        return run_script(["scripts/run_defensive_security_mini_suite.py", "--installed", args.installed, "--backend", args.backend])
    if args.command == "holdout-security-mini-suite":
        return run_script(["scripts/run_holdout_security_mini_suite.py", "--installed", args.installed, "--backend", args.backend])
    if args.command == "non-oracle-validation":
        return run_script(["scripts/run_non_oracle_validation.py", "--installed", args.installed])
    if args.command == "live-llm-validation":
        return run_script(["scripts/run_live_llm_validation.py", "--installed", args.installed, "--base-url", args.base_url, "--model", args.model, "--timeout-seconds", args.timeout_seconds])
    if args.command == "live-contract-validation":
        return run_script(["scripts/run_live_contract_validation.py", "--installed", args.installed, "--base-url", args.base_url, "--model", args.model, "--timeout-seconds", args.timeout_seconds])
    if args.command == "improvement-demo":
        return run_script(["scripts/run_improvement_demo.py", "--installed", args.installed, "--source", args.source, "--budget", args.budget, "--base-url", args.base_url, "--model", args.model, "--timeout-seconds", args.timeout_seconds])
    if args.command == "contract-improvement-demo":
        return run_script(["scripts/run_contract_improvement_demo.py", "--installed", args.installed, "--base-url", args.base_url, "--model", args.model, "--timeout-seconds", args.timeout_seconds])
    if args.command == "iterative-contract-improvement":
        return run_script(["scripts/run_iterative_contract_improvement.py", "--installed", args.installed, "--base-url", args.base_url, "--model", args.model, "--timeout-seconds", args.timeout_seconds, "--budget", args.budget])
    if args.command == "activation-ablation":
        return run_script(["scripts/run_task_conditioned_activation_ablation.py", "--installed", args.installed, "--backend", args.backend])
    if args.command == "live-mechanism-ablation":
        return run_script(["scripts/run_live_mechanism_ablation.py", "--installed", args.installed, "--base-url", args.base_url, "--model", args.model, "--timeout-seconds", args.timeout_seconds])
    if args.command == "advanced-evolve":
        return run_script(["scripts/run_advanced_candidate_evolution.py", "--installed", args.installed, "--budget", args.budget])
    if args.command == "defensive-security-mini-suite-extended":
        return run_script(["scripts/run_extended_defensive_security_mini_suite.py", "--installed", args.installed, "--backend", args.backend])
    if args.command == "external-generalization":
        return run_script(["scripts/run_external_generalization_validation.py", "--installed", args.installed, "--backend", args.backend, "--base-url", args.base_url, "--model", args.model, "--timeout-seconds", args.timeout_seconds])
    if args.command == "open-source-readiness":
        return run_script(["scripts/check_open_source_readiness.py"])
    if args.command == "public-release-readiness":
        return run_script(["scripts/check_public_release_readiness.py"])
    if args.command == "swebench-infra-final":
        return run_script(["scripts/finalize_swebench_infra_status.py"])
    if args.command == "grand-maturity-report":
        return run_script(["scripts/build_grand_autonomous_maturity_reports.py"])
    if args.command == "evolve":
        return run_script(["scripts/run_skill_evolution_lab.py", "--suite", args.suite, "--budget", args.budget, "--gate", args.gate])
    if args.command == "swebench-infra-unblock":
        return run_script(["scripts/run_swebench_infra_unblock.py", "--run-id", args.run_id, "--instance-id", args.instance_id, "--max-retries", args.max_retries])
    if args.command == "representative-matrix":
        return run_script(["scripts/build_representative_validation_matrix.py"])
    if args.command == "harbor-skeleton":
        return run_script(["scripts/run_harbor_live_skeleton.py", "--case", args.case])
    if args.command == "external-security-scaffold":
        return run_script(["scripts/build_external_security_validation_scaffold.py", "--target-sample-count", args.target_sample_count])
    if args.command == "external-swebench":
        command = ["scripts/run_external_swebench_smoke.py", args.external_command]
        if args.external_command == "prepare":
            command.extend(["--dataset", args.dataset, "--limit", args.limit, "--selection", args.selection, "--seed", args.seed])
        elif args.external_command == "run":
            command.extend(["--run-id", args.run_id, "--dataset", args.dataset, "--variants", args.variants, "--installed", args.installed, "--max-workers", args.max_workers, "--backend", args.backend])
        elif args.external_command == "summarize":
            command.extend(["--run-id", args.run_id])
        elif args.external_command == "gold-smoke":
            command = ["scripts/run_swebench_gold_patch_smoke.py", "--run-id", args.run_id, "--dataset", args.dataset, "--instance-id", args.instance_id, "--backend", args.backend, "--max-workers", args.max_workers, "--timeout-seconds", args.timeout_seconds]
            if args.attempt_mirrors:
                command.append("--attempt-mirrors")
        return run_script(command)
    if args.command == "harbor-swebench-smoke":
        return run_script(["scripts/run_harbor_swebench_smoke.py", "--source-run", args.source_run, "--instances", args.instances, "--variants", args.variants])
    if args.command == "export-review-package":
        return run_script(["scripts/export_review_package.py"])
    if args.command == "run-holdout":
        return run_script(["scripts/run_real_effect_eval.py"])
    if args.command == "compare-baselines":
        return run_script(["scripts/run_component_baseline_eval.py"])
    if args.command == "compare-trace-policy":
        return run_script(["scripts/run_risk_trace_policy_baseline.py"])
    if args.command == "trace-robustness":
        return run_script(["scripts/run_risk_trace_policy_robustness.py"])
    if args.command == "analyze-summary-miss":
        return run_script(["scripts/run_direct_summary_miss_analysis.py"])
    if args.command == "revision-matrix":
        return run_script(["scripts/run_revision_decision_matrix.py"])
    if args.command == "posterior-signal-audit":
        return run_script(["scripts/run_posterior_revision_signal_audit.py"])
    if args.command == "naive-revision-ablation":
        return run_script(["scripts/run_naive_revision_ablation.py"])
    if args.command == "second-domain-config":
        return run_script(["scripts/run_second_domain_config_security.py"])
    if args.command == "operator-transfer-audit":
        return run_script(["scripts/run_operator_transfer_audit.py"])
    if args.command == "prior-posterior-split":
        return run_script(["scripts/run_prior_posterior_split.py"])
    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
