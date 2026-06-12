# Contract-Grounded Runtime Patch Index

Date: 2026-06-12

This index describes the local implementation changes from the Codex workspace. It was uploaded through the GitHub connector because the local directory is not a git repository and normal git push authentication is unavailable in this session.

## New Runtime Module

```text
src/skill_deployment/live_contract.py
```

Adds:

- failure taxonomy
- live output normalization
- evidence span line alignment
- low-confidence suppression
- positive-observation suppression
- before/after verifier helper

## Modified Runtime Integration

```text
src/skill_deployment/__init__.py
scripts/run_defensive_security_mini_suite.py
agents/llm_security_agent.py
src/skill_deployment/cli.py
```

Adds:

- exported live contract helpers
- optional evidence normalizer inside mini-suite runner
- raw/normalized output artifacts
- stricter live agent checklist prompt
- CLI commands:
  - live-contract-validation
  - external-generalization
  - live-mechanism-ablation
  - contract-improvement-demo

## New Execution Scripts

```text
scripts/run_live_contract_validation.py
scripts/run_external_generalization_validation.py
scripts/run_live_mechanism_ablation.py
scripts/run_contract_improvement_demo.py
```

Purpose:

- run contract-grounded live validation
- run public-source plus independent holdout generalization
- run live mechanism ablations
- generate and validate a strict contract improvement candidate

## Report / Ledger Integration

```text
scripts/build_grand_autonomous_maturity_reports.py
scripts/build_representative_validation_matrix.py
scripts/build_review_package_manifest.py
```

Adds the new evidence lanes into:

- GRAND_AUTONOMOUS_SPRINT_STATUS
- ACADEMIC_CLAIM_READINESS_ASSESSMENT
- REPRESENTATIVE_VALIDATION_MATRIX
- FRAMEWORK_MATURITY_EVIDENCE_LEDGER
- review_package/MANIFEST.json

## New User Docs

```text
PROJECT_OVERVIEW_FOR_GITHUB.md
docs/ARCHITECTURE_AND_DESIGN.md
docs/USER_GUIDE.md
HANDOFF_FOR_NEXT_CHAT.md
docs/RUN_STATE_SUMMARY.md
docs/REPRODUCE_LATEST_RESULTS.md
```

These explain:

- project scope and non-goals
- Skill lifecycle
- live execution contract
- evidence normalizer
- QGSE-Pareto / marginal utility / rejected buffer concepts
- how to run install, compare, live validation, ablation, and evolve
- how to avoid oracle leakage
- how to interpret evidence types and claim boundaries

## Latest Local Reports Generated

```text
reports/LIVE_CONTRACT_VALIDATION_STATUS.md
reports/EXTERNAL_GENERALIZATION_VALIDATION_STATUS.md
reports/LIVE_MECHANISM_ABLATION_STATUS.md
reports/CONTRACT_IMPROVEMENT_DEMO_STATUS.md
reports/REPRESENTATIVE_VALIDATION_MATRIX.md
reports/FRAMEWORK_MATURITY_EVIDENCE_LEDGER.md
reports/GRAND_AUTONOMOUS_SPRINT_STATUS.md
reports/ACADEMIC_CLAIM_READINESS_ASSESSMENT.md
reports/REVIEW_PACKAGE_INTEGRITY_STATUS.md
```

## Current Evidence Boundary

The latest evidence supports a mature research prototype, not a production system. The strongest honest status is:

```text
academic_claim_readiness: moderate_high_with_caveat
```

The project still lacks:

- official external security benchmark execution
- resolved SWE-bench gold-patch harness run
- a promoted candidate that strictly improves active Skill behavior
- broad real-world security validation

## Upload Status

Uploaded snapshot commit:

```text
53ab0a023f5c5308499dff066b3e7d0009325601
```

A complete code push still requires authenticated git/gh or a connector with tree-commit support.
