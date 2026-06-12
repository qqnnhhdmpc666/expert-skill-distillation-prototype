# User Guide

This guide explains how to run the current prototype and how to interpret its artifacts.

## Install

From the repository root:

```powershell
python -m pip install -e .[dev]
```

Build and install the current secure-code-review Skill:

```powershell
skill-deploy build-codex-skill
skill-deploy install --skill outputs/deployable_codex_skill/secure_code_review --version v2
```

Run a basic installed Skill case:

```powershell
skill-deploy run-skill --installed secure_code_review --case upload_security_001 --backend offline_deterministic
```

## Compare Installed Versions

```powershell
skill-deploy compare-variants --cases upload,config --backend offline_deterministic --source installed
```

Key output:

```text
outputs/validation/skill_marginal_utility/
```

Look for `run_metadata.json` under each variant to verify hashes, active pointer snapshots, and schema version.

## Run Live Contract Validation

Set your API key only in the current process:

```powershell
$env:OPENAI_API_KEY = "<your key>"
skill-deploy live-contract-validation --installed secure_code_review --base-url https://api.deepseek.com --model deepseek-v4-flash
```

Key outputs:

```text
outputs/live_contract_validation/live_contract_validation_summary.json
reports/LIVE_CONTRACT_VALIDATION_STATUS.md
```

Each case contains:

```text
raw_execution_before_normalization.json
normalized_execution.json
pre_normalization_verifier_report.json
post_normalization_verifier_report.json
normalization_trace.json
```

Use these files to check whether a pass came from raw model behavior or from contract-safe normalization.

## Run External / Semiexternal Generalization

```powershell
$env:OPENAI_API_KEY = "<your key>"
skill-deploy external-generalization --installed secure_code_review --backend live_llm_text --base-url https://api.deepseek.com --model deepseek-v4-flash
```

This downloads small public read-only source excerpts and mixes them with independent holdout cases. It is not an official benchmark.

Key outputs:

```text
outputs/external_generalization_validation/external_generalization_summary.json
reports/EXTERNAL_GENERALIZATION_VALIDATION_STATUS.md
```

Important metrics:

- `case_count`
- `pass_count`
- `false_positive_count`
- `evidence_exact_match_rate`
- `unsupported_retained_count`
- `ambiguous_handled_count`
- `live_llm_pass_rate`
- `discrepancy_count`

## Run Mechanism Ablation

```powershell
$env:OPENAI_API_KEY = "<your key>"
skill-deploy live-mechanism-ablation --installed secure_code_review --base-url https://api.deepseek.com --model deepseek-v4-flash
```

This compares:

- active contract system
- no evidence normalizer
- no out-of-scope guard
- all capabilities always on
- no task router
- simple prompt baseline approximation

Key outputs:

```text
outputs/mechanism_ablation/live_contract/live_mechanism_ablation_summary.json
reports/LIVE_MECHANISM_ABLATION_STATUS.md
```

Interpretation: this supports the mechanism only if degraded variants show worse scope control, false positives, evidence grounding, or score.

## Attempt Contract Improvement

```powershell
$env:OPENAI_API_KEY = "<your key>"
skill-deploy contract-improvement-demo --installed secure_code_review --base-url https://api.deepseek.com --model deepseek-v4-flash
```

This generates a candidate from real failure evidence and validates it against active runtime behavior. It does not auto-install the candidate.

Key outputs:

```text
outputs/contract_improvement_demo/contract_improvement_demo_summary.json
reports/CONTRACT_IMPROVEMENT_DEMO_STATUS.md
```

A candidate is not promoted unless all strict conditions pass:

- candidate score is strictly higher
- false positives do not increase
- schema errors do not increase
- unsupported evidence does not increase
- clean negative controls are not worse
- unsupported limitation remains unsupported
- no scope violation

For a stronger iterative attempt over multiple narrow candidates:

```powershell
$env:OPENAI_API_KEY = "<your key>"
skill-deploy iterative-contract-improvement --installed secure_code_review --base-url https://api.deepseek.com --model deepseek-v4-flash --budget 5
```

Key outputs:

```text
outputs/iterative_contract_improvement/iterative_contract_improvement_summary.json
outputs/iter_ci/cand/<candidate_id>/
reports/ITERATIVE_CONTRACT_IMPROVEMENT_STATUS.md
```

The iterative run first evaluates the active package, then validates narrow candidate patches. A staged promotion proposal requires strict score improvement with no increase in false positives, schema errors, unsupported evidence, clean/ambiguous regressions, unsupported-scope regressions, or positive-case regressions. It still does not auto-install the candidate.

## Regenerate Maturity Reports

```powershell
skill-deploy representative-matrix
skill-deploy grand-maturity-report
python scripts\build_review_package_manifest.py
```

Main reports:

```text
reports/REPRESENTATIVE_VALIDATION_MATRIX.md
reports/FRAMEWORK_MATURITY_EVIDENCE_LEDGER.md
reports/GRAND_AUTONOMOUS_SPRINT_STATUS.md
reports/ACADEMIC_CLAIM_READINESS_ASSESSMENT.md
review_package/MANIFEST.json
```

## Validate

```powershell
python -m pytest -q
python scripts\validate_task_cases.py
skill-deploy validate-review-package
```

All three should pass before making any broad claim.

## Add A New Skill

1. Create `SKILL.md` and `manifest.json`.
2. Define capability groups and supported task families.
3. Add an out-of-scope guard.
4. Add controlled cases with agent-visible and verifier-only fields separated.
5. Run installed runtime validation.
6. Add marginal utility comparison.
7. Only then attempt candidate evolution.

Never expose verifier-only expected findings or evidence spans to the runner or candidate generator.

## How To Read Results

Use evidence type labels:

- `fresh_run`: strongest local execution evidence.
- `derived_summary`: useful but not direct execution.
- `scaffold`: structure only.
- `infra_blocked`: blocked infrastructure, not success.
- `external_official_harness`: official harness output.

Do not call local deterministic evidence real-world security effectiveness. Do not call public-source read-only demos official benchmark results.
