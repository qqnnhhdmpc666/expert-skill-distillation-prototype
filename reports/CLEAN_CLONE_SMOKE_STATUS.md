# Clean Clone Smoke Status

Generated at: `2026-06-12T14:57:04.482776+00:00`

- Source: `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main`
- Worktree: `C:\Users\31552\AppData\Local\Temp\p0m_clean_clone_smoke\worktree`
- Virtualenv: `C:\Users\31552\AppData\Local\Temp\p0m_clean_clone_smoke\venv`
- Overall status: `pass`

## Commands

| Step | Status | Return code | Command |
|---|---|---:|---|
| create_venv | `pass` | 0 | `C:\Users\31552\AppData\Local\Programs\Python\Python313\python.exe -m venv C:\Users\31552\AppData\Local\Temp\p0m_clean_clone_smoke\venv` |
| upgrade_pip | `pass` | 0 | `C:\Users\31552\AppData\Local\Temp\p0m_clean_clone_smoke\venv\Scripts\python.exe -m pip install --upgrade pip` |
| editable_install | `pass` | 0 | `C:\Users\31552\AppData\Local\Temp\p0m_clean_clone_smoke\venv\Scripts\python.exe -m pip install -e .[dev]` |
| build_codex_skill | `pass` | 0 | `C:\Users\31552\AppData\Local\Temp\p0m_clean_clone_smoke\venv\Scripts\skill-deploy.exe build-codex-skill` |
| install_skill | `pass` | 0 | `C:\Users\31552\AppData\Local\Temp\p0m_clean_clone_smoke\venv\Scripts\skill-deploy.exe install --skill outputs/deployable_codex_skill/secure_code_review --version v2` |
| run_installed_skill | `pass` | 0 | `C:\Users\31552\AppData\Local\Temp\p0m_clean_clone_smoke\venv\Scripts\skill-deploy.exe run-skill --installed secure_code_review --case upload_security_001 --backend offline_deterministic` |
| validate_review_package | `pass` | 0 | `C:\Users\31552\AppData\Local\Temp\p0m_clean_clone_smoke\venv\Scripts\skill-deploy.exe validate-review-package` |

## Boundary

This is a local clean-environment packaging smoke. It is not an external benchmark and does not validate real-world security effectiveness.
