# Related-Work Delta Audit

Date: 2026-06-06

## Purpose

This audit clarifies how the current prototype relates to:

- SPARK-PDI / Evidence Over Plans: Online Trajectory Verification for Skill Distillation, arXiv:2605.09192.
- COLLEAGUE.SKILL: Automated AI Skill Generation via Expert Knowledge Distillation, arXiv:2605.31264.

It should prevent two opposite mistakes:

- overclaiming that every component is original;
- underclaiming the work as a simple SPARK + COLLEAGUE splice.

Current safe positioning:

```text
risk-budgeted traceable skill deployment prototype
```

or:

```text
correctness-constrained expert skill deployment optimization
```

Source basis:

- SPARK-PDI introduces PDI and SPARK for preserving environment-verified trajectories and using execution evidence as an online diagnostic signal. See https://arxiv.org/abs/2605.09192.
- COLLEAGUE.SKILL introduces an inspectable, correctable, versioned skill package generated from heterogeneous expert/person traces. See https://arxiv.org/abs/2605.31264.

## Category Labels

```text
A. inherited / inspired component
B. scoped engineering adaptation
C. our method-discovery contribution
```

Not every row should be C. Most rows are A or B. The current true exploration points are mainly around compact deployment under correctness, budget, validation, and selective trace constraints.

Latest method-level exploration:

```text
posterior skill revision
```

This adapts SPARK-PDI's posterior-evidence orientation to deployable expert skill artifacts: execution/verifier feedback is treated as a revision signal that can change patch, gate, rollback, and trace decisions. This is a method hypothesis, not a PDI-scale metric.

## Delta By Component

| Component | Related Work Inspiration | What We Reuse | What We Simplify | What We Add | Current Supporting Artifact | Limitation | Claim Strength | Category |
|---|---|---|---|---|---|---|---|---|
| expert material -> rule / full skill | COLLEAGUE.SKILL trace-to-skill and inspectable skill package | Expert-material-first skill artifact idea; full skill as auditable package | No multi-host install surface; no person-grounded behavior track; no private trace ingestion | Rule/evidence package specialized to API-review expert rules | `outputs/mvp_vertical_slice/baseline_001` | Adequate for demo, not a general COLLEAGUE replacement | partially_supported | B |
| full skill -> compact skill | Skill package / deployment surface from COLLEAGUE; efficiency motivation from SPARK student-model setting | Separation between full/audit skill and deployable invocation skill | No broad skill marketplace or general routing | Compact deployment skill with rule-level token/cost accounting | `baseline_001`, `fixed_budget_compiler_001`, `validation_aware_compiler_001` | Current compiler is toy and domain-specific | partially_supported | C |
| execution feedback -> failure report | SPARK emphasis on environment-grounded evidence and trajectory verification | Verifier output as evidence, not only plan/preference signal | We do not compute PDI or full trajectory-level posterior metrics | Unified execution report from Harbor/SPARK-compatible artifacts | `harbor_api_review_001`, `harbor_api_review_002`, `integrations/spark/*` | API-review verifier is much simpler than SPARK task trajectories | supported for demo | B |
| failure report -> patch | SPARK online diagnostic/intervention idea; COLLEAGUE correction lifecycle | Failure feedback should trigger skill updates | No general natural-language correction lifecycle | Failure-type-to-patch mapping at rule/output-contract level | `output_format_error_001`, `counterfactual_patch_utility_001` | Toy taxonomy; not a general patch compiler | partially_supported | C |
| patch -> validation gate / rollback | COLLEAGUE rollback/versioning; SPARK validation before using evidence | Promotion checks and rollback idea | No full version manager or multi-run causal validation | Gate rejects regression or over-budget candidates | `rollback_gate_001`, `validation_aware_compiler_001`, `traceable_compiler_integration_001` | Gate is deterministic and toy-scale | partially_supported | C |
| compact skill -> agent invocation | COLLEAGUE deployable skill surface; agent skill invocation literature | Skill as agent-facing artifact | No cross-host packaging or installation | API-review agent prompt/output contract for compact skill | `agent_mock_api_review_001`, `llm_agent_api_review_001` | Small controlled matrix; not broad agent stability | partially_supported | B |
| trace verifier / selective trace | SPARK evidence-over-plans principle and trajectory grounding | Agent behavior should expose evidence beyond final answer | Not full trajectories or PDI; only rule-application traces | Selective trace for high-risk/failure-critical rules under token budget | `skill_to_agent_loop_001`, `traceable_compiler_integration_001`, `selective_trace_compiler_001` | Toy trace policy; not a mature tracing strategy | partially_supported | C |
| real effect evaluation | SPARK compares skills against no-skill/human-written skills on runnable tasks | Need task-level effect, not only artifact validity | No 86-task benchmark; no large model/student sweep | 4-case controlled holdout for skill-conditioned API-review behavior | `real_effect_eval_001` | Controlled family only; not benchmark | partially_supported | B |
| posterior skill revision signal | SPARK-PDI posterior evidence over prior plans; COLLEAGUE correction lifecycle | Posterior evidence should matter after deployment | No PDI-like cross-task metric; no broad trajectory suite | Audits recovery gain, attribution specificity, rollback, and trace allocation over existing artifacts | `posterior_revision_signal_audit_001` | Controlled-family diagnostic only; not cross-domain proof | partially_supported | C |

