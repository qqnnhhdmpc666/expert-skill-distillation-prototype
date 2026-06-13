# Claim Boundary

## Safe Claims

- This is a controlled prototype for environment-grounded expert skill distillation and evolution with evidence-qualified promotion.
- The mainline is expert material -> normalized capabilities -> Skill Package -> execution -> verifier feedback -> typed repair -> revised Skill Package.
- Qualification-Guided Skill Evolution is the promotion-control layer inside that larger lifecycle: verifier feedback proposes a Skill revision, while integrity, behavior, robustness, and promotion-evidence gates decide whether the revision can be promoted.
- It demonstrates a multi-stage lifecycle: expert material and target asset -> Skill v1 -> execution output -> verifier feedback -> typed repair -> Skill v2 -> rerun.
- It supports a small multi-task case suite for preliminary controlled generalization evidence, including one non-security data-quality review family.
- It records artifact-backed source, execution, feedback, revision, and validation traces.
- It separates backend maturity levels: offline deterministic runner, optional live LLM text path, local deterministic runner, and WSL/Harbor sandbox substrate.
- It now shares one capability registry between the controlled suite and the non-oracle local semantic backend.
- It now shares one controlled task-case loader and one controlled verifier across the suite path.
- It now routes offline deterministic and non-oracle local semantic execution through a shared backend-runner abstraction.
- It now routes the local live LLM upload path through the same shared backend-runner abstraction used by the other stable local backends.
- It now routes one controlled non-security local live LLM repair loop through that same shared local runner path.
- It now has a minimal read-existing Harbor replay adapter under the shared backend-runner interface for the upload/config Harbor LLM repair loops.
- It demonstrates typed posterior feedback, repair, and gate decisions in controlled cases.
- It shows one controlled Harbor non-oracle A1/A2 repair loop with a deterministic heuristic agent: A1 reward `0.0`, verifier missing-capability feedback, patched capability config, A2 reward `1.0`.
- It shows one local live LLM-backed upload-security run with deterministic verifier pass.
- It shows one local live LLM-backed A1/A2 repair loop where Skill v1 misses capabilities and Skill v2 passes after verifier-driven repair.
- It shows one local live LLM-backed non-security data-quality A1/A2 repair loop where A1 fails on output-contract strictness and A2 passes after typed repair.
- It shows one Harbor/Docker live LLM-backed non-oracle upload run where the agent reads `/app/target` and `/app/skill`, writes `/app/security_report.json`, and receives verifier reward `1.0`.
- It shows one Harbor/Docker live LLM-backed A1/A2 repair loop where A1 reads a generated v1 `/app/skill`, fails with missing-capability feedback, and A2 reads a generated v2 `/app/skill` and passes.
- It shows one second controlled Harbor/Docker live LLM-backed config-security repair loop where A1 fails with `output_contract_error`, `revision/patch_plan.json` tightens the contract, and A2 passes on the same target.
- It shows a three-run repeatability smoke for the Harbor upload LLM repair loop: A1 always fails, A2 always passes, and the missing-capability failure reason is stable in this slice.
- It now emits Skill Qualification Cards that explicitly mark local config/API LLM failures as quarantine/reject instead of treating them as successful promotion evidence.
- It now separates `RevisionQualificationCard` from `EvidenceSupportCard`, so generalization, negative control, and repeatability artifacts support promotion decisions without pretending that a specific Skill was promoted by themselves.
- It now compares multiple promotion mechanisms and treats QGSE as the current best mechanism, not a frozen assumption.
- It now includes a minimal metamorphic stress suite for upload/config/data-quality/API verifier relations.
- It now includes a synthetic Promotion Mechanism Challenge Set; on that set, a QGSE + Conservative Pareto hybrid is the best current candidate.
- It now includes an artifact-backed promotion challenge set built from existing success/failure artifacts; QGSE and QGSE-Pareto tie on current internal artifacts.
- It now includes a promotion-mechanism fairness audit to reduce the risk of comparing against weak strawman baselines.
- It now includes an agent-level deterministic metamorphic stress run; this currently exposes limitations and is not all-pass evidence.
- It attempted one live LLM agent-level data-quality row-shuffle stress, but the current run hit API `403 Forbidden`; this is backend/access evidence, not a model-behavior result.
- It now includes standardized lifecycle evidence bundles in `outputs/skill_lifecycle_evidence/` plus a controlled `no-skill / skill-v1 / skill-v2` matrix in `outputs/validation/skill_net_effect_matrix.json`.
- It now exposes capability-level provenance artifacts showing how curated expert notes map to normalized capabilities, v1 inclusion, and v2 repair attribution.
- It now includes a generated installed-skill registry in `outputs/installed_skills/` with version directories, active manifests, deployment records, and a rollback-surface demo.
- It now includes reviewer-readiness packets in `outputs/reviewer_readiness/` that organize what to show first, which boundary to state, and which artifacts support each controlled claim.

