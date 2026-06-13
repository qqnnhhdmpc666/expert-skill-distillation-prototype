# Morning Status 0800

Updated: 2026-06-09

## One-line status

The repository is now a controlled multi-backend prototype for scenario-conditioned expert knowledge distillation into Skill Packages, with shared local runner abstractions, typed repair/gate flow, artifact-backed validity cards, and bounded Harbor replay integration.

## Research framing update

The trunk is now better described as **Environment-Grounded Expert Skill Distillation and Evolution with Evidence-Qualified Promotion**.

That means:

- expert material -> normalized capabilities -> Skill Package is the main product path
- execution feedback -> typed repair -> Skill evolution is the main adaptation path
- QGSE / QGSE-Pareto / qualification cards are the promotion-control layer, not the whole project

Short version:

> feedback proposes revision; qualification decides promotion.

So the project should not be judged by one A2 PASS, reward, or PDI-like score. A revised Skill Package is promoted only after integrity, behavior, robustness, and promotion-evidence gates decide what scope is supported.

## Canonical snapshot docs

- `reports/MORNING_HANDOFF_0800.md`
- `reports/CURRENT_SYSTEM_SNAPSHOT.md`
- `reports/CODEX_SELF_ASSESSMENT_0800.md`
- `docs/CLAIM_BOUNDARY.md`

Read those four first. This file is the concise status board.

## Current strongest evidence

- Offline controlled suite: `outputs/validation/generalization_suite.json`
  - 5 task families
  - 5 distinct A1 feedback types
  - 5 distinct typed repair actions
  - A2 pass `5/5`
- Negative controls: `outputs/validation/negative_controls.json`
  - unsupported evidence rejected
  - append-style false positives rejected on a clean config target
- Verifier stress checks: `outputs/validation/verifier_stress_checks.json`
  - optional strict target-text binding added to the shared verifier
  - correct-target upload report passes
  - swapped-target and fabricated-evidence checks fail as expected
- Repair alignment audit: `outputs/validation/repair_policy_alignment.json`
  - repair policy and typed operator registry are fully aligned
  - known feedback types no longer rely on silent manual fallback
- Local non-oracle semantic backend: `outputs/validation/non_oracle_local_suite.json`
  - shared runner path
  - target-grounded reads across 5 controlled families
  - A2 pass `5/5`
- Local live LLM repair loops:
  - upload: `outputs/live_llm_repair_loop_upload_001/summary.json`
  - non-security data quality: `outputs/live_llm_repair_loop_data_quality_001/summary.json`
  - config security: `outputs/live_llm_repair_loop_config_security_001/summary.json` (`A2` FAIL)
  - API review: `outputs/live_llm_repair_loop_api_review_001/summary.json` (`A2` FAIL)
- Harbor live LLM evidence:
  - upload pass: `outputs/harbor_llm_upload_001/summary.json`
  - upload repair loop: `outputs/harbor_llm_repair_loop_upload_001/summary.json`
  - config repair loop: `outputs/harbor_llm_repair_loop_config_001/summary.json`
  - upload repeatability smoke: `outputs/validation/harbor_llm_repeatability_upload.json`
- Shared validity cards: `outputs/validation/skill_revision_validity_cards.json`
  - card count `11`
- Skill qualification cards: `outputs/validation/skill_qualification_cards.json`
  - card count `9`
  - explicitly promotes bounded successes and quarantines/rejects local config/API failures
- Standardized lifecycle evidence:
  - `outputs/skill_lifecycle_evidence/index.json`
  - `outputs/validation/skill_net_effect_matrix.json`
  - `reports/SKILL_LIFECYCLE_EVIDENCE_STATUS.md`
  - per-case distillation bundles now expose `source_material -> extracted_candidates -> capability_provenance -> skill_v1/v2 -> evolution_lessons`
  - per-case and live-loop trajectory bundles now expose normalized `trajectory.jsonl`, `target_reads.json`, `skill_reads.json`, `raw_output.json`, `verifier_feedback.json`, `repair_patch.json`, and qualification boundary