## Repository / Implementation Maturity Audit

This section compares the repositories as engineering artifacts, not only as mechanisms.

### Snapshot Metrics

The following counts exclude `.git`, caches, and for our repository exclude `outputs/` and `external_repos/` to avoid counting generated artifacts and vendored related work as source code.

| Repository | Files | Python Files | Markdown Files | Test-like Files | Python LOC | Markdown LOC | Packaging / Config |
|---|---:|---:|---:|---:|---:|---:|---|
| ours: `D:\solution` | 122+ | 28+ | 56+ | 6+ | ~6.7k+ | ~8.4k+ | minimal `pyproject.toml`; still script-first |
| SPARK-PDI repo | 239 | 29 | 52 | 1 | ~9.5k | ~34.4k | `pyproject.toml`, `uv.lock`, ruff, mypy |
| COLLEAGUE.SKILL repo | 108 | 30 | 57 | 7 | ~8.1k | ~13.0k | `requirements.txt`, install docs, tests, CI-like repo hygiene |

Interpretation:

- Our code volume is not tiny, but it is mostly experiment runners, adapters, and artifact generators.
- SPARK has a more coherent research pipeline package: `spark_skills_gen`, `spark_tasks_gen`, eval scripts, uv environment, lint/type config, and generated task/trajectory assets.
- COLLEAGUE has a more product-like tool structure: `tools/`, `tests/`, install scripts, host integrations, contribution docs, citation/license, and a stable user-facing `SKILL.md`.
- Our current repository is strongest as a reproducible demo/artifact lab, not yet as a reusable library or mature open-source platform.

### Structural Comparison

| Dimension | Ours | SPARK-PDI | COLLEAGUE.SKILL | Maturity Gap |
|---|---|---|---|---|
| Main entrypoints | Many `scripts/run_*.py` slices | `run_pipeline.py`, `run_eval_skills.py`, package modules | slash skill entrypoint plus install scripts | ours lacks one canonical CLI or package API |
| Package structure | `scripts/`, `agents/`, `integrations/`; empty/unused `src/` | importable packages under `spark_skills_gen/` and `spark_tasks_gen/` | tool modules under `tools/` with tests | ours is script-first and not yet library-first |
| Tests | mostly smoke via script execution and generated summaries | limited explicit tests but strong pipeline assets/config | `tests/` with lifecycle/install/research tool tests | ours lacks a formal test suite for core functions |
| Config / tooling | `.gitignore`, `.gitattributes`; no project package config | `pyproject.toml`, `uv.lock`, ruff, mypy config | `requirements.txt`, install docs, CI/workflow directory | ours lacks dependency lock, lint/type policy, CI |
| Data / tasks | small API-review controlled family and Harbor fixtures | task generation/eval artifacts, trajectory data, token budgets | example skills, prompts, references | ours intentionally scoped, but less broad |
| Documentation | many design/audit reports | README plus trajectory/eval docs | README, INSTALL, ROADMAP, CONTRIBUTING, LICENSE, CITATION | ours has rich internal notes but less polished user docs |
| Standards | artifact discipline: summary/manifest per slice | pipeline schemas and token budgets | skill schema, manifest, install lifecycle | ours has standards in docs, but not consolidated as code schema |
| Reproducibility | good for known slices via runbook and artifacts | stronger environment reproducibility through uv | good installation/lifecycle test coverage | ours needs dependency/env standardization |

### File-Level Design Assessment

Current strengths:

- Each experimental slice has a stable output directory.
- Most slices write `summary.json`, `summary.md`, and `manifest.json`.
- Claims are now linked to supporting artifacts through `artifact_claim_audit_001`.
- The prototype covers the full vertical loop rather than only one isolated component.

Current weaknesses:

- Many scripts are long single-purpose runners rather than small reusable modules.
- Core data structures such as `rule_ledger`, `execution_report`, `patch_proposal`, `validation_gate`, and `trace_contract` are not defined as typed schemas or shared classes.
- Test coverage is mostly implicit: rerunning scripts and checking output summaries.
- Error handling is adequate for demo slices but not mature for arbitrary inputs.
- There is no packaged CLI such as `skill-deploy run`, `skill-deploy verify`, or `skill-deploy audit`.
- There is no CI gate for linting, type checks, unit tests, or artifact schema validation.
- Some docs are stronger than the implementation: standards are described but not always enforced in code.

