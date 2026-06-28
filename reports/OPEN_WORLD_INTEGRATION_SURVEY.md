# Open-World Integration Survey

## Agent Backends

| backend | task type | setup complexity | v0 decision |
|---|---|---|---|
| mini-SWE-agent | repo/task command agent | low | primary smoke backend |
| SWE-agent | GitHub issue repair agent | medium | defer |
| OpenHands | full software agent platform | high | defer |

## Public Evaluation Lanes

| lane | v0 decision |
|---|---|
| current public repo-level dependency-use held-out set | main project-aligned micro-lane |
| SWE-bench Lite / Verified | compatibility only |
| Terminal-Bench | defer |
| OpenHands Index | defer |
| CyberSecEval AutoPatchBench | defer |
| SEC-bench | defer |
| JitVul | defer |
| SecCodePLT | defer |

The v0 selection prioritizes Bundle injection traceability, deterministic verifier compatibility, and anti-leakage auditability over breadth.
