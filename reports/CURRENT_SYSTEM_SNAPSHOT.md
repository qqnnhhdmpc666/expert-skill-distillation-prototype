# Current System Snapshot

Updated: 2026-06-09

## Canonical architecture

The canonical controlled path now lives in shared code under `src/skill_deployment/`.

Main modules:

- `task_cases.py`
- `capability_registry.py`
- `verifier.py`
- `repair.py`
- `runner.py`
- `validity.py`
- `harbor_adapter.py`

Canonical lifecycle:

`TaskCase -> SkillPackage -> BackendRunner -> ExecutionReport -> VerifierReport -> TypedRepair -> GateDecision -> Skill v2 -> ValidityCard`

## Backend maturity snapshot

| Backend | Current status | What it proves | Main boundary |
|---|---|---|---|
| `offline_deterministic` | shared and stable | controlled 5-family lifecycle with repair diversity | not semantic execution |
| `non_oracle_local_semantic` | shared and stable | target-grounded local deterministic reads across 5 families | heuristic code, not LLM reasoning |
| `live_llm_text` | shared local runner path | local LLM can read target/skill and participate in controlled repair loops | only narrow local slices |
| `harbor_llm_repair_upload_replay` | replay adapter | Harbor upload loop can be read through shared runner vocabulary | replay only |
| `harbor_llm_repair_config_replay` | replay adapter | Harbor config loop can be read through shared runner vocabulary | replay only |

## Controlled evidence matrix

| Slice | Artifact | Status |
|---|---|---|
| Offline 5-family suite | `outputs/validation/generalization_suite.json` | A2 `5/5` |
| Negative controls | `outputs/validation/negative_controls.json` | passed |
| Verifier stress checks | `outputs/validation/verifier_stress_checks.json` | passed |
| Repair policy alignment | `outputs/validation/repair_policy_alignment.json` | fully aligned |
| Executable ablation | `outputs/validation/ablation_summary.json` | `14` rows |
| Non-oracle local semantic suite | `outputs/validation/non_oracle_local_suite.json` | A2 `5/5` |
| Local live-LLM upload loop | `outputs/live_llm_repair_loop_upload_001/summary.json` | A1 fail -> A2 pass |
| Local live-LLM data-quality loop | `outputs/live_llm_repair_loop_data_quality_001/summary.json` | A1 fail -> A2 pass |
| Local live-LLM config-security loop | `outputs/live_llm_repair_loop_config_security_001/summary.json` | A1 fail -> A2 fail |
| Local live-LLM API-review loop | `outputs/live_llm_repair_loop_api_review_001/summary.json` | A1 fail -> A2 fail |
| Harbor live-LLM upload loop | `outputs/harbor_llm_repair_loop_upload_001/summary.json` | A1 fail -> A2 pass |
| Harbor live-LLM config loop | `outputs/harbor_llm_repair_loop_config_001/summary.json` | A1 fail -> A2 pass |
| Harbor upload repeatability | `outputs/validation/harbor_llm_repeatability_upload.json` | 3-run smoke |
| Shared validity cards | `outputs/validation/skill_revision_validity_cards.json` | `11` cards |

## Current strongest deltas over earlier internal state

1. task cases are no longer only embedded in one orchestration script
2. verifier logic is no longer only script-private
3. offline and local semantic execution now go through `BackendRunner`
4. local live-LLM path also goes through the shared runner
5. Harbor evidence is now partially connected to the shared system through replay adapters
6. revision evidence is summarized with explicit validity cards, not only pass/fail tables
7. repair policy and typed operator vocabulary are now explicitly aligned

## Legacy or historical paths

These exist as historical or compatibility surfaces and should not be presented as the canonical core:

- script-local Harbor launchers
- older Streamlit-assembled demo narratives
- older one-off reports that predate the shared `src/skill_deployment` path

The canonical path for technical explanation should begin with:

- `src/skill_deployment/`
- `data/task_cases/`
- `outputs/validation/`
- selected `outputs/live_llm_*` and `outputs/harbor_llm_*`

## What remains outside the canonical core

1. live Harbor execution itself
2. Harbor verifier normalization
3. broad multi-task live-LLM generalization
4. semantic-strength evaluator or human usefulness review
5. default-on strict evidence binding across every legacy slice

## Best current positioning

This repository is best described as:

> a reproducible controlled research-system skeleton with multi-backend repair-loop evidence

It should not yet be positioned as:

- a mature platform
- a general-purpose agent framework
- a broad real-world vulnerability scanning system