### Component Maturity Grades

These are qualitative grades for current engineering maturity, not research value.

| Component | Current Grade | Reason |
|---|---|---|
| ArtifactStore discipline | B | consistent summaries/manifests across many slices |
| Stable demo loop | B | reproducible controlled loop, Harbor/LLM/mock layers present |
| PatchCompiler | C+ | useful toy mappings, not generalized or typed |
| ValidationGate | C+ | clear deterministic gates, not centralized reusable module |
| InvocationProtocol | C | useful protocol, but overhead and generality unresolved |
| TraceVerifier | C+ | concrete checker exists, partial/selective trace exists, still keyword-based |
| AgentRunner | C | mock and LLM agents exist, but no unified runner interface |
| TaskCase | C | case files exist, but no schema validator or generator |
| Test suite | D+ | script smoke tests exist, formal tests are limited |
| Packaging / CLI / CI | D | not yet packaged, no CI/lint/type workflow |

### What This Means For Claims

Do say:

```text
The current repository is a demo-oriented, artifact-rich prototype with reproducible vertical slices.
```

Do not say:

```text
The current repository is as mature as SPARK-PDI or COLLEAGUE.SKILL as an open-source codebase.
```

Do say:

```text
Compared with related repositories, our current delta is mainly in the controlled deployment loop and risk-budgeted trace exploration, not in repository engineering maturity.
```

Do not say:

```text
Our implementation is already a production-quality platform.
```

### Practical Maturation Targets

If the project continues beyond the demo, the next engineering targets should be:

1. Move reusable logic from `scripts/` into `src/skill_deployment/`.
2. Define typed schemas for `TaskCase`, `SkillPackage`, `ExecutionReport`, `PatchProposal`, `ValidationGateResult`, and `TraceContract`.
3. Add a small CLI wrapper:

```text
skill-deploy run-demo
skill-deploy audit-claims
skill-deploy run-holdout
skill-deploy compare-baselines
```

4. Add unit tests for verifiers, patch selection, gates, and token accounting.
5. Add `pyproject.toml`, dependency lock strategy, ruff/format config, and a CI smoke workflow.
6. Convert component baseline plan into runnable ablation scripts only after the demo story is stable.

## Repository Maturity Patch Status

The repository now includes a minimal maturity patch:

```text
pyproject.toml
src/skill_deployment/
tests/
scripts/validate_task_cases.py
scripts/skill_deploy.py
docs/REPOSITORY_MATURITY_PATCH_PLAN.md
```

This moves the implementation from pure script-first toward a minimal package/schema/test skeleton.

Updated assessment:

- `TaskCase`, token budget, manifest checking, validation gate, and trace helper now have shared modules.
- Fast unit tests cover the new shared helpers.
- A lightweight CLI wrapper calls existing scripts without rewriting the demo.
- Existing outputs and experiment results are unchanged.

Still true:

- The repository is not yet as mature as SPARK-PDI or COLLEAGUE.SKILL.
- Most experimental logic still lives in scripts.
- CI, dependency lock, typed schemas for all artifacts, and a stable public API are still missing.

## Component Baseline Status

The repository now includes the first runnable component attribution baseline:

```text
outputs/mvp_vertical_slice/component_baseline_direct_summary_001
```

Result:

```text
direct_summary_skill avg coverage: 0.92
patched_compact avg coverage: 1.00
```

Interpretation:

- Direct summarization is a meaningful baseline in this controlled API-review family.
- The current prototype should not claim value merely from generating an API-review checklist.
- The safer delta is correctness-constrained deployment: verifier feedback recovers missed failure-critical rules, validation gates prevent risky patches, and selective trace controls observability cost.

Boundary:

```text
This is a small deterministic attribution slice, not evidence that the prototype generally outperforms direct-summary skill generation.
```

## Core Method Spec Status

Current consolidated method spec:

```text
docs/CORE_METHOD_SPEC.md
```

The direct-summary baseline shifts the safe delta:

```text
not: better summarization alone
but: skill deployment under feedback, risk, budget, and traceability constraints
```

## Novelty Pressure Test Status

Current novelty pressure test:

```text
docs/RELATED_WORK_NOVELTY_PRESSURE_TEST.md
```

Current conclusion:

```text
Posterior feedback itself is not novel. The narrower possible delta is typed posterior revision over deployable expert-skill packages: rule-level, output-contract-level, trace-contract-level, and gate-level operators under correctness, budget, and traceability constraints.
```

Current naive revision ablation:

