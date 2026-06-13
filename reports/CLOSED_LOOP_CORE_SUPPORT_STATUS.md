# Closed Loop Core Support Status

Date: 2026-06-13

## Core Question

Does the system truly support the two-part project core?

1. `expert materials -> installable Skill`
2. `execution / verifier feedback -> candidate Skill upgrade`

## Answer

Yes, with an important boundary:

- The **expert-material distillation path is now a real runtime entrypoint** through `skill-deploy distill-skill`.
- The **feedback-driven evolution path was already present** through the existing candidate / verifier / gate / rollback machinery.
- What is still not claimed is open-world automatic induction or guaranteed autonomous improvement.

## Fresh Commands

```powershell
skill-deploy distill-skill --cases upload,config,api_review,auth --skill-id secure_code_review_distilled --version v1
skill-deploy install --skill outputs/distilled_skills/secure_code_review_distilled --version v1
skill-deploy run-skill --installed secure_code_review_distilled --case upload_security_001 --backend offline_deterministic
skill-deploy run-skill --installed secure_code_review_distilled --case config_security_001 --backend offline_deterministic
skill-deploy run-skill --installed secure_code_review_distilled --case api_review_001 --backend offline_deterministic
skill-deploy run-skill --installed secure_code_review_distilled --case auth_access_control_001 --backend offline_deterministic
skill-deploy run-skill --installed secure_code_review_distilled --case data_quality_review_001 --backend offline_deterministic
```

## What Is Newly Real

### A. Expert-material distillation is now first-class

The new CLI path:

```text
skill-deploy distill-skill
```

builds a real installable package from expert materials and writes provenance inside the package version directory.

Fresh artifact:

- `outputs/distilled_skills/secure_code_review_distilled/versions/v1/manifest.json`
- `outputs/distilled_skills/secure_code_review_distilled/versions/v1/SKILL.md`
- `outputs/distilled_skills/secure_code_review_distilled/versions/v1/provenance/source_materials_manifest.json`
- `outputs/distilled_skills/secure_code_review_distilled/versions/v1/provenance/extracted_candidates.json`
- `outputs/distilled_skills/secure_code_review_distilled/versions/v1/provenance/capability_provenance.json`
- `outputs/distilled_skills/secure_code_review_distilled/versions/v1/provenance/distillation_trace.json`

This is no longer just a hardcoded builder path.

### B. Installed runtime uses the distilled package

The distilled package was installed and then executed through the normal installed runtime path, not a bypass.

Pass evidence:

- `outputs/runtime_runs/installed_skills/secure_code_review_distilled/upload_security_001/20260613T065456425255Z_v1/run_summary.json`
- `outputs/runtime_runs/installed_skills/secure_code_review_distilled/config_security_001/20260613T065457270088Z_v1/run_summary.json`
- `outputs/runtime_runs/installed_skills/secure_code_review_distilled/api_review_001/20260613T065457790639Z_v1/run_summary.json`
- `outputs/runtime_runs/installed_skills/secure_code_review_distilled/auth_access_control_001/20260613T065458653506Z_v1/run_summary.json`

Out-of-scope evidence:

- `outputs/runtime_runs/installed_skills/secure_code_review_distilled/data_quality_review_001/20260613T065524720009Z_v1/run_summary.json`

Observed behavior:

- four security task families pass through the installed distilled package
- `data_quality_review_001` activates `out_of_scope_guard`
- no data-quality capability was absorbed into `secure_code_review_distilled`

### C. Feedback-driven evolution remains available on the same system spine

The posterior half of the loop remains the same:

```text
installed Skill
-> execution
-> verifier / evidence
-> candidate generation
-> validation / gate
-> promote / reject / rollback
```

Representative existing artifacts:

- `reports/SMALL_CANDIDATE_EVOLUTION_STATUS.md`
- `reports/IMPROVEMENT_DEMO_STATUS.md`
- `outputs/skill_evolution_lab/secure_code_review/`

## Current Boundary

What is now supported:

- expert materials can become an installable Skill package
- installed runtime can execute that distilled package
- execution evidence can still feed the existing evolution pipeline

What is not yet claimed:

- open-world expert-material understanding
- guaranteed autonomous candidate improvement
- official external benchmark proof
- production-grade general-purpose security tooling

## Practical Interpretation

The system is now aligned with the intended project core:

```text
expert knowledge distillation + evidence-driven Skill evolution
```

The strongest honest claim is:

> The repository now supports a real closed-loop prototype in which controlled expert materials are distilled into installable Skills, and those Skills can enter the existing evidence-driven upgrade and gating runtime.
