# Claim Boundary

## Safe Core Claim

This project is a controlled research prototype for an Evidence-Grounded Skill Evolution Runtime delivered as Codex Skill + CLI.

At the current stage, it can safely claim:

- installed Skill runtime with evidence bundles, comparison, rejection, rollback, and staged promotion logic
- controlled installed multi-capability `secure_code_review` validation
- local defensive representative mini-suite evidence when leakage controls pass
- bounded public-material automatic distillation into an installable Skill package
- bounded stable closed-loop improvement on top of the open-world distilled Skill
- a bounded teaching-utility pilot that can falsify active trajectory-selection hypotheses instead of assuming they work

## What “bounded” means here

The current open-world story is real, but it is not unlimited:

- materials are public or independent, not arbitrary internet-scale open-world inputs
- validation is still local and verifier-controlled
- stable improvement is demonstrated on one bounded closed-loop line, not across arbitrary tasks

So the safe statement is:

> bounded open-world automatic distillation is supported  
> bounded stable evolution improvement is supported  
> universal open-world induction and broad stable autonomous evolution are not yet supported

## Unsafe Claims

Do not claim:

- production vulnerability scanner
- full SPARK reproduction
- SWE-bench success while official harness remains `infra_blocked`
- real-world security validity based only on local deterministic or bounded local evidence
- official CyberSecEval / CVE-Bench / AutoPatchBench result
- universal automatic Skill induction from arbitrary public materials
- broad stable autonomous improvement across arbitrary tasks
- proven superiority of the current active discriminative teaching-utility selector
- exploit generation, attack-chain execution, or unauthorized target testing

## Evidence Lanes

- Runtime-general evidence supports the runtime mechanism.
- Secure-code-review evidence supports bounded defensive review behavior under controlled installed runtime.
- Open-world distillation evidence supports bounded public-material distillation into the current capability registry.
- Open-world closed-loop evidence supports one bounded stable improvement line on top of the distilled runtime.
- Teaching-utility v0.2 evidence supports comparison of trajectory-selection methods under a local bounded live-agent setup, including negative outcomes.
- Software-patch-review evidence supports only internal smoke and harness readiness until non-oracle SWE-bench evaluation succeeds.

## SWE-bench Boundary

SWE-bench evidence must not be used to support `secure_code_review`.

If SWE-bench is `infra_blocked`, report it as infrastructure blocked. Do not call it benchmark success, model failure, or Skill failure.

## Reviewer-Facing Boundary Rules

- `cannot_claim_production_vulnerability_scanner`: `True`
- `cannot_claim_full_spark_reproduction`: `True`
- `cannot_claim_swebench_success_unless_official_harness_resolves`: `True`
- `cannot_claim_real_world_security_validity_from_bounded_local_evidence_only`: `True`
- `cannot_claim_universal_open_world_distillation`: `True`
- `cannot_claim_broad_stable_autonomous_evolution`: `True`
- `can_claim_prototype_level_evidence_grounded_runtime`: `True`
- `can_claim_controlled_installed_multi_capability_secure_code_review_validation`: `True`
- `can_claim_bounded_public_material_distillation`: `True`
- `can_claim_bounded_stable_open_world_closed_loop_improvement`: `True`
