# Artifact Types

Use these labels consistently in reports and matrices.

## `fresh_run`

An artifact produced by executing the current runtime path in this sprint or current validation pass.

Examples:

- installed `run-skill` evidence bundle
- mini-suite per-case `run_metadata.json`
- installed compare `installed_package_marginal_utility.json`

## `derived_summary`

A report generated from existing artifacts without re-running the underlying task.

Examples:

- maturity ledger
- representative matrix
- sprint status report

## `scaffold`

A directory, schema, or placeholder that prepares a future run but is not itself execution evidence.

Examples:

- external benchmark scaffold before real cases run
- planned benchmark manifests

## `infra_blocked`

An execution attempt reached infrastructure setup but could not complete because of Docker, network, image build, dependency download, or external-service issues.

This is not benchmark success and not model/Skill failure.

## `replay`

Evidence derived from pre-existing snapshots or replay adapters rather than a fresh live execution.

## `external_official_harness`

Evidence produced by an official external evaluation harness, such as SWE-bench official `swebench.harness.run_evaluation`.

If the official harness is invoked but Docker or dependency setup fails, label the result `infra_blocked`, not `external_official_harness` success.
