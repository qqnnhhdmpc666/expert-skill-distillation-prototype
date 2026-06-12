# Architecture And Design

This document explains the current Contract-Grounded Skill Evolution Runtime at a system level.

## Core Positioning

The system is a runtime for testing whether Skill packages can be installed, executed, measured, revised, rejected, and eventually promoted under evidence. It is not a single hard-coded security prompt. It is also not a claim that the current secure-code-review Skill is a production security tool.

## Runtime Flow

```text
Skill package -> install registry -> active pointer -> BackendRunner -> raw output
raw output -> optional live contract normalizer -> strict verifier
verifier -> evidence bundle -> marginal utility / ablation / evolution gate
```

The main runtime state lives under:

```text
outputs/installed_skills/
```

Important files:

- `registry.json`
- `active_skill_pointer.json`
- `active_skill_pointers/<skill_id>.json`
- `install_history.jsonl`
- package versions under `packages/<skill_id>/versions/<version>/`

## Skill Package

A Skill package contains:

- `SKILL.md`: human and agent-facing instructions.
- `manifest.json`: structured runtime metadata.
- capability groups: task-conditioned activation groups.
- output contract: required finding fields.
- boundary metadata: unsupported task families and safety limits.

For `secure_code_review`, current capability groups include:

- `upload_security`
- `config_security`
- `api_or_code_review`
- `auth_access_control`
- `out_of_scope_guard`

The runtime uses the task family to activate one capability group at a time. This is meant to reduce false positives from all-capabilities-always-on prompting.

## Backends

The current runners include:

- `offline_deterministic`: deterministic local baseline.
- `non_oracle_local_semantic`: local non-oracle semantic runner.
- `live_llm_text`: OpenAI-compatible live model runner.
- replay/skeleton runners for bounded Harbor/SWE-bench evidence where applicable.

Live LLM runs use environment variables or CLI parameters for base URL and model. API keys must be process-local and must not be written to artifacts.

## Live Execution Contract

The live output contract is stricter than ordinary prompting:

- Each finding must bind to a capability group.
- `evidence_span` must match an exact complete target line after normalization.
- If evidence is absent, the model must not force a finding.
- Clean or out-of-scope inputs should return no findings or an out-of-scope trace.
- Ambiguous inputs should produce no concrete finding and can be recorded as low confidence / needs review.

The current failure taxonomy is:

```text
schema_error
missing_evidence
non_exact_span
unsupported_evidence
wrong_capability_group
over_reporting
under_reporting
unsupported_scope
low_confidence_needed
normalizer_needed
model_contract_violation
```

## Evidence Normalizer

The normalizer is implemented in:

```text
src/skill_deployment/live_contract.py
```

It may read only:

- original target input
- raw model output
- Skill/runtime metadata
- contract schema

It must not read verifier-only oracle fields such as expected findings or expected evidence spans.

The normalizer does not relax the verifier. Instead, it prepares the model output before strict verification by:

- aligning evidence spans to complete target lines when the span is traceable;
- suppressing low-confidence non-exact evidence from concrete findings;
- suppressing positive observations that are not actual findings;
- recording all actions in `normalization_trace.json`.

Each normalized run keeps:

- `raw_execution_before_normalization.json`
- `normalized_execution.json`
- `pre_normalization_verifier_report.json`
- `post_normalization_verifier_report.json`
- `normalization_trace.json`

## Verifier

The verifier checks:

- expected capability coverage
- false positives
- required schema fields
- weak or unsupported evidence
- regression safety

Verifier-only fields are used only after the model/runner has produced output. They must not be included in agent-visible case input or candidate generation input.

## Marginal Utility

Variant comparison uses the same case/backend/verifier to compare packages. Typical variants include:

```text
no_skill
skill_v1
skill_v2
upper_bound
active_installed
candidate
```

The project records hashes and provenance so a comparison is not just a report-level claim.

## Evolution Loop

The evolution mechanism has these components:

- trajectory/evidence store
- failure contrast
- candidate generation
- strict validation gate
- rejected edit buffer
- promotion decision

Candidates may be generated only from allowed evidence:

- failure report
- verifier feedback
- evidence summary
- normalization trace
- limitation summary

Candidates must not read verifier-only expected answers.

The broad contract improvement candidate improved one auth case but regressed ambiguous false-positive behavior, so it was rejected. The later iterative contract improvement run split the update into narrow candidates and produced staged promotion proposals without auto-installing them. This distinction matters: the system now has both rejection evidence and positive improvement evidence under strict gates.

```text
reports/CONTRACT_IMPROVEMENT_DEMO_STATUS.md
outputs/contract_improvement_demo/contract_improvement_demo_summary.json
reports/ITERATIVE_CONTRACT_IMPROVEMENT_STATUS.md
outputs/iterative_contract_improvement/iterative_contract_improvement_summary.json
```

## QGSE-Pareto Gate

The promotion layer is conservative. A candidate can only be promoted when it strictly improves the relevant score and does not worsen:

- false positives
- schema errors
- unsupported evidence
- clean negative controls
- unsupported limitation behavior
- scope boundaries
- positive-case regressions

Rejected candidates are evidence, not failures of the experiment. They show the safety gate is active. They do not prove that evolution can already generate better Skills.

Staged promotion proposals are also not automatic deployment. They mean a candidate strictly improved the live validation score while preserving false-positive, schema, unsupported-evidence, clean-negative, unsupported-limitation, scope, and positive-regression gates on the declared validation slice.

## Current Maturity Boundary

The project currently supports a research-level claim:

```text
Evidence-grounded Skill lifecycle and contract-grounded live execution are implemented, locally validated, and now include at least one staged candidate-improvement proposal.
```

It does not yet support:

```text
Production security scanning.
Official external security benchmark success.
SWE-bench agent effectiveness.
Broad real-world deployment readiness.
```
