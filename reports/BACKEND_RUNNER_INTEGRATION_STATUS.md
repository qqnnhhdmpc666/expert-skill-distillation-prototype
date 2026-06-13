# Backend Runner Integration Status

## Result

Current status: **BackendRunner now owns three stable local backends and one minimal Harbor replay surface**.

Integrated backends:

- `offline_deterministic`
- `non_oracle_local_semantic`
- `live_llm_text`
- `harbor_llm_repair_upload_replay`
- `harbor_llm_repair_config_replay`

Shared entrypoint:

- `src/skill_deployment/runner.py::get_backend_runner(...)`

Concrete implementations:

- `OfflineDeterministicRunner`
- `NonOracleLocalSemanticRunner`
- `LiveLLMSecurityRunner`
- `HarborReplayRunner`

## What changed

`scripts/run_generalization_suite.py` no longer directly owns the main backend execution branches for offline and local semantic attempts. `scripts/run_live_llm_upload.py` also no longer shells directly into the LLM agent; it now goes through the same runner registry. The shared pattern is:

1. loads `TaskCase`
2. constructs `SkillPackage`
3. selects a backend runner
4. calls `runner.run(...)`
5. passes the resulting `ExecutionReport` into the shared verifier

## What is still missing

1. live Harbor execution is still driven by adapter-style scripts, not full `BackendRunner` implementations
2. the new Harbor integration is replay/read-existing only
3. `RunnerResult` is still a thin wrapper and does not yet fully standardize raw-output, trace, and error artifacts across all backends
4. the generalization suite still intentionally rejects `live_llm_text` because only the upload local slice has controlled evidence

## Verification

- `python scripts/run_generalization_suite.py --backend offline_deterministic --scenarios upload,auth,config,api_review,data_quality` -> PASS, 5/5 A2
- `python scripts/run_generalization_suite.py --backend non_oracle_local_semantic --scenarios upload,auth,config,api_review,data_quality` -> PASS, 5/5 A2
- `python scripts/run_live_llm_upload.py` -> PASS when RightCode/OpenAI-compatible env is configured
- `python scripts/run_harbor_replay_summary.py --backend harbor_llm_repair_upload_replay --attempt A1` -> PASS
- `python scripts/run_harbor_replay_summary.py --backend harbor_llm_repair_config_replay --attempt A2` -> PASS
- `python -m pytest -q` -> PASS, runner registry tests included
