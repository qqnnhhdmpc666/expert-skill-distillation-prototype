# Implementation Gap Analysis

This note records the code-level comparison made against the public SPARK and COLLEAGUE.SKILL repositories, and maps the ideas that were folded into this prototype.

## Repositories Checked

- SPARK: `EtaYang10th/spark-skills`
  - Full `git clone` and zip download were unstable on the local network because large repository objects timed out or reset.
  - GitHub API access succeeded, so the core source files were downloaded into `C:\Users\31552\Documents\New project\.codex-downloads\spark-skills-api`.
  - Inspected modules include `spark_skills_gen/pipeline.py`, `trajectory.py`, `skill_evidence.py`, `summarizer.py`, `judge.py`, `evaluator.py`, and `dashboard/`.
- COLLEAGUE.SKILL: `titanwings/colleague-skill`
  - Cloned into `C:\Users\31552\Documents\New project\.codex-downloads\colleague-skill`.
  - Inspected modules include `tools/skill_schema.py`, `tools/skill_writer.py`, `tools/version_manager.py`, `prompts/correction_handler.md`, and related tests.

## What SPARK Does Better

SPARK is built around an execution-first loop:

`execute -> judge -> reflect -> retry -> distill`

Its strongest implementation ideas are:

- Append-only `trajectory.jsonl` for every important event.
- `attempts.json` as a compact attempt history.
- Verifier reward/status as the main front-stage signal, not internal rule IDs.
- A live dashboard showing task list, attempt cards, reflection memo, prompt/response toggles, and PDI exploration dynamics.
- Evidence blocks for skill generation: task pattern, success execution chain, verification signals, failed-attempt lessons, environment affordances, and raw support tail.
- Token budgets are centralized and visible.

## What COLLEAGUE.SKILL Does Better

COLLEAGUE.SKILL is stronger as an installable, evolving skill package:

- Normalized `meta.json` / `manifest.json`.
- Explicit lifecycle fields: version, updated time, correction count, status.
- Separate generated artifacts with stable names.
- Correction handling as a first-class update mode.
- Version archival and rollback under `versions/`.
- Tests for writer, installer, lifecycle, and compatibility behavior.

## Changes Imported Into This Prototype

The current prototype now borrows the following implementation patterns:

- `skills/skill_v*/meta.json`: normalized package metadata inspired by COLLEAGUE.SKILL.
- `revision/correction_report.md`: a human-readable posterior correction document, so detailed repair logic does not clutter the main page.
- `summary/front_stage_metrics.json`: front-stage metrics for status chain, capability coverage, added findings, gate decision, and token cost.
- `summary/online_optimization_metrics.json`: SPARK-inspired online optimization metrics with evidence grounding and plan-stagnation risk.
- `attempts/attempts.json`: compact A0/A1/A2 attempt history.
- `trajectory/online_trajectory.jsonl`: append-only event stream for execution, posterior feedback, metric snapshots, and final summary.
- Main Streamlit view now foregrounds metrics and report improvement; internal rule IDs remain in the developer view.

## Remaining Gaps

- The current verifier is deterministic and template-bound; SPARK executes tasks in real environments and judges reward from actual task outcomes.
- Our trajectory is generated from a controlled demo run; SPARK records live agent commands, stdout, tests, and verifier artifacts.
- Our online metrics are a proxy inspired by PDI, not the full SPARK PDI implementation.
- The prototype does not yet have true version rollback tooling like COLLEAGUE.SKILL.
- The custom scene builder still normalizes user material into a controlled security-review template; it is not a general skill generator.

## Next Engineering Steps

1. Add a small version manager for generated Skill Packages:
   - archive `skill_v1` before patching,
   - expose `versions/`,
   - support rollback for a rejected patch.
2. Convert `trajectory/online_trajectory.jsonl` from synthetic replay into incremental writes during each Streamlit stage click.
3. Add a real PDI-like metric implementation over the A0/A1/A2 traces:
   - execution evidence growth,
   - repeated-plan/stagnation score,
   - weighted intervention score.
4. Add tests that validate:
   - every artifact referenced by `meta.json` exists,
   - trajectory events are well-formed JSONL,
   - correction report links to patch and verifier files.
5. Keep the user-facing page concise:
   - show pass rate / evidence growth / token cost / report diff,
   - move rule IDs and compiler internals to the developer view.

