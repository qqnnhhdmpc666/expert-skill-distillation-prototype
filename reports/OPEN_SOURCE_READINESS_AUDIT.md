# Open-Source Readiness Audit

Generated at: `2026-06-12T15:02:16.280017+00:00`

## Checks

| Check | Status | Detail |
|---|---|---|
| doc_exists:README_PROTOTYPE.md | `pass` | README_PROTOTYPE.md |
| doc_exists:docs/QUICKSTART.md | `pass` | docs/QUICKSTART.md |
| doc_exists:docs/CLAIM_BOUNDARY.md | `pass` | docs/CLAIM_BOUNDARY.md |
| doc_exists:docs/ARTIFACT_TYPES.md | `pass` | docs/ARTIFACT_TYPES.md |
| doc_exists:docs/ADDING_A_NEW_SKILL.md | `pass` | docs/ADDING_A_NEW_SKILL.md |
| doc_exists:docs/RUNNING_VALIDATION.md | `pass` | docs/RUNNING_VALIDATION.md |
| doc_exists:docs/TROUBLESHOOTING.md | `pass` | docs/TROUBLESHOOTING.md |
| doc_exists:docs/RELEASE.md | `pass` | docs/RELEASE.md |
| doc_exists:docs/CLEAN_CLONE_SMOKE.md | `pass` | docs/CLEAN_CLONE_SMOKE.md |
| review_package_manifest_exists | `pass` | review_package/MANIFEST.json |
| command_documented:skill-deploy build-codex-skill | `pass` | skill-deploy build-codex-skill |
| command_documented:skill-deploy install --skill outputs/deployable_codex_skill/secure_code_review --version v2 | `pass` | skill-deploy install --skill outputs/deployable_codex_skill/secure_code_review --version v2 |
| command_documented:skill-deploy run-skill --installed secure_code_review | `pass` | skill-deploy run-skill --installed secure_code_review |
| command_documented:skill-deploy compare-variants | `pass` | skill-deploy compare-variants |
| command_documented:skill-deploy defensive-security-mini-suite | `pass` | skill-deploy defensive-security-mini-suite |
| command_documented:skill-deploy holdout-security-mini-suite | `pass` | skill-deploy holdout-security-mini-suite |
| command_documented:skill-deploy non-oracle-validation | `pass` | skill-deploy non-oracle-validation |
| command_documented:skill-deploy activation-ablation | `pass` | skill-deploy activation-ablation |
| command_documented:skill-deploy advanced-evolve | `pass` | skill-deploy advanced-evolve |
| command_documented:skill-deploy live-llm-validation | `pass` | skill-deploy live-llm-validation |
| command_documented:skill-deploy improvement-demo | `pass` | skill-deploy improvement-demo |
| no_forbidden_overclaim_in_docs | `pass` | unsafe_hits=0 |

## Overclaim Scan

| Doc | Line | Match | Boundary context |
|---|---:|---|---:|
| README_PROTOTYPE.md | 15 | production vulnerability scanner | True |
| README_PROTOTYPE.md | 31 | real-world security effectiveness | True |
| docs/CLAIM_BOUNDARY.md | 19 | production vulnerability scanner | True |
| docs/CLAIM_BOUNDARY.md | 21 | SWE-bench success | True |
| docs/TROUBLESHOOTING.md | 59 | production vulnerability scanner | True |
| docs/RELEASE.md | 3 | production vulnerability scanner | True |
| docs/CLEAN_CLONE_SMOKE.md | 26 | real-world security effectiveness | True |

## Release Gap Calibration

- `open_source_prototype_readiness`: `pass`
- `public_release_readiness`: `partial`

Missing for clean public release:
- clean-environment smoke has not been run from a fresh clone
- dependency/requirements lock has not been reviewed as a release artifact
- license and repository metadata are not yet release-complete
- one-command demo is not yet guaranteed in a clean environment

## Decision

- Overall status: `pass`
