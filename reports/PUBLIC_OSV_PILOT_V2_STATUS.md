# Public OSV Pilot v2 Status

Date: 2026-06-23

```text
frozen_public_records = 10
case_count = 33
build_dev_heldout = 20 / 6 / 7
reference_runtime_passed = 33
reference_runtime_failed = 0
false_safe_count = 0
```

Fresh commands:

```powershell
python scripts\build_public_osv_pilot.py --from-frozen
python scripts\run_public_osv_pilot.py `
  --state-dir .tmp\public-osv-pilot-v2-state-final `
  --output outputs\public_osv_pilot\reference_runtime_results_v2.json
```

The frozen pilot now covers affected and fixed boundaries, package absence, missing
advisories, unknown versions, false and unknown environment markers, unsupported syntax,
and conflicting duplicate pins. Inputs and evaluator gold remain separate. The split is a
stable hash split over case ids.

This is public-data evidence for deterministic source ingestion, retrieval projection,
version applicability, unresolved behavior, and false-safe controls. It is not an AgentHost
result and does not demonstrate Compiler superiority.
