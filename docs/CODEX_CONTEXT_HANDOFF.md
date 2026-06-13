# Codex Context Handoff

This file is the first document a new Codex session should read when taking over this project from GitHub or a cloud worktree.

## Quick Start For A New Codex Session

Recommended first prompt:

```text
Please read docs/CODEX_CONTEXT_HANDOFF.md first, then skim README.md, docs/CLAIM_BOUNDARY.md, reports/DEMO_REPORT.md, reports/CURRENT_PROGRESS_ALIGNMENT.md, and docs/RUNBOOK.md. Continue from the current project state without overclaiming the method.
```

Repository:

```text
https://github.com/qqnnhhdmpc666/expert-skill-distillation-prototype
```

Primary local workspace used so far:

```text
D:\solution
```

Cloud or another machine should clone the GitHub repository and treat the repository contents as the source of truth.

## Project Identity

This is an expert skill distillation and deployment prototype inspired by SPARK-PDI and COLLEAGUE.SKILL.

The current safe positioning is:

```text
risk-budgeted traceable skill deployment prototype
```

Equivalent conservative wording:

```text
correctness-constrained expert skill deployment optimization
```

Current method seed:

```text
typed posterior revision over deployable expert-skill packages
```

In plain terms:

```text
The system treats a generated expert skill as a deployable hypothesis. After execution, verifier feedback is typed into revision operators such as rule patch, output-contract rewrite, rollback, or trace-contract strengthening. A gate then decides whether the revised compact skill should be promoted, rejected, or rolled back under correctness, budget, semantic, and traceability constraints.
```

## What Has Been Built

Stable demo loop:

```text
expert material
-> evidence-grounded full skill
-> compact deployment skill
-> agent output
-> verifier feedback
-> patch proposal
-> validation gate
-> compact v2 or rollback
-> selective trace for high-risk rules
```

Implemented layers:

- Deterministic API-review baseline.
- SPARK/Harbor-compatible execution feedback adapter.
- Real Harbor verifier case001 and case002.
- Mock/scripted API review agent.
- OpenAI-compatible/RightCode LLM agent matrix artifact.
- Output-format failure vertical slice.
- Counterfactual patch utility probe.
- Fixed-budget compiler and validation-aware compiler probes.
- Rollback gate, semantic preservation audit, skill-to-agent trace protocol.
- Real-effect controlled holdout evaluation.
- Selective trace and risk-trace baseline/robustness probes.
- Second-domain config-security validation.
- Operator-transfer and prior/posterior signal audits.
- Minimal Python package, schemas, CLI, and tests.

## Key Evidence Artifacts

Core outputs live under:

```text
outputs/mvp_vertical_slice
```

Important artifact directories:

```text
baseline_001
harbor_api_review_001
harbor_api_review_002
agent_mock_api_review_001
llm_agent_api_review_001
output_format_error_001
counterfactual_patch_utility_001
fixed_budget_compiler_001
rollback_gate_001
validation_aware_compiler_001
semantic_preservation_audit_001
skill_to_agent_loop_001
traceable_compiler_integration_001
real_effect_eval_001
selective_trace_compiler_001
artifact_claim_audit_001
component_baseline_direct_summary_001
risk_trace_policy_baseline_001
risk_trace_policy_robustness_001
direct_summary_miss_analysis_001
adversarial_trace_verifier_001
revision_decision_matrix_001
posterior_revision_signal_audit_001
naive_revision_ablation_001
second_domain_config_security_001
operator_transfer_audit_001
prior_posterior_split_001
```

Useful high-level reports:

```text
reports/DEMO_REPORT.md
reports/CURRENT_PROGRESS_ALIGNMENT.md
docs/CLAIM_BOUNDARY.md
docs/RELATED_WORK_DELTA_AUDIT.md
docs/RELATED_WORK_NOVELTY_PRESSURE_TEST.md
docs/POSTERIOR_SKILL_REVISION_METHOD.md
docs/FALSIFICATION_AND_NEXT_EVIDENCE.md
docs/RUNBOOK.md
```

## Current Results To Remember

API-review baseline:

```text
no_skill: 0 / 6
full_skill: 6 / 6
compact_v1: 4 / 6
compact_v2: 6 / 6
```

Controlled holdout evidence:

```text
compact_v1 avg coverage: 0.58
patched_compact avg coverage: 1.00
```

Selective trace toy slice:

```text
full_trace: 300 / 237, rejected
selective_trace R005/R006: 183 / 237, accepted and blocks shortcut
```

Second-domain config-security probe:

