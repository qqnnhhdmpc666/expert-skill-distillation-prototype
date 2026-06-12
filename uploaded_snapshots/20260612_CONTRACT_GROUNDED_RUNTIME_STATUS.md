# Contract-Grounded Runtime Sprint Status Snapshot

Date: 2026-06-12

This snapshot records the latest local sprint result from the Codex workspace. It is a GitHub-uploaded handoff artifact, not a replacement for a normal git push of the full worktree.

## Project Positioning

The project is an Evidence-Grounded / Contract-Grounded Skill Evolution Runtime for live agents. It is not a production vulnerability scanner, not a complete SPARK reproduction, not a SWE-bench agent, and not an official CyberSecEval / AutoPatchBench / CVE-Bench result.

## Latest Final Judgment

```text
controlled_internal: pass
security_depth: pass_local_bounded
live_contract_effectiveness: partial
external_generalization: partial
mechanism_ablation: supports_mechanism
evolution_improvement: not_yet_demonstrated
external_harness: infra_blocked
public_release_readiness: pass
academic_claim_readiness: moderate_high_with_caveat
```

## Key New Local Artifacts

```text
src/skill_deployment/live_contract.py
scripts/run_live_contract_validation.py
scripts/run_external_generalization_validation.py
scripts/run_live_mechanism_ablation.py
scripts/run_contract_improvement_demo.py
PROJECT_OVERVIEW_FOR_GITHUB.md
docs/ARCHITECTURE_AND_DESIGN.md
docs/USER_GUIDE.md
HANDOFF_FOR_NEXT_CHAT.md
docs/RUN_STATE_SUMMARY.md
docs/REPRODUCE_LATEST_RESULTS.md
```

## Key Reports

```text
reports/LIVE_CONTRACT_VALIDATION_STATUS.md
reports/EXTERNAL_GENERALIZATION_VALIDATION_STATUS.md
reports/LIVE_MECHANISM_ABLATION_STATUS.md
reports/CONTRACT_IMPROVEMENT_DEMO_STATUS.md
reports/REPRESENTATIVE_VALIDATION_MATRIX.md
reports/FRAMEWORK_MATURITY_EVIDENCE_LEDGER.md
reports/GRAND_AUTONOMOUS_SPRINT_STATUS.md
reports/ACADEMIC_CLAIM_READINESS_ASSESSMENT.md
```

## Latest Evidence Summary

- Live contract validation ran seven cases: upload, config, auth, API, clean, unsupported, ambiguous. It completed, but remains partial.
- External/semiexternal validation ran public OWASP NodeGoat read-only excerpts plus independent holdouts. It remains partial, with retained failures and local labels only.
- Mechanism ablation supports the runtime mechanism: no-normalizer, no-router, all-capabilities, and simple-baseline variants regress versus the active contract system.
- Contract improvement candidate generation passed, but the candidate was not promoted because the strict improvement rule was not satisfied.
- SWE-bench official harness remains infra-blocked and is not claimed as benchmark success.

## Reproduction Commands

```powershell
python -m pip install -e .[dev]
skill-deploy build-codex-skill
skill-deploy install --skill outputs/deployable_codex_skill/secure_code_review --version v2

$env:OPENAI_API_KEY = "<your key>"
skill-deploy live-contract-validation --installed secure_code_review --base-url https://api.deepseek.com --model deepseek-v4-flash
skill-deploy external-generalization --installed secure_code_review --backend live_llm_text --base-url https://api.deepseek.com --model deepseek-v4-flash
skill-deploy live-mechanism-ablation --installed secure_code_review --base-url https://api.deepseek.com --model deepseek-v4-flash
skill-deploy contract-improvement-demo --installed secure_code_review --base-url https://api.deepseek.com --model deepseek-v4-flash

skill-deploy representative-matrix
skill-deploy grand-maturity-report
python scripts\build_review_package_manifest.py
python -m pytest -q
python scripts\validate_task_cases.py
skill-deploy validate-review-package
```

## Validation Result In Local Workspace

```text
python -m pytest -q -> 46 passed
python scripts\validate_task_cases.py -> status=ok, case_count=8
skill-deploy validate-review-package -> status=ok, error_count=0
```

## Upload Limitation

The current local folder is not a git repository, GitHub CLI is not authenticated, and SSH auth timed out. This snapshot was uploaded through the Codex GitHub connector. A normal full-worktree push still requires authenticated git/gh access or connector support for tree commits.

## Secret Handling

The explicit API key provided during the session was not found in scanned artifacts. API keys should be provided only through process environment variables and rotated if they were pasted into chat.
