# Release Notes For Prototype Distribution

This repository is a research prototype for an evidence-grounded Skill Evolution Runtime. It is distributed as a Codex Skill + CLI prototype, not as a production vulnerability scanner, official benchmark submission, exploit tool, or production package manager.

## Install

```powershell
python -m pip install -e .[dev]
```

## Minimum Demo

```powershell
skill-deploy build-codex-skill
skill-deploy install --skill outputs/deployable_codex_skill/secure_code_review --version v2
skill-deploy run-skill --installed secure_code_review --case upload_security_001 --backend offline_deterministic
skill-deploy validate-review-package
```

## Claim Boundary

- Local defensive mini-suite evidence is bounded local evidence, not official CyberSecEval, AutoPatchBench, or CVE-Bench evidence.
- SWE-bench remains an auxiliary `software_patch_review` official-harness readiness lane and does not support `secure_code_review` claims.
- Candidate rejection demonstrates safety gating. Candidate improvement is demonstrated only by a strictly better staged promotion proposal.
- Live LLM rows must separate execution from verifier effectiveness.
- Default live validation uses the official DeepSeek OpenAI-compatible endpoint `https://api.deepseek.com` with `deepseek-v4-flash` unless overridden.

## Release Readiness

Public release readiness requires:

- top-level license
- dependency declaration and lock artifact
- clean-environment smoke
- one-command demo path
- no secret-like token in review package
