# Generalization Audit

Audit time: 2026-06-08 final audit.

## Scope

This audit checks whether the four-task generalization suite is evidence for a shared controlled pipeline, or merely four unrelated hard-coded demos.

Primary file audited: `scripts/run_generalization_suite.py`.

## Shared Pipeline Modules

All selected scenarios call the same top-level function:

- `select_scenarios(...)`
- `materialize_task_case(...)`
- `run_scenario(scenario, backend)`
- `agent_attempt(...)`
- `verify(...)`
- `repair(...)`
- `render_skill(...)`
- unified JSON/Markdown artifact writers

Inside `run_scenario`, every case follows the same lifecycle:

1. materialize task case
2. write source material, target asset, and task spec
3. run A0 no-skill attempt
4. build Skill v1
5. run A1 with an injected defect
6. verify A1
7. repair from verifier feedback
8. gate the repair
9. build Skill v2
10. run A2
11. write provenance, execution trace, feedback trace, revision trace, and metrics

The metrics are computed with the same `verify(...)` function for all scenarios:

- capability coverage
- evidence binding
- output contract
- regression safety
- trace observability

## Task-Specific Inputs

Task-specific content now lives in `data/task_cases/<case>/` and is loaded by `scripts/run_generalization_suite.py` at runtime. Negative controls are marked with `negative_control: true` and are skipped by the positive generalization suite.

Per-scenario inputs loaded from the task-case directory include:

- `key`
- `aliases`
- `title`
- `family`
- `expert_material`
- `target_asset`
- `expected`
- `v1`
- `feedback_type`

The capability inventory is shared in `CAPABILITIES`, but each scenario selects different expected and v1 capability subsets.

## Scenario Hard-Code Audit

There is no large branch such as `if scenario == upload/auth/config/api_review`.

The previous embedded `SCENARIOS` table has been removed. The runner now discovers task cases from `data/task_cases/` and uses aliases derived from case id / task family.

Remaining task-conditioned shortcuts:

- `agent_attempt(...)` injects defects based on the task case `typical_feedback` field.
- `verify(...)` remaps weak evidence to `ownership_boundary_missing` when `scenario.feedback_type == "ownership_boundary_missing"`.
- agent output is still deterministic and capability-driven.

## Reasonable Task Conditioning

These parts are reasonable for a controlled 0.1 prototype:

- each task has its own expert material and target asset
- each task has expected capabilities
- each task can define a v1 compact skill with known omissions or weaknesses
- verifier metrics are uniform while the expected capability set is task-conditioned

This is normal dataset conditioning, not necessarily evidence of cheating.

## Unreasonable Or Weak Shortcuts

These parts reduce the strength of the generalization claim:

- feedback-type remapping partly depends on scenario metadata
- agent output is deterministic and capability-driven, not semantic target reasoning

These are acceptable if presented as controlled evidence, but not if presented as broad generalization.

## Conclusion

Evidence strength: **stronger controlled evidence**.

The suite shows one reusable lifecycle running across four task families with different feedback types, repair actions, traces, and A2 verification results. It is stronger than four isolated screenshots and stronger than the earlier embedded-scenario version because task definitions are now loaded from `data/task_cases/<case>/`.

It does not yet provide open-world generalization evidence because the attempt generator remains deterministic and task-conditioned. The next strengthening step is to replace deterministic attempt generation with a non-oracle semantic/LLM/CLI agent path across more than one task.
