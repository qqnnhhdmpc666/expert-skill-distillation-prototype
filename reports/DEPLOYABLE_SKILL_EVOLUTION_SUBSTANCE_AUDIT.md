# DEPLOYABLE SKILL EVOLUTION SUBSTANCE AUDIT

Date: 2026-06-11

Scope: audit the recently added deployable-skill / evolution-layer work for substance, not presentation.

Audit rule:

- `Real execution? = yes` means the command or artifact triggers an actual runner/verifier/script path in this repo.
- `Scaffold? = yes` means the artifact mainly defines interface, schema, packaging, or future workflow shape.
- `Derived` means it is computed from existing artifacts or existing controlled runs rather than newly exercising a deeper system capability.

## 1. `skill-deploy` CLI

### Overall finding

`skill-deploy` is a thin CLI wrapper, not an orchestration layer with its own execution engine.

Evidence:

- [src/skill_deployment/cli.py](C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\src\skill_deployment\cli.py)
- Every new command dispatches through `subprocess.call([sys.executable, ...])`.

### Command-by-command

| Command | Real execution? | Wrapper? | Scaffold? | Input -> output | Called module/script | Main artifact path |
|---|---|---|---|---|---|---|
| `health` | yes | yes | partial | no args -> health check side effects | `scripts/validate_task_cases.py`, `scripts/run_generalization_suite.py`, `scripts/validate_review_package.py`, `scripts/build_deployable_codex_skill.py` | `outputs/deployable_codex_skill/...` and existing validation outputs |
| `run-suite` | yes | yes | no | scenario/backend -> controlled suite run | `scripts/run_generalization_suite.py` | `runs/generalization/...`, `outputs/validation/...` |
| `run-skill` | yes | yes | partial | one case/backend -> controlled suite slice | `scripts/run_generalization_suite.py` | `runs/generalization/<case>/...` |
| `qualify` | yes | yes | no | no args -> qualification cards | `scripts/run_skill_qualification_cards.py` | `outputs/validation/skill_qualification_cards.json` |
| `compare-variants` | yes | yes | partial | cases/backend -> 4-variant controlled comparison | `scripts/run_skill_marginal_utility.py` | `outputs/validation/skill_marginal_utility/...` |
| `build-codex-skill` | yes | yes | yes | no args -> package files | `scripts/build_deployable_codex_skill.py` | `outputs/deployable_codex_skill/secure_code_review/...` |
| `evolve` | yes | yes | partial | suite/budget/gate -> minimal evolution outputs | `scripts/run_skill_evolution_lab.py` | `outputs/skill_evolution_lab/secure_code_review/...` |
| `harbor-skeleton` | yes | yes | yes | case -> environment probe + evidence schema | `scripts/run_harbor_live_skeleton.py` | `outputs/harbor_live_skeleton_upload_001/...` |
| `external-security-scaffold` | yes | yes | yes | target sample count -> benchmark scaffold | `scripts/build_external_security_validation_scaffold.py` | `outputs/external_security_validation/...` |
| `export-review-package` | yes | yes | partial | no args -> copy/export package | `scripts/export_review_package.py` | `review_package/...` |

### Important boundary

`run-skill` does **not** invoke the generated deployable Codex Skill package. It simply routes to `scripts/run_generalization_suite.py` with one selected scenario. So the new package exists, but the command path is still the repo’s existing controlled runner.

Evidence:

- [src/skill_deployment/cli.py](C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\src\skill_deployment\cli.py)
- `run-skill` dispatches to `scripts/run_generalization_suite.py --scenarios <case>`.

## 2. `compare-variants`

### What is real

`compare-variants` really executes four variants for each selected case inside the current controlled backend path:

- `no_skill`
- `skill_v1`
- `skill_v2`
- `upper_bound`

Evidence:

- [scripts/run_skill_marginal_utility.py](C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\scripts\run_skill_marginal_utility.py)
- It calls `run_variant(...)` four times in `run_case(...)`.
- `run_variant(...)` calls `get_backend_runner(...).run(context)` and `verify_controlled_execution(...)`.
- Example artifact tree exists under [outputs/validation/skill_marginal_utility/upload_security_001](C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\validation\skill_marginal_utility\upload_security_001).

