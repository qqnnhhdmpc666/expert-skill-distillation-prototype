# Running Validation

## Core Runtime

```powershell
skill-deploy build-codex-skill
skill-deploy install --skill outputs/deployable_codex_skill/secure_code_review --version v2
skill-deploy run-skill --installed secure_code_review --case upload_security_001 --backend offline_deterministic
```

## Installed Variant Comparison

```powershell
skill-deploy compare-variants --cases upload,config,api_review,auth --backend offline_deterministic --source installed
```

## Defensive Mini-Suites

```powershell
skill-deploy defensive-security-mini-suite --installed secure_code_review --backend offline_deterministic
skill-deploy holdout-security-mini-suite --installed secure_code_review --backend offline_deterministic
skill-deploy defensive-security-mini-suite-extended --installed secure_code_review --backend offline_deterministic
```

These suites are local defensive representative evidence. They are not official CyberSecEval, AutoPatchBench, CVE-Bench, or production security scanner evidence.

## Non-Oracle Validation

```powershell
skill-deploy non-oracle-validation --installed secure_code_review
```

`live_llm_text` may be blocked if `OPENAI_BASE_URL`, `OPENAI_API_KEY`, and `MODEL` or `OPENAI_MODEL` are not configured. That is infrastructure/configuration blocked, not model failure.

## Activation Ablation

```powershell
skill-deploy activation-ablation --installed secure_code_review
```

Ablation variants are temporary experimental packages. They must not overwrite the active installed package.

## Evolution

```powershell
skill-deploy advanced-evolve --installed secure_code_review --budget 5
```

Candidates are compared against `active_installed`. Failed candidates remain in rejected buffers.

## Final Validation

```powershell
python -m pytest -q
python scripts\validate_task_cases.py
skill-deploy validate-review-package
```
