# V1 Walking Skeleton Status

Date: 2026-06-21

## Verdict

```text
core_walking_skeleton = pass
agent_host_qualification = blocked_not_run
external_evaluation_backend = blocked_not_run
independent_llm_judge = implemented_configured_but_auth_blocked
compiler_superiority = not_yet_demonstrated
evolution_improvement = not_yet_demonstrated
```

## Fresh evidence

- Clean venv: `pip install -e .[dev]` passed.
- Installed entry point: `eskill.exe` passed.
- One-command demo on frozen official `PYSEC-2018-28`: passed with `VERSION_IN_RANGE`.
- V1 test suite in clean venv: `24 passed`.
- Existing and V1 combined final regression: `78 passed`.
- Two consecutive installed CLI demos produced the same semantic Bundle digest: `sha256:a458b8005fd99e26820231a21c411fdcb1b9d195d571fd60dbe4e168afbb89f4`.
- Formal DeepSeek judge attempt reached `https://api.deepseek.com/chat/completions` but returned HTTP 401; no Judge pass is claimed.

## Implemented closure

- Source snapshots and EvidenceUnits are stored in CAS and indexed in SQLite.
- Compiler emits Stage 0–9 artifacts, Knowledge IR, Skill IR, Knowledge Projection and source-grounded attestation.
- Unsupported claims are quarantined; conflicting rules remain disputed.
- Direct baseline targets the same Skill IR schema and does not read Compiler intermediates.
- ReleaseBundle pins exact Skill, projection, binding, verifier, permission and dependency digests.
- Runtime distinguishes domain unresolved, parse error, blocked and runtime failure.
- Promotion, rejection and rollback mutate only ActiveBinding through CAS transactions.
- Rollback rebinds the original Bundle digest; existing sessions retain their pinned Bundle.

## Claim boundary

This status supports an executable, evidence-grounded research prototype. The independent Judge contract and formal gate are implemented, but the fresh external attempt was authentication-blocked. It does not support claims of general open-world distillation, stable Skill improvement, AgentHost effectiveness, Harbor parity, or external benchmark performance.