### What is not real

This is **not** yet a full reproducibility-grade marginal utility system.

Missing from the emitted artifacts:

- per-variant `prompt_hash`
- per-variant `model`
- per-variant `verifier_hash`
- normalized `run_id` for each variant
- explicit proof that the same verifier schema version was frozen across all variants

Observed evidence:

- [outputs/validation/skill_marginal_utility/upload_security_001/no_skill/evidence_bundle/trajectory.jsonl](C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\validation\skill_marginal_utility\upload_security_001\no_skill\evidence_bundle\trajectory.jsonl)
- [outputs/validation/skill_marginal_utility/upload_security_001/skill_v1/evidence_bundle/skill_reads.json](C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\validation\skill_marginal_utility\upload_security_001\skill_v1\evidence_bundle\skill_reads.json)
- [outputs/validation/skill_marginal_utility/upload_security_001/skill_v1/verifier_report.json](C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\validation\skill_marginal_utility\upload_security_001\skill_v1\verifier_report.json)

These show execution and verifier output, but not hash-locked provenance.

### `upper_bound` definition

`upper_bound` is not an oracle external reference. It is a controlled full-capability package built from `case.expected_capabilities`.

Evidence:

- [scripts/run_skill_marginal_utility.py](C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\scripts\run_skill_marginal_utility.py)
- `upper = SkillPackage(... capabilities=case.expected_capabilities, metadata={"upper_bound": True})`

So the current `upper_bound` means:

> a full expected-capability reference within the controlled case schema

not:

> a true external oracle or human upper bound

### Which fields are real vs derived

In `skill_marginal_utility.json`:

- Real-run fields:
  - `variants`
  - `scores`
  - `costs`
  - `false_positives`
  - per-variant evidence bundles and verifier reports
- Derived fields:
  - `v2_over_v1_gain`
  - `v2_over_no_skill_gain`
  - `gap_to_upper_bound`
  - `cost_delta`
  - `false_positive_delta`
  - `metamorphic_delta`

The derived fields are computed from real controlled runs, not copied from old summaries. But they are still summary-level computations, not independent fresh validation artifacts.

Evidence:

- [outputs/validation/skill_marginal_utility/skill_marginal_utility.json](C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\validation\skill_marginal_utility\skill_marginal_utility.json)

### Important caveat

The current offline deterministic backend can make `no_skill` look nonzero rather than truly empty-baseline behavior. For `upload_security_001`, `no_skill` scored `0.6`, and `v2_over_no_skill_gain` is `0.0`. That means the marginal utility path is operational, but its semantic meaning is still limited by the existing backend design.

## 3. Codex Skill package

### What exists

The package directory is real and complete as a package scaffold:

- `SKILL.md`
- `manifest.json`
- `README.md`
- `examples/`
- `eval/`

Evidence:

- [outputs/deployable_codex_skill/secure_code_review](C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\deployable_codex_skill\secure_code_review)
- [scripts/build_deployable_codex_skill.py](C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\scripts\build_deployable_codex_skill.py)

### What is real

- The builder script really creates the package files.
- `skill-deploy` really exists as an installed console entrypoint in the local Python environment.

Evidence:

- `Get-Command skill-deploy` resolved to `C:\Users\31552\AppData\Local\Programs\Python\Python313\Scripts\skill-deploy.exe`

### What is not real yet

This is **not** a proven installable-and-callable Codex Skill in the stronger sense requested by the plan.

Not demonstrated:

- no dedicated `install` command in `skill-deploy`
- no dedicated `rollback` command in `skill-deploy`
- no clean temporary-directory install test of this package itself
- `run-skill` does not dispatch through the built package
- no proof that the package can be imported by a separate Codex skill loader independent of this repo

### Registry / rollback reality

The current registry is a generated controlled installation surface, not a real package manager.

Evidence:

- [outputs/installed_skills/registry.json](C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\installed_skills\registry.json)
- [scripts/build_skill_operationalization_artifacts.py](C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\scripts\build_skill_operationalization_artifacts.py)

Key facts from that script:

- it deletes and regenerates `outputs/installed_skills`
- it seeds install history from existing distillation bundles
- the rollback history for `upload_security_001` includes an explicit `rollback_demo`
- the file itself says this is “not a production package manager”

