# Clean Clone Smoke

The clean clone smoke copies a reduced source tree to a temporary worktree, creates a local virtual environment, installs the package, and runs the minimum CLI path.

```powershell
python scripts\run_clean_clone_smoke.py --source . --keep-artifacts
```

Expected commands inside the smoke:

```powershell
python -m pip install -e .[dev]
skill-deploy build-codex-skill
skill-deploy install --skill outputs/deployable_codex_skill/secure_code_review --version v2
skill-deploy run-skill --installed secure_code_review --case upload_security_001 --backend offline_deterministic
skill-deploy validate-review-package
```

Artifacts:

```text
outputs/release/clean_clone_smoke/summary.json
reports/CLEAN_CLONE_SMOKE_STATUS.md
```

The smoke is local release-readiness evidence. It is not an external benchmark and does not validate real-world security effectiveness.
