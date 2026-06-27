# Skill-Knowledge Runtime Protocol

Status: V1 vertical-slice contract.

This protocol defines how a task receives Skill and knowledge artifacts without collapsing them into one prompt blob.

## Conditions

The vertical slice supports condition manifests for ablation-ready execution:

- `C0_no_skill_no_knowledge`
- `C1_full_material`
- `C2_skill_only`
- `C3_skill_plus_knowledge`
- `C4_release_bundle`
- `C5_active_runtime`

The implemented smoke path uses `C5_active_runtime`.

## Manifest Files

`build_injection_manifests(...)` writes:

- `condition_manifest.json`
- `skill_manifest.json`
- `knowledge_manifest.json`
- `bundle_manifest.json`

The condition manifest records:

- whether Skill is enabled;
- whether knowledge access is enabled;
- runtime-visible paths;
- hidden evaluator paths;
- active bundle digest.

The runtime-visible task path points to a sanitized `runtime_task_view.json`; it does not point at raw `task.json`, because raw `task.json` contains evaluator-only gold.

## Knowledge Access

Knowledge access is constrained to `allowed_knowledge.json`. The runtime may query this snapshot by package and advisory id. It must not query the internet, hidden gold, or verifier-only answers.

## Skill Boundary

The current local skill condition encodes how-to requirements for dependency-use triage:

- find dependency declarations;
- extract resolved version;
- find import or call-site evidence;
- consult allowed advisory snapshot;
- abstain when evidence is missing.

The Skill is a workflow guide. The advisory range itself remains runtime knowledge, not baked into the Skill.

## Nonclaims

This protocol is not a vector database, GraphRAG, Harbor bridge, live AgentHost integration, production scanner, or proof of full compiled `ReleaseBundle` attachment. Current attachment is `partial_local_manifest_only`.
