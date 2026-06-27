# Documentation Status Consolidation

Date: 2026-06-23

```text
documentation_status = consolidated
claim_boundary = consistent_current_v1
legacy_lane = explicitly_downgraded
```

## Updated documents

| Document | Change |
|---|---|
| `README.md` | Rewritten as current V1 external-facing overview. Removed stale DeepSeek 401, Harbor missing, and old `skill-deploy` mainline wording. |
| `README_PROTOTYPE.md` | Downgraded to legacy prototype notes for the old `skill_deployment` lane. |
| `docs/CLAIM_BOUNDARY.md` | Rewritten around current V1 claims and non-claims. |
| `docs/QUICKSTART.md` | Rewritten to use `eskill` as the main path; `skill-deploy` is now legacy. |
| `reports/PUBLIC_VALIDATION_AND_AGENT_USABILITY_STATUS.md` | Updated AgentHost and Harbor statuses. |
| `reports/COMPILER_VS_DIRECT_EVALUATION.md` | Updated AgentHost blocker language and retained no-superiority boundary. |
| `reports/AGENT_HOST_QUALIFICATION.md` | Added Codex Responses smoke result and precise no-compatible-host status. |
| `reports/HARBOR_EXTERNAL_EVAL_STATUS.md` | Updated from 2-case pair smoke to 6-case subset parity pass. |

## Replaced stale statuses

| Old wording | Current wording |
|---|---|
| DeepSeek Judge is HTTP 401 | Independent DeepSeek Judge = `pass` |
| Harbor/Docker/WSL missing | Harbor/Docker/WSL available through `Ubuntu-24.04-Codex`; subset parity passed |
| Harbor is only contract ready | Harbor public OSV oracle/verifier subset parity = `pass_6_of_6` |
| Current main system is Evidence-Grounded Skill Evolution Runtime Prototype | Current main system is Expert Skill Distillation System |
| `skill-deploy` is the main quickstart | `eskill` is the V1 main quickstart |
| `secure_code_review` is the main application line | dependency-advisory applicability is the V1 public validation slice; `secure_code_review` is legacy/earlier lane |

## Current allowed claim boundary

Allowed:

```text
core_local = pass
independent_judge = pass
public_osv_reference_runtime = pass_33_of_33_false_safe_0
harbor_public_osv_parity = public_task_parity_subset_pass
direct_and_compiler_artifacts = distinct
safe_update_reject_rollback = pass
```

Not allowed:

```text
mature AgentHost has passed
Compiler is superior to direct_to_skill_ir
general open-world distillation is proven
stable autonomous Skill evolution is proven
Harbor subset parity is broad benchmark success
OSV applicability means exploitability or reachability
```

## Recommended external reading path

1. `README.md`
2. `reports/PUBLIC_VALIDATION_AND_AGENT_USABILITY_STATUS.md`
3. `docs/design_v03/SYSTEM_ARCHITECTURE_FREEZE_V1.md`
4. `docs/design_v03/EXECUTABLE_ARCHITECTURE_REVIEW.md`
5. `reports/COMPILER_VS_DIRECT_EVALUATION.md`
6. `reports/AGENT_HOST_ROUTE_DECISION.md`
7. `reports/HARBOR_EXTERNAL_EVAL_STATUS.md`
8. `docs/CLAIM_BOUNDARY.md`
