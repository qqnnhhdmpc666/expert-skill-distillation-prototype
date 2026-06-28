# Benchmark Alignment Notes v0

## A. Skill-Generation Benchmarks

SkillGenBench / Anything2Skill-style evaluation starts from external knowledge corpora such as docs, manuals, logs, or trajectories and evaluates generated skill artifacts with fixed downstream executors. This is the closest future path for testing source-material-to-skill generation.

## B. Skill-Usage Benchmarks

SkillsBench-style evaluation starts from a task plus curated skill and checks whether an agent can use that skill under a deterministic verifier. This maps to our Bundle injection and usage layer.

## C. Agent Benchmarks Requiring Source-Material Construction

SWE-bench, OSWorld, and Terminal-Bench-style tasks are ordinary agent benchmarks. They require separate source-material construction and harness readiness before they can evaluate this system.

## Immediate Path

1. Document-to-Agent E2E v0 for runnable proof.
2. SkillGenBench / Anything2Skill-style mapping for skill generation.
3. SkillsBench-style comparison for skill usage.
4. SWE-bench only after Docker and official harness execution are ready.
