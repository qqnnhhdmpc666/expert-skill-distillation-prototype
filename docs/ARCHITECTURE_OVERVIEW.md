# Architecture Overview

## 1. System Flow

```text
expert materials
-> Skill Distiller
-> full_skill.md
-> evidence_map.json
-> rule_ledger.json
-> Compact Skill Builder
-> compact_skill_v1.md
-> Agent Execution
-> review.json
-> Harbor / local verifier
-> execution_report_spark.json
-> Feedback-to-Patch
-> compact_skill_v2.md
```

## 2. Core Artifacts

| Artifact | Role |
|---|---|
| `full_skill.md` | Complete review skill for audit and maintenance |
| `evidence_map.json` | Maps each rule to source material evidence |
| `rule_ledger.json` | Internal decision representation for keep/drop/patch |
| `compact_skill_v1.md` | Lightweight invocation skill before execution feedback |
| `execution_report_spark.json` | Unified execution feedback format |
| `repair_log*.md` | Human-readable explanation of patches |
| `compact_skill_v2.md` | Deployment skill after feedback patch |
| `validation_gate.json` | Checks whether a patch is accepted |

## 3. Feedback Types

Current vertical slices:

| Failure Type | Signal | Patch Target | Patch Action |
|---|---|---|---|
| `missing_rule` | Missing R005/R006 | domain rule | `patch_into_compact_v2` |
| `output_format_error` | Missing required JSON fields | output contract | `rewrite_output_contract` |

## 4. Execution Layers

| Layer | Status | Purpose |
|---|---|---|
| deterministic baseline | complete | proves artifact flow |
| SPARK fixture | complete | proves adapter interface |
| real Harbor verifier | complete | proves Docker verifier feedback |
| mock agent + Harbor | complete | proves compact skill drives review.json |
| RightCode GPT + local verifier | complete | proves real LLM can be skill-conditioned in this slice |

## 5. Decision Policy Exploration

Current exploratory policies:

| Policy | Meaning |
|---|---|
| priority-only | Keep high-priority supported rules |
| risk-cost | Select rules under token budget using risk/cost score |
| execution-aware-risk-cost | Add prior failure-critical rules into compact selection |

This is exploratory only. The current result is a small-slice comparison, not a benchmark.
