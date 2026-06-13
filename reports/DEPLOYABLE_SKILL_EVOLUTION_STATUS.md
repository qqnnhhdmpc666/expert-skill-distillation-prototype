# Deployable Skill Evolution Status

Updated: 2026-06-11

## Current implementation status

P0 is implemented as a deployable Codex Skill + CLI research prototype.

- `skill-deploy health` runs task-case validation, offline suite, review-package validation, and deployable Skill package generation.
- `skill-deploy run-skill` runs one controlled case through the shared Skill pipeline.
- `skill-deploy compare-variants` writes ReSkill-style marginal utility reports for `no_skill`, `skill_v1`, `skill_v2`, and `upper_bound`.
- `skill-deploy qualify` regenerates QGSE Skill Qualification Cards.
- `skill-deploy harbor-skeleton` writes a Harbor live-runner skeleton Evidence Bundle without pretending replay is live execution.
- `skill-deploy build-codex-skill` writes a deployable defensive secure-code-review Skill package.

P1 is implemented as a minimal controlled Skill Evolution Lab.

- Trajectory Store records success, failure, regression/inconclusive evidence without allowing single-trajectory direct Skill edits.
- Failure Contrast and `text_gradient.md` convert known config/API failures into optimizer-facing constraints.
- Candidate Pool and Elite Pool are generated from positive marginal utility evidence.
- Rejected Edit Buffer records no-op and skill-to-execution-gap failures.
- Retirement decisions support `quarantine`, `retire`, and `downgrade`.
- `outputs/installed_skills/evolution_state_registry.json` overlays evolution states on the generated install registry.

P2 is scaffolded but not executed.

- `outputs/external_security_validation/cyberseceval_style_small_sample_scaffold.json` defines the defensive benchmark entry protocol and safety boundary.
- No CyberSecEval/AutoPatchBench/SecureAgentBench/CVE-Bench result is claimed yet.

## Main artifacts

- Deployable Skill package: `outputs/deployable_codex_skill/secure_code_review`
- Marginal utility report: `outputs/validation/skill_marginal_utility/skill_marginal_utility.json`
- Evolution lab summary: `outputs/skill_evolution_lab/secure_code_review/evolution_summary.json`
- Rejected edit buffer: `outputs/skill_evolution_lab/secure_code_review/rejected_edit_buffer.json`
- Retirement decisions: `outputs/skill_evolution_lab/secure_code_review/retirement_decisions.json`
- Evolution state registry: `outputs/installed_skills/evolution_state_registry.json`
- Harbor skeleton: `outputs/harbor_live_skeleton_upload_001/summary.json`
- External security scaffold: `outputs/external_security_validation/cyberseceval_style_small_sample_scaffold.json`

## Current evidence reading

- Upload security has positive controlled marginal utility from `skill_v1` to `skill_v2`.
- Data-quality is not treated as a positive marginal-utility win in the offline comparison because `v2_over_v1_gain` is `0.0`; it is downgraded by the evolution lab despite earlier local-live qualification evidence.
- Local config repair remains quarantined because behavior does not express the revised capability.
- Local API repair remains retired/rejected because the capability patch is effectively no-op and A2 still misses the target capability.
- Harbor live runner is only a P0 skeleton in this implementation pass; existing Harbor replay/live-loop artifacts remain separate evidence.

## Safety boundary

The deployable Skill and external benchmark scaffold are defensive only:

- allowed: defensive detection, explanation, fix recommendation, patch validation
- forbidden: exploit generation, attack-chain execution, unauthorized target testing, reusable exploitation steps in external reports

Current public wording should remain:

> controlled deployable prototype with bounded secure-code-review evidence

