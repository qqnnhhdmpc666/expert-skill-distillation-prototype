# Reproduce Latest Results

This document gives the shortest practical path to reproduce the latest local evidence.

## 1. Install

```powershell
python -m pip install -e .[dev]
```

## 2. Build And Install Skill

```powershell
skill-deploy build-codex-skill
skill-deploy install --skill outputs/deployable_codex_skill/secure_code_review --version v2
```

## 3. Offline Health

```powershell
skill-deploy run-skill --installed secure_code_review --case upload_security_001 --backend offline_deterministic
skill-deploy compare-variants --cases upload,config --backend offline_deterministic --source installed
```

## 4. Live Runs

Set the API key only for the current shell:

```powershell
$env:OPENAI_API_KEY = "<your key>"
```

Then run:

```powershell
skill-deploy live-contract-validation --installed secure_code_review --base-url https://api.deepseek.com --model deepseek-v4-flash
skill-deploy external-generalization --installed secure_code_review --backend live_llm_text --base-url https://api.deepseek.com --model deepseek-v4-flash
skill-deploy live-mechanism-ablation --installed secure_code_review --base-url https://api.deepseek.com --model deepseek-v4-flash
skill-deploy contract-improvement-demo --installed secure_code_review --base-url https://api.deepseek.com --model deepseek-v4-flash
skill-deploy iterative-contract-improvement --installed secure_code_review --base-url https://api.deepseek.com --model deepseek-v4-flash --budget 5
```

Live model behavior can vary. Do not delete failed rows. They are part of the evidence.

## 5. Rebuild Reports

```powershell
skill-deploy representative-matrix
skill-deploy grand-maturity-report
python scripts\build_review_package_manifest.py
```

## 6. Final Validation

```powershell
python -m pytest -q
python scripts\validate_task_cases.py
skill-deploy validate-review-package
```

## 7. Expected Current Pattern

The exact live rows may vary, but the latest saved state has this pattern:

- controlled internal runtime passes
- live contract effectiveness is pass on the latest saved representative set
- external generalization is partial, currently with 9/12 effective pass and zero false positives
- mechanism ablation supports the mechanism
- iterative contract improvement has staged promotion proposals, but they are not auto-installed
- external official SWE-bench harness remains infra-blocked

## 8. Secret Scan

Before committing or uploading:

```powershell
rg "sk-[A-Za-z0-9]" reports outputs docs review_package PROJECT_OVERVIEW_FOR_GITHUB.md HANDOFF_FOR_NEXT_CHAT.md
```

There should be no API key literal in committed artifacts.