So:

- `install` = generated artifact seeding from prior bundles
- `rollback` = recorded demonstration history surface
- not a true transactional installer / rollback executor

## 4. Skill Evolution Lab

### What is real

The `evolve` command really runs a script and emits all requested P1-style files:

- `trajectory_store.json`
- `failure_contrast.json`
- `text_gradient.md`
- `candidate_pool.json`
- `rejected_edit_buffer.json`
- `elite_pool.json`
- `retirement_decisions.json`
- `skill_state_registry.json`
- `evolution_report.md`

Evidence:

- [outputs/skill_evolution_lab/secure_code_review](C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\skill_evolution_lab\secure_code_review)
- [scripts/run_skill_evolution_lab.py](C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\scripts\run_skill_evolution_lab.py)

### What is derived

This is **not** yet a true autonomous multi-trajectory evolution engine.

Substance by submodule:

1. `Trajectory Store`
- Yes, it reads multiple records.
- But it reads from existing marginal utility output plus existing qualification cards.
- It does not ingest raw heterogeneous trajectory corpora and re-mine them from scratch.

2. `Failure Contrast -> Text Gradient`
- Yes, `failure_contrast.json` and `text_gradient.md` are produced.
- But their lessons are rule-mapped from current qualification card failure states, not discovered by a fresh optimizer over raw trajectories.

3. `Trace Miner`
- No separate multi-trajectory mining module exists.
- Repetition/cross-case generalization is not actually established by a miner over many traces.

4. `Candidate Builder`
- It does generate candidate records.
- But it does not generate a new edited Skill file/version diff for a new package revision.
- It promotes existing `skill_v2`-style candidates into a candidate list.

5. `Rejected Edit Buffer`
- Real file, real output.
- But populated from current failure contrast mapping, not from repeated rejected proposal attempts across actual evolution rounds.

6. `Elite Pool`
- Real file, real ranking output.
- But it does not run a separate held-out validation set fight between candidate variants and a weakest elite member.
- It ranks current candidates using already-computed marginal utility numbers.

7. `Retirement decisions`
- Real file, real output.
- But decisions are rule-triggered from qualification decisions and marginal utility thresholds.
- They are not driven by a live lifecycle manager applying state transitions to installed package revisions.

### Bottom line

Current status is:

> minimal evidence-gated evolution simulator over existing controlled artifacts

not:

> genuine autonomous Skill Evolution Lab with proposal-validation-promotion loops over fresh multi-trajectory evidence

Evidence:

- [outputs/skill_evolution_lab/secure_code_review/evolution_summary.json](C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\skill_evolution_lab\secure_code_review\evolution_summary.json)

## 5. Harbor skeleton

### Finding

This is a real skeleton and should be treated exactly as a skeleton.

What it really does:

- probes `docker --version`
- probes `wsl --status`
- writes a Harbor-labeled evidence bundle
- writes a summary with `live_ready`

What it does not do:

- does not start Harbor
- does not start Docker
- does not launch a Harbor task
- does not execute a live repair loop
- does not replace replay or prior Harbor evidence

Evidence:

- [scripts/run_harbor_live_skeleton.py](C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\scripts\run_harbor_live_skeleton.py)
- [outputs/harbor_live_skeleton_upload_001/summary.json](C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\harbor_live_skeleton_upload_001\summary.json)

Observed result in this environment:

- `live_ready = false`
- Docker unavailable
- WSL available

So the honest statement is:

> Harbor live runner is not complete here; only readiness probing and evidence schema fallthrough were implemented.

## 6. External security scaffold

### Finding

This is scaffold only.

What it really does:

- writes benchmark order
- writes required case chain
- writes required metrics
- writes safety boundary
- sets `status = scaffold_not_executed`

What it does not do:

- does not download CyberSecEval
- does not run AutoPatchBench
- does not run SecureAgentBench
- does not run CVE-Bench
- does not execute any external case

Evidence:

- [scripts/build_external_security_validation_scaffold.py](C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\scripts\build_external_security_validation_scaffold.py)
- [outputs/external_security_validation/cyberseceval_style_small_sample_scaffold.json](C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\external_security_validation\cyberseceval_style_small_sample_scaffold.json)

