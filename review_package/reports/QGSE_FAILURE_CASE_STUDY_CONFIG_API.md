# QGSE Failure Case Study: Config And API Review

## Purpose

These two failures are not cleanup noise. They are important evidence that Qualification-Guided Skill Evolution is not a success wrapper. It can distinguish:

- a repair that lands structurally but does not change agent behavior;
- a repair action that is effectively a no-op before behavior claims should be trusted.

## Case 1: Local Live LLM Config

Artifact: `outputs/live_llm_repair_loop_config_security_001/summary.json`

Observed chain:

- A1 fails with `missing_capability`.
- Missing capability: `CONFIG_ENV_GUARD`.
- Repair action: `patch_capability`.
- Before capabilities: `CONFIG_AUDIT_EXPORT`.
- After capabilities: `CONFIG_AUDIT_EXPORT`, `CONFIG_ENV_GUARD`.
- A2 still fails with `CONFIG_ENV_GUARD` missing.

QGSE interpretation:

| Gate | Result | Reason |
|---|---|---|
| Integrity Gate | pass | The missing capability appears in the revised manifest. |
| Behavior Gate | fail | A2 still misses the same capability. |
| Robustness Gate | not measured | Robustness is not meaningful until behavior improves. |

Failure origin:

- Primary: `skill_to_execution_gap`
- Secondary: `llm_instruction_following_failure`

Qualification:

- `decision = quarantine`
- `promotion_level = L0_NON_PROMOTABLE`
- `claim_scope = controlled local config slice only`

Why this matters:

If the system only used reward or gate acceptance, it could miss this failure. QGSE blocks promotion because the revised Skill did not produce the intended behavior.

## Case 2: Local Live LLM API Review

Artifact: `outputs/live_llm_repair_loop_api_review_001/summary.json`

Observed chain:

- A1 fails with `missing_capability`.
- Missing capability: `API_OVERBROAD_RISK`.
- Repair action: `patch_capability`.
- Before capabilities already include `API_OVERBROAD_RISK`.
- After capabilities are unchanged.
- A2 still fails with `API_OVERBROAD_RISK` missing.

QGSE interpretation:

| Gate | Result | Reason |
|---|---|---|
| Integrity Gate | fail | `patch_capability` did not add or change the required capability. |
| Behavior Gate | fail | A2 still misses the same capability. |
| Robustness Gate | not measured | Robustness is not meaningful until integrity and behavior are fixed. |

Failure origin:

- Primary: `repair_operator_noop_or_patch_application_failure`
- Secondary: `skill_to_execution_gap`

Qualification:

- `decision = reject`
- `promotion_level = L0_NON_PROMOTABLE`
- `claim_scope = controlled local API review slice only`

Why this matters:

This catches a repair-compiler/operator issue before the system can claim behavior improvement. It is a stronger diagnosis than simply saying "A2 failed."

## Lesson

The project should preserve these failures as diagnostic evidence. They show why the upgrade mechanism needs gates instead of a single score:

- reward-delta-only would not explain why config failed;
- gate-only would over-trust accepted patches;
- weighted scores can hide hard blockers;
- QGSE separates structural repair failure from behavioral non-use.

The next implementation step is not to force these cases to pass. It is to fix the failure origin and rerun qualification.
