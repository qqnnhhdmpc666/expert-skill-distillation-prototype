# SPARK-PDI / COLLEAGUE.SKILL Borrowing Notes

## Access status

- Attempted to clone `https://github.com/EtaYang10th/spark-skills` into `external_repos/spark-skills`.
- Attempted to clone `https://github.com/titanwings/colleague-skill` into `external_repos/colleague-skill`.
- Local `git clone` stalled on the current network, so implementation work used public paper/repository pages as design references. No private or unverified code was copied.

## Borrowed design ideas

### From SPARK-PDI

Source: arXiv `2605.09192`, "Evidence Over Plans: Online Trajectory Verification for Skill Distillation".

Transferred into the demo:

- Treat generated skills as posterior artifacts, revised after an observed attempt rather than trusted as prior plans.
- Preserve run evidence as first-class artifacts: `A1_trace.jsonl`, verifier report, patch proposal, gate decision, A2 rerun report.
- Make the UI show `agent observed findings -> verifier computed missing rules -> patch -> rerun`.
- Use trace policy and verifier contracts to make claims inspectable.

Not claimed:

- Full SPARK reproduction.
- Full PDI metric implementation.
- 86-task benchmark or student-model transfer results.

### From COLLEAGUE.SKILL

Source: public `titanwings/colleague-skill` README and `COLLEAGUE.SKILL` arXiv page.

Transferred into the demo:

- Skill is represented as a package, not a single prompt.
- Package files are inspectable and versioned: `manifest.yaml`, `SKILL.md`, `rules/*.yaml`, `contracts/*`, `trace_policy.yaml`, examples, eval cases, changelog.
- The package has capability and behavior boundary tracks.
- The demo now separates reusable skill package directories from run artifact directories.
- The UI shows v1 -> v2 directory-level diff and rollback/gate reasoning.

Not claimed:

- Persona distillation.
- Multi-source workplace ingestion.
- One-command host installation.
- Full version manager equivalent to the upstream project.

## Current local implementation

- Reusable skill packages are written to `skill_packages/<scenario>/<version>/`.
- Per-run evidence is written to `runs/demo_session_<scenario>_<mode>/`.
- The Streamlit UI now has:
  - `专家材料包` view instead of a thin rule list.
  - `Skill Package` directory view.
  - Directory-level diff.
  - Hidden expected rule IDs inside the verifier contract rather than prominently exposing answers.

