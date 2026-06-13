# Real Connection Conversion Status

Date: 2026-06-11

Scope: Minimum Real Skill Evolution Loop only. No Harbor live work, no external benchmark, no UI, no database, and no service API were added.

## Summary

The current runtime now connects the minimum loop:

`installed Skill package -> run-skill -> evidence bundle -> candidate Skill diff -> marginal utility -> qualification / reject / rollback`

This is still a prototype runtime, not a production package manager. The important conversion is that install / rollback state is now read by `skill-deploy run-skill`, and the next run observes the active package version rather than using the old generalization suite path.

## Fresh Commands

The following commands were run fresh after the conversion:

```powershell
skill-deploy build-codex-skill
skill-deploy install --skill outputs/deployable_codex_skill/secure_code_review --version v1
skill-deploy run-skill --installed secure_code_review --case upload_security_001 --backend offline_deterministic
skill-deploy install --skill outputs/deployable_codex_skill/secure_code_review --version v2
skill-deploy run-skill --installed secure_code_review --case upload_security_001 --backend offline_deterministic
skill-deploy rollback --installed secure_code_review --to-version v1
skill-deploy run-skill --installed secure_code_review --case upload_security_001 --backend offline_deterministic
skill-deploy compare-variants --cases upload,data_quality --backend offline_deterministic
skill-deploy evolve --suite secure_code_review --budget 1 --gate qgse_pareto
```

Verification commands:

```powershell
python -m py_compile src/skill_deployment/install_state.py src/skill_deployment/provenance.py src/skill_deployment/evidence.py scripts/run_installed_skill.py scripts/run_skill_marginal_utility.py scripts/run_skill_evolution_lab.py scripts/install_skill_package.py scripts/rollback_installed_skill.py scripts/build_deployable_codex_skill.py
```

## Requirement Status

| Requirement | Status | Runtime evidence | Fresh artifact |
|---|---|---|---|
| `run-skill` must read installed package, no fallback to old generalization suite | Done | `skill-deploy run-skill` dispatches to `scripts/run_installed_skill.py`, which reads registry and active pointer before calling `BackendRunner` | `src/skill_deployment/cli.py`, `scripts/run_installed_skill.py` |
| install / rollback changes active pointer and is observed by next run | Done | Fresh v1 run used v1 path, fresh v2 run used v2 path, rollback run returned to v1 path | `outputs/installed_skills/active_skill_pointer.json`, `outputs/installed_skills/install_history.jsonl`, `outputs/installed_skills/rollback_event.json` |
| run-skill evidence records runtime source and package hashes | Done | evidence bundle summary contains `runtime_source`, `skill_version`, `skill_hash`, `manifest_hash`, `skill_package_path` | `outputs/runtime_runs/installed_skills/secure_code_review/upload_security_001/20260611T144906732360Z_v1/evidence_bundle/summary.json`, `outputs/runtime_runs/installed_skills/secure_code_review/upload_security_001/20260611T144936625541Z_v2/evidence_bundle/summary.json`, `outputs/runtime_runs/installed_skills/secure_code_review/upload_security_001/20260611T145006884743Z_v1/evidence_bundle/summary.json` |
| compare-variants records reproducibility provenance | Done | each variant writes `run_metadata.json`; summary embeds per-variant metadata | `outputs/validation/skill_marginal_utility/upload_security_001/skill_v2/run_metadata.json`, `outputs/validation/skill_marginal_utility/data_quality_review_001/no_skill/run_metadata.json` |
| evolve generates real candidate Skill file and diff | Done | candidate directory contains runtime Skill file, manifest, v3 copies, and `skill_diff.md` | `outputs/skill_evolution_lab/secure_code_review/candidates/config_security_001__v3_candidate_001/` |
| candidate_v3 is compared with skill_v2 and rejected if not strictly better | Done | `candidate_v3` score delta is `0.0`, decision is `not_promoted`, rejected edit is appended | `outputs/skill_evolution_lab/secure_code_review/candidates/config_security_001__v3_candidate_001/validation_result.json`, `outputs/skill_evolution_lab/secure_code_review/candidates/config_security_001__v3_candidate_001/promotion_decision.json`, `outputs/skill_evolution_lab/secure_code_review/rejected_edit_buffer.json` |

## Fresh Artifact Details