```text
outputs/mvp_vertical_slice/naive_revision_ablation_001
```

Current observation:

```text
always_append_domain_rules fixes missing_rule but fails output_format_error
always_rewrite_output_contract fixes output_format_error but fails missing_rule
always_regenerate_full_skill is a strong high-cost upper bound
always_full_trace blocks shortcut but exceeds budget
type_specific_operator_plus_gate_and_selective_trace is the best-supported narrow combination in current toy slices
```

Second-domain probe:

```text
outputs/mvp_vertical_slice/second_domain_config_security_001
```

Current observation:

```text
In a configuration-security domain, direct summary is strong but misses C006 audit retention;
always-append fails output contract;
always-contract misses C006;
accept-if-fixed regresses C003;
full trace and full skill exceed budget;
typed operator + gate + selective trace is accepted at 166/260.
```

Boundary:

```text
This is still a hand-constructed deterministic probe, not a related-work-scale benchmark.
```

Freeze-and-transfer audit:

```text
outputs/mvp_vertical_slice/operator_transfer_audit_001
```

Prior/posterior split:

```text
outputs/mvp_vertical_slice/prior_posterior_split_001
```

Current interpretation:

```text
The second-domain evidence is stronger when presented as two-domain schematic transfer:
the operator/gate/trace-policy skeleton is reused, while domain-specific adapters handle rule semantics and output fields.
The posterior-evidence claim is strongest where posterior verifier feedback identifies residual misses, wrong repair type,
regression, and trace-budget pressure that prior material signals did not resolve.
```

Current concise claim:

```text
Skill deployment needs risk-budgeted verification, not just better summarization.
```

Supporting diagnostic:

```text
outputs/mvp_vertical_slice/risk_trace_policy_baseline_001
outputs/mvp_vertical_slice/risk_trace_policy_robustness_001
outputs/mvp_vertical_slice/direct_summary_miss_analysis_001
outputs/mvp_vertical_slice/adversarial_trace_verifier_001
```

The risk-trace baseline compares same-size random selective trace against risk-based selective trace. In the toy slice, both use 183/237 tokens, but only risk-based trace covers R005/R006, the failure-critical rules.

The robustness slice enumerates all 15 size=2 trace allocations over R001-R006. Only R005/R006 covers both failure-critical rules. The direct-summary miss analysis shows the only direct-summary failure is R006 idempotency, which patched compact recovers.

The adversarial trace sanity check rejects obvious fake or weak trace evidence, including fake evidence spans, generic triggers, mismatched finding IDs, and rule-id-only traces. This strengthens the traceability contract at toy scale but remains far weaker than SPARK-style trajectory grounding.

Current revision framing:

```text
docs/CONSTRAINED_POST_EXECUTION_REVISION.md
outputs/mvp_vertical_slice/revision_decision_matrix_001
```

This framing clarifies that the current delta is not "we added a budget." The scoped method-discovery question is how post-execution feedback should trigger targeted repair, rollback, semantic audit, trace contracts, or selective trace under correctness and cost constraints.

Boundary:

```text
This is still a scoped method-discovery contribution, not a claim of mature policy optimization or superiority over SPARK/COLLEAGUE.
```

## What Is Baseline Adequate

These parts are adequate for demo but should not be presented as core novelty:

- expert material to full skill;
- evidence map and rule ledger as internal representation;
- Harbor/SPARK-compatible report conversion;
- mock/LLM agent invocation plumbing;
- basic artifact store with `summary.json`, `summary.md`, and `manifest.json`.

## Current True Exploration Points

The current method-discovery points are:

1. Compact deployment under budget while preserving failure-critical rules.
2. Validation gate that rejects regression or over-budget patches.
3. Failure-type-specific patching rather than always regenerating skill.
4. Semantic audit for compressed rules to avoid rule-ID shortcuts.
5. Rule-application trace as a verifier contract.
6. Risk-budgeted selective trace so trace cost is spent on high-risk or failure-critical rules.

## Safe Delta Statement

Use:

```text
We build on COLLEAGUE.SKILL's inspectable skill artifact idea and SPARK-PDI's execution-evidence orientation. Our scoped contribution is a controlled API-review prototype that studies correctness-constrained deployment: budgeted compact skill generation, verifier-driven patching, validation gates, rule-application trace, and risk-budgeted selective trace.
```

Avoid:

```text
We fully reproduce and improve SPARK.
```

Avoid:

```text
We outperform COLLEAGUE.SKILL or replace its skill package system.
```

Avoid:

```text
Every module in this prototype is original.
```

## Bottom Line

This project should be positioned as:

```text
not a simple A+B splice,
not a universal new skill compiler,
but a scoped deployment-oriented exploration built on two related-work ideas:
inspectable skill artifacts and execution-grounded verification.
```
