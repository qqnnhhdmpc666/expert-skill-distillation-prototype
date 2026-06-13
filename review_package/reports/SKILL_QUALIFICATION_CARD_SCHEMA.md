# Skill Qualification Card Schema

## Purpose

A Skill Qualification Card is the decision record for a revised Skill Package. It is stricter than a validity card: it decides whether a revision can be promoted, quarantined, or rejected.

The principle is:

> Feedback proposes revision; qualification decides promotion.

## JSON Shape

```json
{
  "card_id": "harbor_llm_upload_repair_loop",
  "card_type": "RevisionQualificationCard",
  "artifact": "outputs/harbor_llm_repair_loop_upload_001",
  "scenario": "real-upload-security-review",
  "backend": "harbor_live_llm",
  "qualification_decision": "promote_with_scope_limit",
  "promotion_level": "L4_PROMOTE_SANDBOXED_WITH_SCOPE_LIMIT",
  "claim_scope": "Controlled sandboxed repair-loop evidence for real-upload-security-review only; no broad Harbor/backend generalization.",
  "gates": {
    "integrity_gate": {
      "status": "pass",
      "evidence": "A1 missing capabilities are represented in the revised capability manifest."
    },
    "behavior_gate": {
      "status": "pass",
      "evidence": "A2 passes the deterministic verifier after the revision."
    },
    "robustness_gate": {
      "status": "partial",
      "evidence": "The loop closes in Harbor, but repeatability/metamorphic evidence is still narrow."
    }
  },
  "observed_delta": {
    "a1_pass": false,
    "a2_pass": true,
    "coverage_delta": 0.6667,
    "schema_delta": 0.0,
    "evidence_delta": 0.0,
    "a1_feedback_type": "missing_capability",
    "a2_feedback_type": "pass",
    "repair_action": "patch_capability",
    "gate_decision": "accept"
  },
  "next_required_evidence": [
    "Add negative, swapped-target, fake-evidence, and metamorphic controls.",
    "Attach human or external review before broad deployment claims."
  ],
  "sources": [
    "outputs/harbor_llm_repair_loop_upload_001/summary.json"
  ]
}
```

## Field Semantics

| Field | Meaning |
|---|---|
| `card_id` | Stable ID for this qualification decision. |
| `artifact` | Directory or validation file that grounds the card. |
| `scenario` | Task scenario or evidence slice. |
| `backend` | Execution backend, such as `live_llm_text` or `harbor_live_llm`. |
| `qualification_decision` | `reject`, `quarantine`, `candidate_only`, `promote_with_scope_limit`, or `supporting_evidence`. |
| `card_type` | `RevisionQualificationCard` for A1 -> A2 repair-loop decisions, or `EvidenceSupportCard` for supporting evidence. |
| `promotion_level` | Only for `RevisionQualificationCard`: one of `L0_NON_PROMOTABLE`, `L1_CANDIDATE`, `L2_PROMOTE_LOCAL_WITH_SCOPE_LIMIT`, `L3_PROMOTE_CONTROLLED`, `L4_PROMOTE_SANDBOXED_WITH_SCOPE_LIMIT`, `L5_PROMOTE_REVIEWED`. |
| `support_level` | Only for `EvidenceSupportCard`; describes what promotion level the evidence can support, without promoting a Skill by itself. |
| `claim_scope` | The strongest safe claim supported by this card. |
| `gates.integrity_gate` | Whether the revision truly landed and did not relax the verifier. |
| `gates.behavior_gate` | Whether A2 behavior materially improved after the revision. |
| `gates.robustness_gate` | Whether negative, repeatability, sandbox, or metamorphic checks constrain overfitting. |
| `observed_delta` | A1/A2 deltas derived from deterministic verifier reports. |
| `next_required_evidence` | The next evidence needed to raise the promotion level. |
| `sources` | Artifact paths that a reviewer can open to audit the decision. |

## Gate Status Vocabulary

| Status | Meaning |
|---|---|
| `pass` | Evidence directly supports this gate. |
| `partial` | Evidence is useful but incomplete or narrow. |
| `fail` | Evidence contradicts promotion. |
| `not_measured` | The required check has not been performed. |

## Decision Rules

- If the Integrity Gate fails, the card is `reject` and promotion level is `L0_NON_PROMOTABLE`.
- If Integrity passes but Behavior fails, the card is `quarantine` and promotion level is `L0_NON_PROMOTABLE`.
- If A2 improves but robustness is not measured, the card can be at most `L1_CANDIDATE`.
- If a local live LLM or local semantic loop passes under controlled conditions, the card can reach `L2_PROMOTE_LOCAL_WITH_SCOPE_LIMIT`.
- If multiple controlled task families and negative/metamorphic evidence support the behavior, the card can reach `L3_PROMOTE_CONTROLLED`.
- If the repair loop closes inside Harbor/Docker, the card can reach `L4_PROMOTE_SANDBOXED_WITH_SCOPE_LIMIT`, but only for the tested scope.
- `L5_PROMOTE_REVIEWED` requires human or external task review and is not currently claimed.

## Current Implementation

Run:

```powershell
python scripts/run_skill_qualification_cards.py
```

Outputs:

- `outputs/validation/skill_qualification_cards.json`
- `reports/SKILL_QUALIFICATION_CARD_STATUS.md`

The card generator is intentionally conservative. It downgrades local config/API failures instead of hiding them behind aggregate success.

## Card Type Split

`RevisionQualificationCard` answers whether one revised Skill Package can be accepted, quarantined, rejected, or promoted with scope.

`EvidenceSupportCard` answers whether a validation artifact supports a promotion decision elsewhere. Negative controls, repeatability smokes, and generalization suites are evidence support cards; they do not mean a specific Skill was promoted by themselves.
