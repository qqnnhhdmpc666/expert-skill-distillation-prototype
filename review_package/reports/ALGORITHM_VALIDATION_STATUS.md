# Algorithm Validation Status

更新时间：2026-06-08 04:13 CST

## Artifacts

```text
outputs/validation/ablation_upload.json
outputs/validation/ablation_config.json
outputs/validation/ablation_summary.json
outputs/validation/ablation_summary.md
```

Command:

```powershell
python scripts\run_ablation_suite.py
```

## Minimal Ablation Conclusion

The controlled ablation compares:

1. A0 naive baseline
2. Skill v1
3. Skill v1 + naive regenerate
4. Skill v1 + always append
5. Skill v1 + typed repair only
6. Skill v1 + typed repair + gate
7. Skill v2 final

Across upload security and config security, `typed_repair_plus_gate` reaches pass while preserving regression safety. `always_append` can recover coverage but has false-positive/regression risk. `naive_regenerate` can solve some cases, but is less stable and fails the config slice.

## Required Questions

1. typed repair + gate 是否比 always append 更可控？

Yes, in this controlled slice. It reaches pass while keeping `regression_safety_score = 1.0`; always append recovers coverage but can keep or introduce unsupported findings.

2. naive regenerate 是否也能解决问题？

Partially. It can pass the upload slice, but fails the config slice because it does not reliably preserve environment-aware negative guards.

3. gate 是否防止 regression？

Yes in the config slice: gate rejects strategies with regression risk and accepts typed repair + gate.

4. feedback type 是否真的决定 repair action？

Yes. `revision/repair_policy.json` maps feedback types to repair actions, and `runs/generalization/*/revision/gate_decision.json` references the taxonomy/policy artifacts.

5. 当前证据强度是什么？

Controlled minimal evidence. It supports the design choice that typed feedback + constrained repair + gate is more controllable than blind append/regenerate in these cases. It is not large-scale algorithm proof.
