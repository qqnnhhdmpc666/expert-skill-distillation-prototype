# Distillation Feedback Loop v1 Anti-Fake Audit

## Scoped Staging

Included in this commit:
- v1 defect case data under `data/distillation_cases/repo_dependency_use_triage_v1/`
- Bundle runtime policy, evidence binding, repo evidence collector, repo security runtime, trajectory long-path IO support
- Distillation attribution/revision/report helpers and v1 runner
- v1 tests and v1 status/evidence artifacts under `outputs/distillation_loop/repo_dependency_use_triage_v1/`

Explicitly not staged as unrelated dirty state:
- `outputs/installed_skills/` runtime registry changes
- `outputs/open_world_closed_loop/` candidate artifacts
- `outputs/teaching_utility_v02/` historical experiment changes/deletions/new runs
- `outputs/test_tmp/` scratch artifacts
- v0-only report/script/test artifacts not required by v1 commit surface

## Cached Checks

- `git diff --cached --check`: pass
- `git diff --cached --stat`: 927 files changed, 50271 insertions, 72 deletions
- Historical output prefixes above are absent from `git diff --cached --name-only`.

## Anti-Fake Search

- No runtime/source branch of the form `if defect_id` or `if task_id` was found in staged runtime/distillation implementation.
- Defect ids are used for isolated state/output path names and condition labels only.
- Concrete task ids appear in tests and task registry filtering, not in runtime prediction logic.
- Baseline/revised variants are passed to the Bundle builder as metadata; no `variant == baseline` behavior branch was found.
- Revision plans record `task_specific_patch=false` and `patched_task_answers=[]`.

## D1-D4 Evidence Table

| defect | baseline policy field | revised policy field | baseline failed tasks | attribution type | repair target | revised pass result | anti-fake evidence path |
|---|---|---|---|---|---|---|---|
| $defect | required_evidence excludes import_use_site | required_evidence includes import_use_site | dependency_use_triage_requests_demo<br>dependency_use_triage_declared_not_used<br>dependency_use_triage_version_not_affected<br>dependency_use_triage_the_gan_zoo_public | evidence_binding_gap, skill_missing_rule | skill_rule, evidence_binding_plan | revised_pass_count=4, promotion=promote | $caseDir/baseline_bundle/runtime_bundle_policy.json<br>$caseDir/revised_bundle/runtime_bundle_policy.json<br>$caseDir/failure_attribution.jsonl<br>$caseDir/promotion_decision.json |
| $defect | decision_policy.version_range_comparison_required=false | decision_policy.version_range_comparison_required=true | dependency_use_triage_requests_demo<br>dependency_use_triage_version_not_affected<br>dependency_use_triage_the_gan_zoo_public | skill_overgeneralized_rule | skill_rule, runtime_policy | revised_pass_count=4, promotion=promote | $caseDir/baseline_bundle/runtime_bundle_policy.json<br>$caseDir/revised_bundle/runtime_bundle_policy.json<br>$caseDir/failure_attribution.jsonl<br>$caseDir/promotion_decision.json |
| $defect | knowledge_projection_policy.allowed_advisory_fields=[] | knowledge_projection_policy.allowed_advisory_fields=[affected_ranges] | dependency_use_triage_requests_demo<br>dependency_use_triage_declared_not_used<br>dependency_use_triage_version_not_affected<br>dependency_use_triage_the_gan_zoo_public | knowledge_gap | knowledge_projection, knowledge_access_binding | revised_pass_count=4, promotion=promote | $caseDir/baseline_bundle/runtime_bundle_policy.json<br>$caseDir/revised_bundle/runtime_bundle_policy.json<br>$caseDir/failure_attribution.jsonl<br>$caseDir/promotion_decision.json |
| $defect | candidate_path_overrides.import_use_site=[] | candidate_path_overrides.import_use_site=[*.py] | dependency_use_triage_requests_demo<br>dependency_use_triage_version_not_affected<br>dependency_use_triage_the_gan_zoo_public | evidence_binding_gap | evidence_binding_plan | revised_pass_count=4, promotion=promote | $caseDir/baseline_bundle/runtime_bundle_policy.json<br>$caseDir/revised_bundle/runtime_bundle_policy.json<br>$caseDir/failure_attribution.jsonl<br>$caseDir/promotion_decision.json |

## Claim Boundary

- This audit supports a bounded local multi-defect distillation feedback loop.
- It does not claim compiler superiority, official public benchmark performance, general vulnerability discovery, or production readiness.