## Unsafe Claims

- It is not a general vulnerability scanner.
- It is not a full SPARK-PDI reproduction.
- It does not claim to invent feedback loops or Skill Packages; the intended contribution is the qualification protocol for deciding whether a revised Skill Package deserves scoped promotion.
- It does not prove arbitrary expert materials can be automatically distilled.
- It does not prove that the current provenance bundle method is a general autonomous distillation algorithm; current provenance is controlled keyword projection over curated expert notes.
- It does not prove real-world vulnerability discovery.
- It does not provide large-scale generalization evidence.
- It does not yet show broad Harbor LLM generalization across open-ended security tasks.
- It does not yet show semantic target reasoning in `local_real_agent`.
- It does not yet show Harbor or live-LLM generalization on the new non-security family.
- It does not yet show diverse repair-loop feedback on the non-oracle local semantic backend beyond the upload slice.
- It does not yet route Harbor execution through the shared backend runner path.
- It does not yet route live Harbor execution itself through the shared backend runner path; the new Harbor runner is replay/read-existing only.
- It does not yet prove that the shared live-LLM runner generalizes beyond the controlled local upload slice.
- It does not yet prove that the shared live-LLM runner broadly generalizes beyond two narrow local controlled slices: upload and data quality.
- It does not yet reach `L5_PROMOTE_REVIEWED`; no systematic human/external usefulness review has been attached.
- Reviewer-readiness packets are not external human validation.

## Qualification Boundary

Current Skill Qualification Cards:

- `outputs/validation/skill_qualification_cards.json`
- `outputs/validation/promotion_mechanism_comparison.json`
- `outputs/validation/promotion_mechanism_challenge_set.json`
- `outputs/validation/artifact_backed_promotion_challenge_set.json`
- `outputs/validation/promotion_mechanism_fairness_audit.json`
- `outputs/validation/metamorphic_stress_minimal.json`
- `outputs/validation/agent_level_metamorphic_stress_001/summary.json`
- `outputs/validation/live_llm_agent_level_metamorphic_stress_001/summary.json`
- `reports/SKILL_QUALIFICATION_CARD_STATUS.md`
- `reports/PROMOTION_MECHANISM_EXPLORATION.md`
- `reports/PROMOTION_MECHANISM_CHALLENGE_SET_STATUS.md`
- `reports/ARTIFACT_BACKED_PROMOTION_CHALLENGE_SET_STATUS.md`
- `reports/PROMOTION_MECHANISM_FAIRNESS_AUDIT.md`
- `reports/METAMORPHIC_STRESS_STATUS.md`
- `reports/AGENT_LEVEL_METAMORPHIC_STRESS_STATUS.md`
- `reports/LIVE_LLM_AGENT_LEVEL_METAMORPHIC_STRESS_STATUS.md`

Current qualification reading:

- Local live LLM upload: `L2_PROMOTE_LOCAL_WITH_SCOPE_LIMIT` under controlled upload scope.
- Local live LLM data quality: `L2_PROMOTE_LOCAL_WITH_SCOPE_LIMIT` under controlled data-quality scope.
- Local live LLM config: `L0_NON_PROMOTABLE` / quarantine because the revised capability is not expressed in A2 behavior.
- Local live LLM API review: `L0_NON_PROMOTABLE` / reject because the repair is effectively a no-op and A2 still misses the same capability.
- Harbor live LLM upload: `L4_PROMOTE_SANDBOXED_WITH_SCOPE_LIMIT` under controlled upload scope.
- Harbor live LLM config: `L4_PROMOTE_SANDBOXED_WITH_SCOPE_LIMIT` under controlled config scope, with narrower robustness than upload.

These levels are scoped evidence labels, not universal capability claims.

Lifecycle-evidence boundary:

- `outputs/skill_lifecycle_evidence/` standardizes provenance and trajectory artifacts so they are easier to inspect and export.
- Offline lifecycle bundles are normalized artifact bundles, not full SPARK-style live terminal trajectories.
- Harbor/local live bundles are still narrow slices, not broad multi-task autonomous evidence.

Mechanism boundary:

- `qgse_protocol` is best under current grounded-label interpretation, not an externally validated final mechanism.
- `qgse_pareto_protocol` is best on the synthetic challenge set and should be treated as a next candidate, not a final claim.
- On the current artifact-backed challenge set, `qgse_protocol` and `qgse_pareto_protocol` both avoid false promotion and scope error; the tie should be reported honestly.
- Agent-level metamorphic stress currently fails some local deterministic checks, which limits claims about semantic robustness.

## Positive Harbor Evidence

