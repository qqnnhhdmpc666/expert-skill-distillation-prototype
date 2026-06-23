# Claim Boundary

## Safe Core Claim

This project is a research prototype for an Expert Skill Distillation System:

```text
Knowledge Compiler
+ Skill Runtime
+ Pluggable Knowledge Provider
+ External Verification
+ Safe Evolution
```

V1 demonstrates the system on a bounded Python dependency-advisory applicability slice. It compiles expert rules and frozen public OSV data into structured artifacts, releases them as immutable Bundles, executes the Bundle in a local runtime, and records evidence for validation, promotion, rejection, and rollback.

## Current Supported Claims

- The local V1 core implementation is present and tested.
- Skill IR and Knowledge Projection are separate artifacts inside a ReleaseBundle.
- Independent DeepSeek Judge has passed on the compiler gate.
- Public OSV pilot v2 reference runtime passed 33/33 cases with false-safe count 0.
- Harbor public OSV oracle/verifier parity passed a 6-case representative subset.
- `direct_to_skill_ir` and `compiler_distilled_skill` now produce distinct Skill IR and Agent artifacts.
- Safe update, unsafe-update rejection, and full-bundle rollback are implemented in the local runtime.

## Current Non-Claims

- Mature AgentHost execution is not qualified.
- Compiler superiority over direct generation is not evaluated.
- General open-world automatic distillation is not proven.
- Stable autonomous evolution that reliably produces better Skills is not proven.
- Harbor subset parity is not broad public benchmark success.
- OSV advisory applicability is not exploitability, reachability, or proof that a real project is vulnerable.
- The system is not a production vulnerability scanner.

## Current Blockers

AgentHost is the main blocker. Codex CLI 0.137 is installed, but the current DeepSeek endpoint is Chat Completions compatible while Codex requires a Responses-compatible provider. A default OpenAI Responses attempt reached Codex but failed with endpoint/credential errors. OpenHands is not installed locally. Therefore the current status is:

```text
agent_host = hard_blocked_no_compatible_mature_host
compiler_vs_direct = prepared_condition_sensitive_eval_no_agenthost
```

## Legacy Lane Boundary

The older `skill_deployment` / `skill-deploy` / `secure_code_review` lane is retained as earlier prototype evidence. It must be described as legacy baseline or earlier controlled runtime work, not as the current V1 main architecture.

## Reviewer-Facing Boundary Rules

- `can_claim_core_local_v1_implemented`: `True`
- `can_claim_independent_deepseek_judge_pass`: `True`
- `can_claim_public_osv_reference_runtime_pass`: `True`
- `can_claim_harbor_public_osv_subset_parity_pass`: `True`
- `can_claim_distinct_direct_and_compiler_artifacts`: `True`
- `cannot_claim_mature_agenthost_execution`: `True`
- `cannot_claim_compiler_superiority`: `True`
- `cannot_claim_general_open_world_distillation`: `True`
- `cannot_claim_broad_stable_autonomous_evolution`: `True`
- `cannot_claim_production_vulnerability_scanner`: `True`
- `cannot_claim_exploitability_or_reachability`: `True`
