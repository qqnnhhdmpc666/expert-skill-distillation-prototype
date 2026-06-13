# Metamorphic Verifier Stress Plan

## Purpose

The current verifier can check controlled contracts, but a fixed verifier can still be overfit. Metamorphic stress tests reduce the chance that Skill promotion is based on reward hacking or a single visible answer.

Metamorphic testing asks: if the input changes in a known way, how should the output change?

## Minimum Test Families

### Upload Security

| Transform | Expected relation | Failure caught |
|---|---|---|
| Remove upload type weakness from target. | `UPLOAD_TYPE_MAGIC` finding should disappear. | False positive / append-style repair. |
| Remove audit-log weakness from target. | `UPLOAD_AUDIT_RETENTION` finding should disappear. | False positive / ungrounded capability. |
| Replace evidence span with unrelated text. | Verifier should reject unsupported evidence. | Fake evidence. |
| Swap target asset with clean config target. | Upload findings should be rejected. | Target binding failure. |
| Rename variables without changing behavior. | Findings should remain semantically stable. | Brittle evidence matching. |

### Config Security

| Transform | Expected relation | Failure caught |
|---|---|---|
| Use a clean production config. | No config security findings should appear. | False positive. |
| Move debug flag from prod to dev-only context. | Production debug finding should disappear. | Environment binding failure. |
| Remove hardcoded secret. | Secret finding should disappear. | Stale append. |
| Change comments only. | Findings should not materially change. | Comment overfitting. |
| Drop required `recommended_fix`. | Verifier should fail schema/contract. | Output contract weakness. |

### Data Quality

| Transform | Expected relation | Failure caught |
|---|---|---|
| Add duplicate rows. | Duplicate finding should appear. | Missed capability. |
| Remove missing values. | Missing-value finding should disappear. | False positive. |
| Shuffle row order. | Findings should stay stable. | Order sensitivity. |
| Rename columns with mapped aliases. | Findings should preserve if alias map is supplied. | Brittle field binding. |
| Remove `recommended_fix`. | Verifier should fail contract. | Schema weakness. |

### API Review

| Transform | Expected relation | Failure caught |
|---|---|---|
| Add an endpoint with overbroad access. | `API_OVERBROAD_RISK` should appear. | Missed capability. |
| Restrict the endpoint correctly. | Overbroad risk should disappear. | False positive. |
| Keep schema but change path names. | Schema-contract findings should stay stable. | String-only matching. |
| Remove evidence span. | Verifier should reject unsupported evidence. | Fake evidence. |

## Hidden/Visible Split

Promotion should not rely only on visible verifier checks. For each family, keep:

- visible checks for development and debugging;
- hidden or withheld variants for qualification;
- clean controls to detect append-only repair;
- swapped-target controls to test target binding.

The project does not yet have a full hidden-verifier benchmark. Current negative controls and strict target binding are first steps only.

## Recommended Artifacts

Future runs should write:

- `outputs/validation/metamorphic_stress_<scenario>.json`
- `reports/METAMORPHIC_STRESS_STATUS.md`

Each row should include:

- `base_case`
- `transform`
- `expected_relation`
- `actual_relation`
- `verifier_pass`
- `failure_origin`
- `promotion_impact`

## Promotion Impact

Metamorphic failure should not always invalidate the original task result, but it must limit promotion:

- single task pass, no metamorphic checks -> at most `L1_CANDIDATE` or `L2_PROMOTE_LOCAL`;
- controlled pass plus negative/metamorphic support -> can support `L3_PROMOTE_CONTROLLED`;
- Harbor pass plus repeatability/metamorphic support -> can support `L4_PROMOTE_SANDBOXED`;
- human/external task review remains required for `L5_PROMOTE_REVIEWED`.

## Immediate Next Implementation

The smallest high-value implementation is now available:

```powershell
python scripts/run_metamorphic_stress.py
```

Outputs:

- `outputs/validation/metamorphic_stress_minimal.json`
- `reports/METAMORPHIC_STRESS_STATUS.md`

Current minimal checks:

1. Upload clean-target transform: remove upload type/audit weakness and confirm appended findings are rejected.
2. Config clean-production transform: confirm append-style config findings are rejected.
3. API injected-risk transform: add an overbroad endpoint and confirm `API_OVERBROAD_RISK` appears.
4. Data-quality row-shuffle transform: confirm findings are stable under row ordering.

These tests would directly address the most important concern: whether the system is learning deployable behavior or only matching a fixed verifier.

## Agent-Level Stress

Verifier-level stress checks whether the verifier accepts/rejects known relations. Agent-level stress checks whether an agent reads the transformed target and produces the expected changed output.

Current agent-level entry point:

```powershell
python scripts/run_agent_level_metamorphic_stress.py
```

Outputs:

- `outputs/validation/agent_level_metamorphic_stress_001/summary.json`
- `reports/AGENT_LEVEL_METAMORPHIC_STRESS_STATUS.md`

Current boundary: this is a deterministic local semantic agent stress, not live LLM or Harbor evidence. Failures are intentionally retained because they reveal detector brittleness and false-positive risk under transformed targets.
