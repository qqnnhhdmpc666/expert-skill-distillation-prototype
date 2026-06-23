# Repo-Level Security Task Spec

Status: V1 vertical-slice contract.

This spec defines the first non-toy repo-level security task family for the expert Skill-Knowledge distillation runtime: `dependency_use_triage`.

## Task Objective

Given a frozen repository snapshot and an allowed advisory knowledge snapshot, decide whether a declared dependency is:

- present in the repo;
- resolved to a concrete version;
- actually imported or used by repo code;
- affected by the allowed advisory range.

The task does not claim exploitability, runtime reachability, or vulnerability discovery.

## Required Task Package Files

Each task lives under:

```text
data/repo_security_tasks/<task_id>/
```

Required files:

- `task.json`: task metadata and evaluator-only hidden gold.
- `repo_snapshot_manifest.json`: frozen repo snapshot inventory.
- `allowed_knowledge.json`: runtime-visible allowed knowledge only.
- `expected_output_schema.json`: prediction schema contract.
- `verifier.py`: native deterministic verifier entrypoint.
- `repo_snapshot/`: task repository files.

## Visibility Boundary

Runtime-visible:

- task instruction;
- repo snapshot files;
- repo snapshot manifest;
- allowed knowledge snapshot;
- expected output schema.

Evaluator-only:

- `task.json#hidden_gold`;
- native verifier checks;
- expected decision and required evidence types.

The runtime, Skill, and evidence binding planner must not read evaluator-only fields.

## Prediction Contract

`prediction.json` must include:

- `schema_version`;
- `task_id`;
- `task_type`;
- `decision`;
- `package`;
- `declared_version`;
- `advisory_id`;
- `evidence`;
- `reason_codes`.

Every evidence item must name an evidence type, path, line when available, and excerpt. The verifier requires grounded evidence for dependency declaration, resolved version, import/use site, advisory range, and decision evidence.

## Current Fixture

Current task:

```text
data/repo_security_tasks/dependency_use_triage_requests_demo/
```

It checks `requests==2.19.1` against allowed advisory `PYSEC-2018-28` and a local source use site in `src/app/client.py`.