- Installation / reviewer-prep surface:
  - `outputs/installed_skills/registry.json`
  - `outputs/reviewer_readiness/reviewer_assessment.json`
  - `reports/SKILL_INSTALLATION_STATUS.md`
  - `reports/REVIEWER_READINESS_STATUS.md`
  - upload now includes an explicit rollback-demo history referencing the existing rollback-gate precedent
- Promotion mechanism comparison: `outputs/validation/promotion_mechanism_comparison.json`
  - QGSE selected as current best over reward-delta-only, gate-only, weighted-score, and Pareto-conservative baselines
- Promotion mechanism challenge set: `outputs/validation/promotion_mechanism_challenge_set.json`
  - QGSE + Conservative Pareto selected as best current candidate on synthetic false-promotion/scope/cost/human-usefulness challenges
- Promotion mechanism fairness audit: `outputs/validation/promotion_mechanism_fairness_audit.json`
  - documents baseline roles, strawman risk, shared evidence limits, and next baseline improvements
- Artifact-backed promotion challenge set: `outputs/validation/artifact_backed_promotion_challenge_set.json`
  - uses Harbor upload success, config/API failures, agent-level stress failures, and negative controls as real internal challenge samples
- Minimal metamorphic stress: `outputs/validation/metamorphic_stress_minimal.json`
  - upload clean target, config clean target, data-quality row shuffle, and API injected-risk controls pass
- Agent-level metamorphic stress: `outputs/validation/agent_level_metamorphic_stress_001/summary.json`
  - deterministic local semantic agent exposes false-positive and evidence-span brittleness; retained as limitation evidence
- Live LLM agent-level metamorphic stress: `outputs/validation/live_llm_agent_level_metamorphic_stress_001/summary.json`
  - attempted data-quality row-shuffle stress; current result is API `403 Forbidden`, so no live model-behavior claim is made

## Evidence strength judgment

- Offline generalization claim: `strong controlled evidence`
- Negative-control robustness claim: `moderate controlled evidence`
- Local live-LLM repair-loop claim: `moderate controlled evidence for upload/data-quality, mixed controlled evidence for config/api`
- Harbor live-LLM repair-loop claim: `moderate controlled evidence`
- Broad open-world generalization claim: `not supported`
- General vulnerability scanner claim: `not supported`
- Full SPARK-PDI reproduction claim: `not supported`
- QGSE contribution claim: `supported as a design-and-prototype framing`, with executable qualification cards now attached
- Lifecycle/provenance claim: `moderate controlled evidence`
- Reviewer-prep / install-surface claim: `weak-to-moderate controlled productization evidence`

## Qualification addendum

- Local live LLM upload: `L2_PROMOTE_LOCAL_WITH_SCOPE_LIMIT`, controlled upload scope only.
- Local live LLM data quality: `L2_PROMOTE_LOCAL_WITH_SCOPE_LIMIT`, controlled non-security data-quality scope only.
- Local live LLM config: `L0_NON_PROMOTABLE` / quarantine, because A2 still misses `CONFIG_ENV_GUARD` after the patch.
- Local live LLM API review: `L0_NON_PROMOTABLE` / reject, because `patch_capability` does not change the before/after capability set and A2 still misses `API_OVERBROAD_RISK`.
- Harbor live LLM upload: `L4_PROMOTE_SANDBOXED_WITH_SCOPE_LIMIT`, controlled upload scope only, supported by repeatability smoke.
- Harbor live LLM config: `L4_PROMOTE_SANDBOXED_WITH_SCOPE_LIMIT`, controlled config scope only, but robustness is narrower than upload.
- `L5_PROMOTE_REVIEWED` is not claimed.

## Current architecture boundary

- `Agent`: task executor that reads target/skill and emits raw findings.
- `Runner`: normalized execution wrapper returning `ExecutionReport` plus artifact paths.
- `Harbor`: sandbox substrate, not the algorithm.

Current shared local runners:

- `offline_deterministic`
- `non_oracle_local_semantic`
- `live_llm_text`

Current Harbor runner state:

- live Harbor execution is still script-driven
- shared runner currently has a minimal read-existing replay adapter:
  - `harbor_llm_repair_upload_replay`
  - `harbor_llm_repair_config_replay`

## Most important limitations

1. Harbor is not yet a fully shared live execution backend under `BackendRunner`; current integration is replay/read-existing.
2. Live LLM evidence is still narrow and controlled; the added local config/api slices currently fail rather than closing the loop.
3. The local non-oracle semantic backend is deterministic heuristic code, not autonomous semantic reasoning.
4. Verifier/gate support structural validity and narrow robustness, not semantic completeness or human usefulness.
5. The Streamlit UI is secondary; the review package and artifact chain are the primary credible deliverables.
6. Provenance extraction is still controlled keyword projection over curated expert notes; it is exportable and auditable, but not broad autonomous expert-material induction.
7. Reviewer-readiness packets reduce external-review friction, but they are still internal preparation artifacts rather than human usefulness evidence.

## Final validation board

| Command | Result |
|---|---|
| `python -m py_compile demo/streamlit_app.py` | PASS |
| `python -m pytest -q` | PASS, `34 passed` |
| `python scripts/validate_task_cases.py` | PASS, `7` task cases |
| `python scripts/run_generalization_suite.py --backend offline_deterministic --scenarios upload,auth,config,api_review,data_quality` | PASS, `5/5` A2 |
| `python scripts/run_generalization_suite.py --backend non_oracle_local_semantic --scenarios upload,auth,config,api_review,data_quality` | PASS, `5/5` A2 |
| `python scripts/run_ablation_suite.py` | PASS, `14` rows |
| `python scripts/run_live_llm_upload.py` | PASS, local upload smoke + repair loop landed |
| `python scripts/run_live_llm_upload.py --scenario data_quality --skip-smoke` | PASS, local non-security repair loop landed |
| `python scripts/run_skill_revision_validity_cards.py` | PASS, `11` validity cards |
| `python scripts/run_skill_qualification_cards.py` | PASS, `9` qualification cards |
| `python scripts/compare_promotion_mechanisms.py` | PASS, QGSE selected as current best mechanism |
| `python scripts/run_promotion_mechanism_challenge_set.py` | PASS, QGSE + Pareto selected as best challenge-set candidate |
| `python scripts/run_promotion_mechanism_fairness_audit.py` | PASS, fairness audit report generated |
| `python scripts/run_artifact_backed_promotion_challenge_set.py` | PASS, QGSE/QGSE-Pareto avoid false promotion/scope errors on current artifacts |
| `python scripts/run_metamorphic_stress.py` | PASS, `4/4` minimal metamorphic controls |
| `python scripts/run_agent_level_metamorphic_stress.py` | PASS as audit run; `overall_pass=false` retained as limitation evidence |
| `python scripts/run_live_llm_agent_level_metamorphic_stress.py` | PASS as audit run; current result `api_error` / `403 Forbidden` |
| `python scripts/run_harbor_replay_summary.py --backend harbor_llm_repair_upload_replay --attempt A1` | PASS |
| `python scripts/run_harbor_replay_summary.py --backend harbor_llm_repair_config_replay --attempt A2` | PASS |
| `python scripts/run_verifier_stress_checks.py` | PASS, shared strict-binding stress checks landed |
| `python scripts/run_repair_policy_alignment_audit.py` | PASS, policy/operator mapping fully aligned |
| `python scripts/export_review_package.py` | PASS, `review_package/` and `review_package.zip` refreshed |
| `python scripts/validate_review_package.py` | PASS, `0` errors |

## What to say externally

Safe wording:

> This is a controlled multi-backend prototype for expert knowledge distillation into Skill Packages. It supports typed verifier feedback, typed repair, gate decisions, artifact-backed validity cards, one non-security family, and bounded Harbor-backed execution evidence.

Unsafe wording:

- "general vulnerability scanner"
- "broad Harbor LLM generalization"
- "full SPARK-PDI reproduction"
- "mature open-source platform"

Compatibility note: `review_package_export.zip` is refreshed as a copy of the validated `review_package.zip` so older handoff references still resolve.
