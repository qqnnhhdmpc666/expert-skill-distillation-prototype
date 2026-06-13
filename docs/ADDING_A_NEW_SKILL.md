# Adding A New Skill

This repository treats a Skill as an installable package, not a loose prompt fragment.

## Required Package Shape

```text
outputs/deployable_codex_skill/<skill_id>/
  manifest.json
  SKILL.md
  versions/
    v1/
      manifest.json
      SKILL.md
```

`manifest.json` must include:

- `skill_id`
- `version`
- `task_family`
- `capabilities`
- `output_contract`
- `trace_contract`
- `metadata.capability_groups` if task-conditioned routing is required

## Install

```powershell
skill-deploy install --skill outputs/deployable_codex_skill/<skill_id> --version v1
```

The runtime writes:

- `outputs/installed_skills/registry.json`
- `outputs/installed_skills/active_skill_pointers/<skill_id>.json`
- `outputs/installed_skills/install_history.jsonl`

## Run

```powershell
skill-deploy run-skill --installed <skill_id> --case <case_id> --backend offline_deterministic
```

The evidence bundle must record `skill_package_path`, `skill_hash`, `manifest_hash`, task family, and activated capability group.

## Verifier Contract

A verifier should check:

- required capabilities
- evidence binding to the target
- output schema
- false positives
- out-of-scope behavior

Do not expose verifier-only fields to agent-visible task input or candidate generation.

## Promotion

Promotion must be evidence-gated. A candidate needs strict improvement over `active_installed`, no false-positive increase, no schema-error increase, and no scope violation before a staged promotion proposal is even considered.
