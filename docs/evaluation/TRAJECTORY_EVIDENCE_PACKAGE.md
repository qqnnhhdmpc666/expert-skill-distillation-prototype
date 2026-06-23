# Trajectory Evidence Package

Status: V1 vertical-slice contract.

The trajectory evidence package records what the runtime saw, did, queried, predicted, and how the verifier judged the result.

## Package Layout

The package is written under a run output directory:

```text
trajectory_evidence/
  task_manifest.json
  condition_manifest.json
  skill_manifest.json
  knowledge_manifest.json
  bundle_manifest.json
  environment_manifest.json
  action_trace.jsonl
  observation_trace.jsonl
  knowledge_query_trace.jsonl
  verifier_result.json
  outcome.json
  cost.json
  provenance.json
```

## Outcome Fields

`outcome.json` must record:

- `skill_used`;
- `knowledge_used`;
- `knowledge_queries`;
- `evidence_refs`;
- `prediction`;
- `verifier_pass`;
- `failure_category`.

## Provenance

`provenance.json` includes stable digests for the task manifest, prediction, verifier result, and condition manifest.

## Purpose

The package is designed to support later comparison among:

- no Skill;
- full material;
- direct-to-Skill-IR;
- compiler-distilled Skill;
- human-authored reference Skill when available.

This vertical slice only proves local deterministic package generation and verification. It does not by itself prove compiler superiority.
