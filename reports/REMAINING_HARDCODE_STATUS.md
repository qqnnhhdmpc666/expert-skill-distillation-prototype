# Remaining Hard-Code Status

## Removed Or Reduced

- `SCENARIOS` was removed from `scripts/run_generalization_suite.py`.
- Positive task definitions now come from `data/task_cases/<case>/`.
- Negative controls are marked as `negative_control: true` and are not counted in positive A2 pass.
- Repair action now comes from `verifier feedback type -> revision/repair_policy.json`.
- The verifier no longer remaps weak evidence to `ownership_boundary_missing` by checking `scenario.feedback_type`; it uses `verifier_contract.feedback_overrides`.
- Ablation rows are executable strategy outputs evaluated by the shared verifier/gate path.

## Still Remaining

- Offline deterministic A1 defect injection still uses the task case `typical_feedback` field to decide which controlled defect to inject.
- `agent_attempt(...)` is still a deterministic attempt generator, not a semantic target-reading agent.
- Capability evidence hints are still held in the shared `CAPABILITIES` inventory.
- The non-oracle local semantic backend currently has handcrafted detectors for upload and config only.
- Harbor non-oracle currently uses `nop` as a baseline, which proves execution/feedback plumbing but not solving ability.

## Risk

These remaining shortcuts mean the offline suite should still be described as **stronger controlled evidence**, not strong generalization evidence.

## Next Fix

Replace offline deterministic defect injection with one of:

1. a non-oracle agent output path for each task family;
2. a fixture file under `data/task_cases/<case>/attempts/A1_agent_output.json`;
3. a target-observation rule under `verifier_contract.yaml` that derives failure type from actual output contents.