### Installed runtime state

- Registry: `outputs/installed_skills/registry.json`
- Active pointer: `outputs/installed_skills/active_skill_pointer.json`
- Install history: `outputs/installed_skills/install_history.jsonl`
- Rollback event: `outputs/installed_skills/rollback_event.json`
- Installed v1 package: `outputs/installed_skills/packages/secure_code_review/versions/v1/`
- Installed v2 package: `outputs/installed_skills/packages/secure_code_review/versions/v2/`

Fresh observed state:

- After installing `v1`, `run-skill` wrote `skill_version = v1`.
- After installing `v2`, `run-skill` wrote `skill_version = v2`.
- After rollback to `v1`, `run-skill` again wrote `skill_version = v1`.

### Runtime evidence

- Initial v1 evidence: `outputs/runtime_runs/installed_skills/secure_code_review/upload_security_001/20260611T144906732360Z_v1/evidence_bundle/summary.json`
- v2 evidence: `outputs/runtime_runs/installed_skills/secure_code_review/upload_security_001/20260611T144936625541Z_v2/evidence_bundle/summary.json`
- Rollback-to-v1 evidence: `outputs/runtime_runs/installed_skills/secure_code_review/upload_security_001/20260611T145006884743Z_v1/evidence_bundle/summary.json`

Both evidence bundles include:

- `runtime_source`
- `skill_package_path`
- `skill_version`
- `manifest_hash`
- `skill_hash`

### Marginal utility provenance

Each variant now writes:

- `run_id`
- `case_id`
- `backend`
- `target_hash`
- `skill_hash`
- `manifest_hash`
- `prompt_hash`
- `model`
- `verifier_hash`
- `schema_version`
- `timestamp`
- `cost`
- `tokens`
- unavailable reasons for cost/tokens when needed

Representative fresh artifacts:

- `outputs/validation/skill_marginal_utility/upload_security_001/skill_v2/run_metadata.json`
- `outputs/validation/skill_marginal_utility/data_quality_review_001/no_skill/run_metadata.json`
- `outputs/validation/skill_marginal_utility/skill_marginal_utility.json`

### Candidate evolution

Candidate output:

- `outputs/skill_evolution_lab/secure_code_review/candidates/config_security_001__v3_candidate_001/SKILL.md`
- `outputs/skill_evolution_lab/secure_code_review/candidates/config_security_001__v3_candidate_001/manifest.json`
- `outputs/skill_evolution_lab/secure_code_review/candidates/config_security_001__v3_candidate_001/SKILL.v3.md`
- `outputs/skill_evolution_lab/secure_code_review/candidates/config_security_001__v3_candidate_001/manifest.v3.json`
- `outputs/skill_evolution_lab/secure_code_review/candidates/config_security_001__v3_candidate_001/skill_diff.md`
- `outputs/skill_evolution_lab/secure_code_review/candidates/config_security_001__v3_candidate_001/validation_result.json`
- `outputs/skill_evolution_lab/secure_code_review/candidates/config_security_001__v3_candidate_001/promotion_decision.json`

Fresh result:

- Baseline variant: `skill_v2`
- Candidate variant: `candidate_v3`
- Score delta: `0.0`
- Decision: `not_promoted`
- Rejected buffer entry: `rejected::config_security_001__v3_candidate_001`

## Remaining Gaps

- The installed `secure_code_review` runtime is intentionally scoped to the P0 acceptance case `upload_security_001`; it is not yet a general multi-task package.
- `run-skill` now observes installed versions, but the offline verifier still reports the installed runs as non-passing because current capability evidence hints are not fully target-bound under the stricter verifier. This does not break the runtime connection proof, but it is a behavior-quality gap.
- The registry still preserves older controlled lifecycle rows alongside the new `secure_code_review` runtime row. The active runtime path uses `active_skill_pointer.json`, so this does not affect execution, but registry cleanup remains future hygiene.
- `candidate_v3` is a deterministic bounded text patch from one failure contrast. It is a real candidate file and diff, but not yet a broad search or multi-candidate optimizer.
- Cost is unavailable for offline deterministic runs, so `cost = null` with an explicit reason. Token estimates are available for skill text only.

## Non-Scope Confirmation

No new work was added for:

- Harbor live runner
- external benchmark
- UI
- database
- service API
- production package manager behavior