```text
direct_summary_skill: coverage 0.825, 2 / 4 pass
type_specific_operator_plus_gate_and_selective_trace: 4 / 4 pass, 166 / 260 tokens
always_regenerate_full_skill: 4 / 4 pass, 289 / 260 tokens
always_full_trace: 4 / 4 pass, 629 / 260 tokens
```

Operator-transfer audit:

```text
missing_rule -> patch_rule
output_contract_error -> rewrite_output_contract
regression_observed -> reject_and_rollback
trace_budget_pressure -> risk_based_selective_trace
```

Safe interpretation:

```text
Current artifacts support a narrow two-domain schematic transfer of typed posterior revision under deployment constraints. They do not prove broad generalization.
```

## Claims Allowed

You may say:

- The project has a reproducible controlled vertical loop for expert-material-to-deployable-skill artifacts.
- SPARK-PDI contributes the posterior execution evidence orientation.
- COLLEAGUE.SKILL contributes the inspectable and correctable skill artifact orientation.
- The prototype explores correctness-constrained deployment after skill generation.
- In controlled API-review and config-security slices, typed posterior revision explains why different failures need different revision operators.
- Validation gates can reject over-budget or regressive patches in toy slices.
- Selective trace can allocate trace overhead to failure-critical rules in toy slices.

## Claims Not Allowed

Do not say:

- This is a full reproduction of SPARK-PDI.
- This outperforms SPARK-PDI or COLLEAGUE.SKILL.
- This is a benchmark.
- This is a mature universal skill compiler.
- This proves general cross-domain transfer.
- This proves real LLM agents will consistently benefit in open-ended settings.
- Every component is original.

If unsure, downgrade wording to:

```text
partially supported in controlled slices
```

or:

```text
diagnostic evidence, not a general proof
```

## How To Verify The Repository Quickly

Run from the repository root:

```powershell
python -m pytest
python scripts\run_demo_pipeline.py --check-existing
python scripts\run_artifact_claim_audit.py
python scripts\validate_task_cases.py
```

Expected current state:

```text
pytest: passing
run_demo_pipeline --check-existing: overall_status ok
artifact claim audit: generated successfully
task case validation: passing
```

Before committing or pushing, scan for secrets:

```powershell
rg 'OPENAI_API_KEY\s*=\s*[''"]?sk-|sk-[A-Za-z0-9]{20,}' -n .
```

The repo must not contain API keys.

## Current Engineering Shape

This repository started script-first and has been patched toward a minimal package structure.

Package skeleton:

```text
src/skill_deployment
```

Important package files:

```text
schemas.py
artifacts.py
token_budget.py
gate.py
trace.py
cli.py
```

CLI entry points are still lightweight wrappers over scripts. Do not do a large refactor unless explicitly requested. The priority is preserving the demo and evidence artifacts.

## Recommended Next Work

Short-term cloud handoff tasks:

- Confirm the cloud worktree can run the quick verification commands.
- Use the zero-dependency interactive web demo at `demo/web/index.html` for mentor-facing walkthroughs. If the in-app browser blocks `file://`, serve it locally, for example `python -m http.server 8765 --directory demo/web`, then open `http://127.0.0.1:8765/index.html`.
- Keep `docs/CODEX_CONTEXT_HANDOFF.md` updated whenever the project direction changes.
- Do not rerun heavy Harbor or LLM workflows unless needed.
- Keep GitHub `main` synchronized after meaningful work.

Research-method next tasks:

- Make the second-domain evidence less hand-constructed by adding one small independently written case family.
- Strengthen comparison against direct summary, full regeneration, always append, always contract, accept-if-fixed, and full trace.
- Look for a cleaner method abstraction around typed posterior revision without over-naming every component.
- Continue mapping related work gaps: self-refine, Reflexion, prompt repair, memory update, program repair, skill libraries, SPARK-PDI, and COLLEAGUE.SKILL.

Demo-stability next tasks:

- Keep `reports/DEMO_REPORT.md` short enough to present.
- Maintain `docs/CLAIM_BOUNDARY.md`.
- Make sure `scripts\run_demo_pipeline.py --check-existing` remains green.

## If The New Session Feels Lost

Read these in order:

```text
docs/CODEX_CONTEXT_HANDOFF.md
docs/CLAIM_BOUNDARY.md
reports/DEMO_REPORT.md
reports/CURRENT_PROGRESS_ALIGNMENT.md
docs/RUNBOOK.md
docs/RELATED_WORK_DELTA_AUDIT.md
docs/POSTERIOR_SKILL_REVISION_METHOD.md
```

Then run:

```powershell
python scripts\run_demo_pipeline.py --check-existing
```

After that, continue only from evidence-backed claims. This project is valuable precisely because it keeps the distinction between a working demo, a method seed, and a general research claim clear.
