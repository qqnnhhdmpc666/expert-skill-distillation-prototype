# Quickstart

This quickstart exercises the controlled Codex Skill + CLI path.

## Install The Package Locally

```powershell
python -m pip install -e .[dev]
```

## Build And Install The Secure Review Skill

```powershell
skill-deploy build-codex-skill
skill-deploy install --skill outputs/deployable_codex_skill/secure_code_review --version v2
```

## Run One Installed Skill Case

```powershell
skill-deploy run-skill --installed secure_code_review --case upload_security_001 --backend offline_deterministic
```

## Compare Installed Variants

```powershell
skill-deploy compare-variants --cases upload,config --backend offline_deterministic --source installed
```

## Validate Review Package

```powershell
skill-deploy validate-review-package
```

## Representative Sprint Commands

```powershell
skill-deploy defensive-security-mini-suite --installed secure_code_review --backend offline_deterministic
skill-deploy holdout-security-mini-suite --installed secure_code_review --backend offline_deterministic
skill-deploy non-oracle-validation --installed secure_code_review
skill-deploy live-llm-validation --installed secure_code_review --base-url https://api.deepseek.com --model deepseek-v4-flash
skill-deploy activation-ablation --installed secure_code_review
skill-deploy advanced-evolve --installed secure_code_review --budget 5
skill-deploy improvement-demo --installed secure_code_review --source live_llm_feedback --budget 2 --base-url https://api.deepseek.com --model deepseek-v4-flash
skill-deploy defensive-security-mini-suite-extended --installed secure_code_review --backend offline_deterministic
skill-deploy evolve --suite secure_code_review --budget 3 --gate qgse_pareto
skill-deploy swebench-infra-unblock --run-id swebench_gold_patch_smoke_requests_20260612 --instance-id psf__requests-1963 --max-retries 2
skill-deploy representative-matrix
```

SWE-bench is an auxiliary official-harness readiness lane. It is allowed to remain `infra_blocked`; do not treat that as model or Skill failure.

## Read Evidence Bundles

Each controlled run writes an `evidence_bundle/` directory with:

- `summary.json`
- `trajectory.jsonl`
- `target_reads.json`
- `skill_reads.json`
- `verifier_feedback.json`
- `repair_patch.json`
- `qualification_decision.json`

The `summary.json` provenance records `skill_package_path`, `skill_hash`, `manifest_hash`, task family, activated capability group, and runtime source.
