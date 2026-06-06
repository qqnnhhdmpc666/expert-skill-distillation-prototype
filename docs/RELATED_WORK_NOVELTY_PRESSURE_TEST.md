# Related-Work Novelty Pressure Test

Date: 2026-06-06

## Purpose

This document pressure-tests the current method idea against related work. It starts from the skeptical position:

```text
posterior feedback drives revision is not novel by itself
```

Many agent-improvement, prompt-repair, program-repair, and memory-update systems use execution feedback to update something. Therefore the possible delta must be narrower:

```text
posterior feedback is mapped to typed revision operators over a deployable expert skill package,
then promoted only through deployment-level gates involving regression, budget, semantics, and traceability.
```

This remains a method hypothesis, not a proven contribution.

## Pressure-Test Dimensions

| Dimension | Question |
|---|---|
| revised artifact | Is the object being revised a prompt, policy, memory, program, trajectory, or deployable expert-skill package? |
| posterior evidence | What feedback arrives after execution? |
| revision unit | Is the update coarse-grained or split into rule/output-contract/trace-contract/gate records? |
| failure-type distinction | Does the method choose different revision operators for different failure types? |
| regression validation | Does it reject a patch that fixes one failure but breaks prior coverage? |
| compression semantics | Does it check whether compacted content still has executable semantics? |
| trace budget allocation | Does it decide where to spend trace/evidence cost? |
| expert-skill deployment target | Is the target specifically a deployable expert skill artifact? |

## Component Pressure Matrix

| Work / Category | Revised Artifact | Posterior Evidence Used | Revision Unit | Failure-Type-Specific Operator? | Regression Gate? | Compression Semantics? | Trace Budget Allocation? | Expert-Skill Deployment Target? | What Remains Different In Our Work |
|---|---|---|---|---|---|---|---|---|---|
| SPARK-PDI / trajectory-based skill distillation | skill distilled from execution trajectories | environment-verified execution trajectory and PDI-like posterior signal | trajectory/skill evidence | partly, through trajectory verification diagnostics rather than our rule/contract/trace operator split | validates trajectory evidence; not our compact deployment promotion gate | not the main focus | not the main focus | skill distillation, but not expert-material deployment package in our form | Our current gap is narrower: typed revision and promotion of compact expert-skill deployment artifacts after verifier feedback. |
| COLLEAGUE.SKILL / versioned skill artifact | inspectable, correctable skill package | expert/person traces, corrections, lifecycle feedback | skill package / correction lifecycle | has correction lifecycle, but not our current failure taxonomy/operator ablation | versioning/correction support, but not our current budget/regression/trace gate combination | not central | not central | yes, closest artifact inspiration | We inherit the artifact idea; current novelty pressure is whether deployment-time typed revision/gating adds a distinct mechanism. |
| Reflexion / self-improving agent | agent memory/reflection | verbal feedback from task outcome | reflection memory | generally coarse task reflection, not rule/output/trace contract split | retries improve future attempts, but not deployment package promotion gate | no | no | no | Shows posterior feedback is not novel; our possible delta is artifact granularity and deployment gate. |
| Self-Refine / iterative self-feedback | model output | self-generated feedback | output revision | feedback-guided output edits, usually not typed expert-skill operators | checks improved output, not package regression across prior coverage | no | no | no | Covers iterative feedback, but not versioned expert-skill package deployment. |
| Voyager / tool-agent skill library | executable skills/code in a lifelong agent library | environment feedback and self-verification | code skill / library entry | updates skills, but not our rule/output-contract/trace-contract split | skill library has validation, but not our compact-skill promotion gate | no | no | partly skill library, not expert-material skill artifact | Closest in skill-library spirit; our target is distilled expert-review rules as deployable artifacts. |
| Prompt optimization / OPRO / PromptAgent | prompt text | task score, evaluation feedback, search signal | prompt candidate | may use task scores, not typed failure-to-operator mapping | selected by eval score, not artifact regression/trace gate | no | no | no | Strong pressure against claiming prompt repair novelty; our delta must be artifact-level typed revision. |
| Program repair / SWE-agent style repair | code or repository state | tests, CI, issue feedback | code patch | yes, failure often maps to code edits | tests/CI are strong regression gates | not about skill compression | no | no | Strong pressure: verifier-guided patch and regression tests are known. Our remaining gap is expert-skill package operators and trace budget. |
| Tool-agent memory / skill update systems | memory, tool-use policies, learned routines | task outcome and user/environment feedback | memory item or skill routine | sometimes | sometimes via task success | not central | not central | not specifically expert-skill deployment package | Covers broad feedback update; our claim must stay narrower. |
| Current prototype | compact expert-skill deployment package | verifier/Harbor/trace feedback | rule, output contract, trace contract, gate record | yes in toy slices: missing_rule, output_format_error, regression, semantic compression, shortcut, fake trace, trace budget | yes in toy slice: reject_and_rollback | yes via semantic audit | yes via selective trace | yes, controlled API-review expert skill | Narrow method prototype: typed posterior revision of deployable expert-skill package under correctness/budget/traceability constraints. |

## Pressure-Test Result

The broad statement is not novel:

```text
use posterior feedback to revise a system
```

The narrower candidate still has some room:

```text
typed posterior revision over deployable expert-skill packages
```

Specifically:

- The revised object is not just an agent prompt, memory, policy, or generated answer.
- The revision units are explicitly split into `compact_rules`, `output_contract`, `trace_contract`, and `promotion_gate_record`.
- Different failure types trigger different revision operators.
- A patch is not promoted only because it fixes the current failure; it must pass deployment-level checks for regression, budget, semantics, and trace evidence.
- Trace is treated as a limited verification resource, not an all-or-nothing logging option.

## Current Weaknesses

The novelty pressure remains high:

- Program repair already has verifier-guided patch and regression testing.
- Reflection and self-improvement already use feedback to revise agent behavior.
- COLLEAGUE already gives strong pressure on versioned/correctable skill artifacts.
- SPARK already gives strong pressure on posterior execution evidence for skill distillation.

Therefore, the current project should not claim a broad new paradigm.

## Stronger Current Positioning

Use:

```text
We explore typed posterior revision for deployable expert-skill packages:
execution feedback is attributed to rule-level, output-contract-level, trace-contract-level, or gate-level operators,
and candidate revisions are promoted only if they pass deployment constraints such as regression, budget, semantic preservation, and traceability.
```

Avoid:

```text
We introduce posterior feedback revision for agents.
```

Avoid:

```text
Posterior Skill Revision is already a general new framework.
```

## Required Next Evidence

To make the narrow method more credible, the next evidence should include:

1. A naive revision ablation:

```text
always append
always regenerate
always rewrite output contract
always full trace
accept if current failure fixed
type-specific operator + gate + selective trace
```

2. A second domain probe:

```text
not necessarily large-scale, but outside API review
```

3. A prior-vs-posterior split:

```text
which risk signals were known before execution, and which only appeared after verifier feedback?
```

4. A stronger negative result policy:

```text
if always regenerate or generic repair wins under acceptable cost, downgrade the method claim.
```

## Current Supporting Artifact

The first naive revision ablation is:

```text
outputs/mvp_vertical_slice/naive_revision_ablation_001
```

Current expected interpretation:

```text
type-specific operator + deployment gate + selective trace is the best-supported narrow mechanism combination in the current toy slices,
but always_regenerate_full_skill remains a strong upper bound and must be treated honestly.
```
