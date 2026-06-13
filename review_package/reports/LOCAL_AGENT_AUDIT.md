# Local Agent Audit

Audit time: 2026-06-08 final audit.

Primary file audited: `agents/local_security_review_agent.py`.

## What It Really Does

The local agent does perform real local I/O:

- reads target assets through `read_all_texts(target_dir)`
- reads skill capabilities from `manifest.json` when present
- falls back to scanning `SKILL.md` for capability ids
- writes `agent_output.json`
- writes `trace.jsonl`
- writes `stdout.log`
- writes `backend_metadata.json`

The trace records target reads and emitted findings.

## What It Does Not Do Yet

The local agent is not yet a semantic security agent.

Findings are generated from the capabilities present in the skill package. The evidence text comes from the built-in `CAPABILITY_TEXT` table, not from semantic analysis of the target file contents.

The `scenario` argument is used for fallback defaults when no manifest or skill text yields capabilities. This means scenario naming can still affect behavior in fallback mode.

## Verifier Coupling

The main generalization suite uses its own deterministic `agent_attempt(...)` output and `verify(...)` function. The local agent smoke run is separate evidence that a command-line runner can read files and write output/trace/metadata.

Therefore, the current local agent does not yet prove that a non-oracle agent independently solves the suite.

## Required Boundary Statement

`local_real_agent` currently is a deterministic local runner, not a semantic agent.

It is useful as a backend interface and trace artifact proof, but it should not be described as an autonomous vulnerability discovery agent.

## Added Non-Oracle Local Smoke

After the final audit, a separate minimal non-oracle local semantic smoke was added:

- `agents/non_oracle_local_security_agent.py`
- `scripts/run_non_oracle_local_agent_smoke.py`
- `outputs/non_oracle_local_agent_upload_001/summary.json`

This path reads the target asset and Skill manifest, extracts evidence spans with simple deterministic detectors, writes trace/stdout/metadata, and is verified by the shared verifier. The upload smoke passes.

Boundary: this is non-oracle and target-grounded, but it is still deterministic heuristic code. It is not an LLM agent and not a Harbor sandbox agent.

## Next Strengthening Step

Connect the generalization suite to the non-oracle agent output path for multiple task families, then replace heuristic detectors with a non-oracle LLM/CLI agent in Harbor. The verifier should continue to read the agent output file produced by that backend.
