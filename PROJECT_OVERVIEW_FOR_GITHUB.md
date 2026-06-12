# Contract-Grounded Skill Evolution Runtime

This repository is a research prototype for an Evidence-Grounded / Contract-Grounded Skill Evolution Runtime for live agents.

It is not a production vulnerability scanner, not a complete SPARK reproduction, not a SWE-bench agent, and not an official CyberSecEval, AutoPatchBench, or CVE-Bench result. The current goal is narrower and more research-oriented: make Skill installation, execution, evidence capture, variant comparison, failure attribution, candidate generation, rejection, and rollback observable enough that Skill evolution claims can be tested instead of guessed.

## What The System Does

The runtime packages a task skill as an installable Codex Skill package with:

- `SKILL.md`
- `manifest.json`
- capability groups
- output contracts
- safety boundaries
- evidence bundle paths

The `skill-deploy` CLI can install a Skill, run it on a case, compare versions, run live LLM validation, run ablations, and create evolution candidates. Every meaningful run writes artifacts under `outputs/` and corresponding reports under `reports/`.

## Main Research Idea

Skill evolution should not be driven by a single bad case or a vague sense that a prompt got better. This project treats a Skill like an external, versioned, evidence-bearing control surface:

1. Run a Skill under a defined backend.
2. Collect raw output and verifier feedback.
3. Normalize live output only through contract-safe rules.
4. Compare variants under the same case and verifier.
5. Generate candidates only from allowed failure evidence.
6. Promote only when strict gates show improvement without regression.
7. Keep rejected edits and failed attempts as evidence.

## Current Evidence Snapshot

As of the latest run:

- Controlled installed runtime: pass.
- Local bounded defensive security evidence: strong, but not official external benchmark evidence.
- Contract-grounded live validation: pass on the current 7-case representative live set.
- External/semiexternal generalization: partial, with 9/12 current effective passes, zero false positives, exact evidence matching, and three retained unsupported limitations.
- Live mechanism ablation: supports the router/normalizer/contract mechanism, especially scope discipline and out-of-scope control.
- Evolution improvement: demonstrated as staged promotion proposals in iterative live-contract candidates; candidates are not auto-installed.
- SWE-bench official harness: infra blocked for gold-patch execution due environment image build/dependency download failure.
- Public release readiness: prototype pass.

Key reports:

- `reports/LIVE_CONTRACT_VALIDATION_STATUS.md`
- `reports/EXTERNAL_GENERALIZATION_VALIDATION_STATUS.md`
- `reports/LIVE_MECHANISM_ABLATION_STATUS.md`
- `reports/CONTRACT_IMPROVEMENT_DEMO_STATUS.md`
- `reports/ITERATIVE_CONTRACT_IMPROVEMENT_STATUS.md`
- `reports/REPRESENTATIVE_VALIDATION_MATRIX.md`
- `reports/GRAND_AUTONOMOUS_SPRINT_STATUS.md`

## Quick Start

```powershell
python -m pip install -e .[dev]
skill-deploy build-codex-skill
skill-deploy install --skill outputs/deployable_codex_skill/secure_code_review --version v2
skill-deploy run-skill --installed secure_code_review --case upload_security_001 --backend offline_deterministic
skill-deploy compare-variants --cases upload,config --backend offline_deterministic --source installed
skill-deploy validate-review-package
```

For live LLM runs, configure the API key only as a process environment variable:

```powershell
$env:OPENAI_API_KEY = "<your key>"
skill-deploy live-contract-validation --installed secure_code_review --base-url https://api.deepseek.com --model deepseek-v4-flash
```

Do not commit API keys or write them into artifacts.

## Evidence Types

The project uses explicit evidence types:

- `fresh_run`: produced by an executed command.
- `derived_summary`: summarized from existing artifacts.
- `scaffold`: structure exists but no real execution claim is made.
- `infra_blocked`: infrastructure prevented execution.
- `replay`: replay/read-existing evidence, not fresh live execution.
- `external_official_harness`: produced by an official external harness.

Reports must not treat `infra_blocked`, `scaffold`, or local deterministic evidence as benchmark success.

## Safety Boundary

The security work is defensive only:

- detection
- explanation
- fix recommendation
- patch validation

The project does not generate exploit steps, run attack chains, test unauthorized targets, or claim production scanning coverage.

## Repository Map

- `src/skill_deployment/`: runtime, runners, install state, verifier, live contract normalizer.
- `agents/`: local and live agent wrappers.
- `scripts/`: CLI-backed experiment and validation scripts.
- `data/`: controlled and local defensive cases.
- `outputs/`: generated execution artifacts.
- `reports/`: human-readable status reports.
- `docs/`: user, architecture, release, and reproduction docs.
- `review_package/`: curated review manifest and artifacts.

## Where To Start Reading

1. `docs/USER_GUIDE.md`
2. `docs/ARCHITECTURE_AND_DESIGN.md`
3. `reports/REPRESENTATIVE_VALIDATION_MATRIX.md`
4. `reports/GRAND_AUTONOMOUS_SPRINT_STATUS.md`
5. `HANDOFF_FOR_NEXT_CHAT.md`
