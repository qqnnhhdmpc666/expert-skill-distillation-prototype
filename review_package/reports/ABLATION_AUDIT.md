# Ablation Audit

Audit time: 2026-06-08 final audit.

Primary files audited:

- `scripts/run_ablation_suite.py`
- `outputs/validation/ablation_summary.md`
- `outputs/validation/ablation_summary.json`

## What Is Fair

The ablation rows use the same conceptual task slices for each compared strategy:

- upload security
- config security

The same score fields are reported for every row:

- task pass
- capability coverage
- evidence binding
- output contract
- regression safety
- trace observability
- cost budget
- missing capabilities
- repaired capabilities
- regression count
- gate decision

The table clearly shows the intended contrast:

- `always_append` may recover coverage while preserving or introducing regression risk
- `naive_regenerate` is unstable across the two controlled scenarios
- `typed_repair_plus_gate` keeps regression safety in the controlled rows

## Executable Upgrade

The ablation suite has been upgraded from a hand-authored table to executable strategy rows. Each strategy now emits findings and is evaluated by the shared verifier/gate path.

Executable strategies:

- `A0_naive_baseline`
- `Skill_v1`
- `Skill_v1_plus_naive_regenerate`
- `Skill_v1_plus_always_append`
- `Skill_v1_plus_typed_repair_only`
- `Skill_v1_plus_typed_repair_plus_gate`
- `Skill_v2_final`

The suite still covers upload and config slices and writes `outputs/validation/ablation_summary.json/md`.

## What Is Not Yet Fair Enough For A Strong Empirical Claim

The current ablation suite is executable controlled evidence, but it is still not a broad empirical benchmark.

Specific limitations:

- strategy implementations are simple deterministic policies
- `naive_regenerate` uses a fixed global prior, not an actual LLM regenerate
- `typed_repair_plus_gate` uses the controlled verifier report and repair policy, not a learned repair policy
- only two task slices are included

## Conclusion

Evidence strength: **moderate controlled evidence**.

The ablation is now stronger as engineering evidence because the rows are produced by executable strategy runners. It should still not be presented as a statistically meaningful experiment or broad algorithm benchmark.

## Next Strengthening Step

Replace deterministic strategy policies with live LLM / CLI strategy runners, and expand ablation beyond upload/config.

Each strategy should still consume the same A1 verifier report and task artifact directory, produce its own patch/output, and be evaluated by the same verifier/gate implementation.