- It does show a non-oracle Harbor `nop` baseline failing with verifier feedback.
- It does show one non-oracle deterministic heuristic Harbor agent solving the controlled upload task.
- It does show one controlled Harbor non-oracle repair loop where A1 fails from a restricted capability config and A2 passes after verifier-driven repair.
- It does show one live LLM-backed Harbor non-oracle agent solving the controlled upload task.
- It does show one live LLM-backed Harbor non-oracle repair loop where A1 fails with missing-capability feedback and A2 passes after repair.
- It does show one live LLM-backed Harbor config-security repair loop where A1 fails with `output_contract_error` and A2 passes after contract tightening.
- It does show a small repeatability smoke for the Harbor upload LLM repair loop.

## Current Evidence

- `outputs/validation/generalization_suite.md`: five controlled task families, including one non-security family, A2 5/5 pass.
- `outputs/validation/non_oracle_local_suite.md`: the deterministic local semantic backend now reads the same five controlled task families and writes artifact-backed outputs.
- `outputs/validation/negative_controls.json`: two negative controls reject unsupported evidence / false positives.
- `outputs/validation/verifier_stress_checks.json`: the shared verifier now has an optional strict target-text binding mode that passes the correct upload target and rejects swapped-target / fabricated-evidence checks.
- `outputs/validation/ablation_summary.md`: minimal controlled ablation for typed repair plus gate.
- `outputs/wsl_harbor_real_upload_001/summary.md`: WSL2/Docker/Harbor security task with oracle agent reward 1.0.
- `outputs/harbor_non_oracle_upload_001/summary.md`: WSL2/Docker/Harbor non-oracle `nop` baseline reward 0.0 with verifier feedback.
- `outputs/harbor_non_oracle_cli_upload_001/summary.md`: WSL2/Docker/Harbor non-oracle heuristic upload attempt reward 1.0.
- `outputs/harbor_non_oracle_repair_loop_upload_001/summary.md`: WSL2/Docker/Harbor non-oracle heuristic A1/A2 repair loop reward 0.0 -> 1.0.
- `outputs/live_llm_upload_001/summary.md`: local live LLM non-oracle upload run, deterministic verifier PASS.
- `outputs/live_llm_repair_loop_upload_001/summary.md`: local live LLM A1/A2 repair loop, A1 missing capability -> A2 PASS.
- `outputs/live_llm_repair_loop_data_quality_001/summary.md`: local live LLM non-security A1/A2 repair loop, A1 output-contract error -> A2 PASS.
- `outputs/harbor_llm_upload_001/summary.md`: WSL2/Docker/Harbor live LLM non-oracle upload run, reward 1.0.
- `outputs/harbor_llm_repair_loop_upload_001/summary.md`: WSL2/Docker/Harbor live LLM non-oracle A1/A2 repair loop, reward 0.0 -> 1.0.
- `outputs/harbor_llm_repair_loop_config_001/summary.md`: WSL2/Docker/Harbor live LLM config-security A1/A2 repair loop, reward 0.0 -> 1.0 via contract repair.
- `reports/HARBOR_RUNNER_INTEGRATION_STATUS.md`: minimal Harbor replay adapter under the shared runner interface.
- `outputs/validation/harbor_llm_repeatability_upload.json`: three-run repeatability smoke for the Harbor upload repair loop.
- `outputs/system_acceptance_001/summary.md`: project-level acceptance snapshot.

## WSL / Harbor Boundary

The oracle Harbor task proves the sandbox substrate and verifier plumbing can run. The non-oracle `nop` baseline proves Harbor can execute a non-oracle agent path and produce failure feedback. The custom heuristic agent proves a deterministic non-oracle agent can read target files and solve one controlled upload task. The heuristic repair-loop run proves a restricted Harbor A1 can fail, produce missing-capability feedback, consume a repair plan, and rerun as A2 with improved reward. The Harbor LLM upload run proves a live LLM-backed non-oracle agent can read target and skill files in Harbor and pass one controlled upload task. The Harbor upload repair-loop run proves the same live LLM-backed Harbor path can fail under a restricted v1 skill and pass after a verifier-driven v2 repair. The Harbor config repair-loop run proves the live Harbor LLM path can also exercise a different verifier failure type (`output_contract_error`) and a different repair action (`rewrite_output_contract`) on a second controlled task. The repeatability smoke reduces the chance that the upload result is a one-off. These results still do not prove broad Harbor LLM generalization, open-world vulnerability discovery, or full SPARK-PDI reproduction.

Next required strengthening: add at least one more Harbor LLM task beyond upload/config and measure larger-sample prompt sensitivity.

## Recommended Presentation Wording

> This prototype studies scenario-conditioned expert knowledge distillation for controlled task execution and revision. It turns expert materials and target assets into a Skill Package, executes it, verifies failures, applies typed posterior repair, and records the evidence chain. The current 0.1+ evidence includes five offline controlled task families with typed repair diversity, local and Harbor live LLM upload runs, one Harbor config repair loop, and a small upload repeatability smoke, but it is still controlled evidence and not a universal vulnerability scanner.
