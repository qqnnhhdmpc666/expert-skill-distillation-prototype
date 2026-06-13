# Troubleshooting

## `run-skill` Reads The Wrong Package

Check:

```powershell
Get-Content outputs\installed_skills\registry.json
Get-Content outputs\installed_skills\active_skill_pointers\secure_code_review.json
```

The evidence bundle should contain the same `skill_package_path`, `skill_hash`, and `manifest_hash`.

## Version Gains Look Suspicious

Check v1/v2 hash integrity in:

```text
outputs/external_security_mini_suite/mini_suite_summary.json
```

If `version_content_identical=true`, version-gain claims are not supported.

## Oracle Leakage Risk

Run:

```powershell
python scripts\audit_oracle_leakage.py
```

Agent-visible fields may contain task text and target snippets. Verifier-only expected findings, evidence spans, clean labels, and expected capability groups must not be exposed to the runner or candidate generation.

## SWE-bench Infra Blocked

SWE-bench is an auxiliary `software_patch_review` harness-readiness lane. If Docker, conda, DNS, proxy, or image pulls fail, record `infra_blocked`.

Allowed actions:

- check Docker daemon
- check WSL networking
- `docker pull ubuntu:22.04`
- `curl -I https://repo.anaconda.com`
- configure dependency mirror/cache without changing evaluator logic
- retry official harness at most a bounded number of times

Forbidden actions:

- modifying the official evaluator
- changing gold patch or test patch
- using a custom evaluator as replacement
- running `skill_llm_patch` without model configuration
- reporting infrastructure blocked as benchmark success

## What This Project Is Not

It is not:

- a production vulnerability scanner
- a full SPARK reproduction
- an exploit automation tool
- an official benchmark result
- a production package manager