Safety boundary is preserved in the scaffold and explicitly forbids exploit generation and attack-chain execution.

## 7. Review package export

### Finding

The review package export is real as a copier/aggregator, not as independent verification.

What it does:

- copies the new deployable-skill, evolution-lab, external-validation, Harbor-skeleton, installed-skill, and report directories into `review_package/`

What it does not do:

- it does not re-validate scientific substance
- it does not distinguish newly executed evidence from copied historical evidence unless the underlying source files already do so

Evidence:

- [scripts/export_review_package.py](C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\scripts\export_review_package.py)
- [review_package](C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\review_package)

## 8. Final status table

| Component | Current status | Real execution? | Scaffold? | Evidence path | Remaining gap |
|---|---|---|---|---|---|
| `skill-deploy` CLI | Thin wrapper over scripts | yes | partial | [src/skill_deployment/cli.py](C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\src\skill_deployment\cli.py) | no native orchestrator, no dedicated install/rollback commands |
| `run-skill` | Controlled case runner entry | yes | partial | [scripts/run_generalization_suite.py](C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\scripts\run_generalization_suite.py) | does not invoke built Codex Skill package |
| `compare-variants` | 4-variant controlled comparison | yes | partial | [outputs/validation/skill_marginal_utility](C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\validation\skill_marginal_utility) | missing prompt/model/hash provenance; `upper_bound` is controlled full-capability reference, not true oracle |
| Deployable Codex Skill package | Package scaffold exists | yes | yes | [outputs/deployable_codex_skill/secure_code_review](C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\deployable_codex_skill\secure_code_review) | not proven as independently installable/callable via dedicated package install flow |
| Installed skill registry | Generated install/version surface | yes | yes | [outputs/installed_skills/registry.json](C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\installed_skills\registry.json) | generated from existing bundles; not a production package manager |
| Rollback surface | Demonstration/event history | yes | yes | [scripts/build_skill_operationalization_artifacts.py](C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\scripts\build_skill_operationalization_artifacts.py) | no live rollback executor in `skill-deploy` |
| Skill Evolution Lab | Minimal evidence-gated simulator | yes | partial | [outputs/skill_evolution_lab/secure_code_review/evolution_summary.json](C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\skill_evolution_lab\secure_code_review\evolution_summary.json) | no fresh multi-trajectory miner, no new skill diff generation, no held-out elite battle |
| Rejected edit buffer | Real emitted artifact | yes | partial | [outputs/skill_evolution_lab/secure_code_review/rejected_edit_buffer.json](C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\skill_evolution_lab\secure_code_review\rejected_edit_buffer.json) | currently populated by rule-mapped contrasts, not repeated live proposal failures |
| Retirement decisions | Real emitted artifact | yes | partial | [outputs/skill_evolution_lab/secure_code_review/retirement_decisions.json](C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\skill_evolution_lab\secure_code_review\retirement_decisions.json) | state changes are advisory overlays, not enforced lifecycle transitions |
| Harbor skeleton | Environment probe + evidence schema | yes | yes | [outputs/harbor_live_skeleton_upload_001/summary.json](C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\harbor_live_skeleton_upload_001\summary.json) | `live_ready=false`; no Harbor live runner |
| External security validation | P2 benchmark scaffold only | yes | yes | [outputs/external_security_validation/cyberseceval_style_small_sample_scaffold.json](C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\external_security_validation\cyberseceval_style_small_sample_scaffold.json) | zero external benchmark execution so far |
| Review package export | Aggregation/export works | yes | partial | [review_package](C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\review_package) | copied package still mixes fresh outputs with prior artifact-backed evidence |

## 9. Bottom-line conclusion

The 15-minute implementation is real in the sense that it added executable CLI entrypoints, generated artifacts, and connected several previously separate outputs into one operational surface.

But it is **not** the full plan substantively.

Best current description:

> first-pass operationalization scaffold with partial real execution, partial derived aggregation, and explicit P0/P1/P2 skeleton surfaces

Not yet justified:

> mature deployable Skill Evolution system
> live Harbor main path
> external benchmark validation
> autonomous multi-trajectory skill evolution
> package-grade install / rollback lifecycle

