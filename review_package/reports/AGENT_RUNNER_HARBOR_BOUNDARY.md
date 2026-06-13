# Agent / Runner / Harbor Boundary

Updated: 2026-06-09

## Three different layers

### Agent

The agent is the task executor.

Examples in this repo:

- `oracle agent`: effectively knows the answer shape and is used to prove substrate plumbing
- `nop agent`: proves a non-oracle Harbor path can fail and emit feedback
- `heuristic agent`: deterministic program logic that reads target files and emits findings
- `live LLM agent`: calls an OpenAI-compatible model and emits `security_report.json`

What the agent owns:

- reading target files
- reading Skill Package content
- deciding which findings to emit
- writing raw execution artifacts such as `security_report.json`, `prompt.md`, `raw_response.txt`, `target_reads.json`

What the agent does not own:

- final success judgment
- typed repair selection
- claim boundary

### Runner

The runner is the execution wrapper.

What the runner owns:

- preparing normalized inputs for a backend
- invoking an agent or replaying a prior execution environment
- collecting stdout/stderr/metadata
- normalizing raw output into `ExecutionReport` plus artifact paths

Current shared local runners:

- `offline_deterministic`
- `non_oracle_local_semantic`
- `live_llm_text`

Current Harbor runner state:

- not full Harbor execution ownership
- now has a minimal read-existing replay adapter:
  - `harbor_llm_repair_upload_replay`
  - `harbor_llm_repair_config_replay`

### Harbor

Harbor is the execution substrate.

It provides:

- sandboxed task packaging
- Docker/WSL execution
- verifier/test harness
- job/trial artifacts

It is not:

- the algorithm
- the repair policy
- the Skill Package method itself
- the agent

## Why this distinction matters

The main algorithmic spine of this project is:

`SkillPackage -> Execution -> VerifierFeedback -> TypedRepair -> Gate -> Skill v2 -> ValidityCard`

Harbor can host one execution segment of that spine, but Harbor is not the spine.

## User-facing interpretation

- a normal user of the prototype does not need Harbor just to understand the method
- a research reviewer does need Harbor-backed evidence for the strongest claims about real sandbox execution
- the current system can be explained without Harbor, but some execution credibility is stronger with Harbor

## Current canonical wording

- Agent: executes a task
- Runner: wraps execution into a normalized backend interface
- Harbor: sandbox/benchmark substrate that can be wrapped or replayed by a runner

## What the new HarborRunner adapter is and is not

It is:

- a minimal `BackendRunner` adapter over existing Harbor repair-loop artifacts
- a way to read Harbor A1/A2 outputs through the same shared system vocabulary used by local backends
- a bridge from strong standalone evidence into the shared system skeleton

It is not:

- a rewrite of Harbor
- a full Harbor backend unification
- proof that every Harbor script is now shared-core

## Artifact anchors

- local runner core: `src/skill_deployment/runner.py`
- Harbor replay loader: `src/skill_deployment/harbor_adapter.py`
- Harbor replay CLI: `scripts/run_harbor_replay_summary.py`
- Harbor upload replay evidence: `outputs/harbor_llm_repair_loop_upload_001/`
- Harbor config replay evidence: `outputs/harbor_llm_repair_loop_config_001/`
