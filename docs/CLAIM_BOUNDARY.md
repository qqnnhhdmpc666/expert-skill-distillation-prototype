# Claim Boundary

## Safe Claim

This project is a controlled deployable prototype for an Evidence-Grounded Skill Evolution Runtime.

It demonstrates:

- prototype-level evidence-grounded Skill Evolution Runtime
- controlled installed multi-capability secure_code_review validation
- representative local defensive security mini-suite if leakage audit passes
- small candidate generation/rejection evidence under strict promotion gates
- SWE-bench official harness readiness tracking, currently infra-blocked unless official harness resolves

## Unsafe Claims

Do not claim:

- production vulnerability scanner
- full SPARK reproduction
- SWE-bench success or agent performance while official harness remains infra_blocked
- real-world security validity based only on offline deterministic mini-suite
- official CyberSecEval/CVE-Bench/AutoPatchBench result
- exploit generation, attack-chain execution, or unauthorized target testing

## Evidence Lanes

- Runtime-general evidence supports the runtime mechanism.
- Secure-code-review evidence supports bounded defensive review behavior under controlled installed runtime.
- Software-patch-review evidence supports only internal smoke and official harness readiness until non-oracle SWE-bench evaluation succeeds.
- External-security evidence is local representative evidence unless an official benchmark is actually run.

## SWE-bench Boundary

SWE-bench official harness results must not be used to support `secure_code_review`.

If SWE-bench is `infra_blocked`, report it as infrastructure blocked. Do not call it benchmark success, model failure, or Skill failure.

## Red-Team Boundary Rules

- `cannot_claim_production_vulnerability_scanner`: `True`
- `cannot_claim_full_spark_reproduction`: `True`
- `cannot_claim_swebench_success_unless_official_harness_resolves`: `True`
- `cannot_claim_real_world_security_validity_from_offline_deterministic_only`: `True`
- `can_claim_prototype_level_evidence_grounded_runtime`: `True`
- `can_claim_controlled_installed_multi_capability_secure_code_review_validation`: `True`
- `can_claim_representative_local_defensive_security_mini_suite_if_leakage_audit_passes`: `True`
