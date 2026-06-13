# Qualification-Guided Skill Evolution

## Position

The current project should not be framed as a new single score, a full SPARK-PDI reproduction, or a generic vulnerability scanner. The stronger and more defensible framing is:

> Feedback proposes revision; qualification decides promotion.

In other words, verifier feedback may identify what should change, but the revised Skill Package should only be promoted after a structured qualification protocol decides whether the change actually landed, changed agent behavior, survived robustness checks, and deserves a bounded evidence level.

This moves the project from "feedback-driven skill revision" to "qualification-guided skill promotion."

## Why A Single Metric Is Not Enough

An A2 PASS or reward improvement is useful, but it is not sufficient evidence that a Skill has genuinely improved. A single score can hide at least four failure modes:

- The repair did not actually land in the Skill Package, but the rerun passed for another reason.
- The Skill changed structurally, but the agent did not use the new instruction.
- The verifier accepted overfitted or fabricated evidence.
- The result works for the current task, but collapses on clean, swapped, held-out, or metamorphic variants.

Therefore this system should not ask only "is Skill v2 better?" It should ask:

- What evidence supports promotion?
- What scope is supported?
- Which failure source blocks promotion?
- What evidence is still missing?

## Gate 1: Integrity Gate

Question: did the revision really land?

Checks:

- `patch_plan.json` exists and is linked to A1 verifier feedback.
- The selected repair operator matches the feedback type.
- Skill v2 manifest, contract, or prompt changed in the expected place.
- The revised Skill contains the missing capability or contract requirement.
- The verifier/gate was not relaxed to manufacture a PASS.
- No expected answer or API secret leaked into prompt, artifacts, reports, or review package.

Failure outcome: `REJECT`.

Current examples:

- `live_llm_upload_repair_loop`: integrity supported, because A1 missing upload capabilities appear in Skill v2.
- `live_llm_api_review_repair_loop`: integrity is weak/failing, because `patch_capability` was selected while the before/after capability list is unchanged.

## Gate 2: Behavior Gate

Question: did the agent actually behave better after the revised Skill?

Checks:

- A2 output reflects the new capability or stricter contract.
- Coverage, schema correctness, evidence binding, or regression safety improves.
- The same missing capability does not remain missing after repair.
- Evidence spans are grounded in the target asset.
- The deterministic verifier reads the generated agent output, not a hidden template.

Failure outcome: `QUARANTINE`.

Current examples:

- `harbor_llm_upload_repair_loop`: behavior supported, because A1 fails with missing upload capabilities and A2 passes in Harbor.
- `live_llm_config_security_repair_loop`: behavior fails, because Skill v2 adds `CONFIG_ENV_GUARD` but A2 still misses it. This is a skill-to-execution gap, not a successful repair.

## Gate 3: Robustness Gate

Question: is this improvement robust, or is it verifier overfitting?

Checks:

- Negative controls reject unsupported evidence.
- Clean targets do not acquire append-style false positives.
- Swapped targets or fabricated evidence are rejected.
- Metamorphic variants preserve or change findings in expected ways.
- Repeated runs have stable failure and success patterns.
- Visible verifier success does not become the only proof.

Failure outcome: restrict promotion level and claim scope. Robustness failure may not invalidate a single task result, but it prevents broad claims.

Current examples:

- `negative_controls.json` supports unsupported-evidence and false-positive rejection.
- `verifier_stress_checks.json` supports stricter target-text binding.
- `harbor_llm_repeatability_upload.json` supports a small repeatability smoke for upload only.

## Gate 4: Promotion Evidence

Question: to which evidence level can this revised Skill be promoted?

Promotion levels:

| Level | Name | Meaning |
|---|---|---|
| L0 | `REJECT` | Structural error, leakage, fake evidence, verifier relaxation, or no behavior improvement. |
| L1 | `CANDIDATE` | Current task improves, but there is little repeatability, holdout, or robustness evidence. |
| L2 | `PROMOTE_LOCAL` | Local live LLM or local semantic execution shows stable improvement in a controlled slice. |
| L3 | `PROMOTE_CONTROLLED` | Multiple controlled tasks, negative controls, and metamorphic checks support the claim. |
| L4 | `PROMOTE_SANDBOXED` | Harbor/Docker sandbox loop also closes under bounded conditions. |
| L5 | `PROMOTE_REVIEWED` | Human/external task review supports usefulness beyond contract compliance. |

The key difference from a scorecard is that the result is not "high score means good." The result is a scoped promotion decision.

## Current Evidence Classification

| Slice | Current qualification reading |
|---|---|
| Offline generalization suite | `L3_PROMOTE_CONTROLLED` support for controlled pipeline reuse, not open-world generalization. |
| Local live LLM upload | `L2_PROMOTE_LOCAL`, because A1 fails, repair lands, and A2 passes locally. |
| Local live LLM data quality | `L2_PROMOTE_LOCAL`, because output-contract feedback repairs a non-security task locally. |
| Local live LLM config | `L0_REJECT` / quarantine, because patch lands but behavior does not improve. |
| Local live LLM API review | `L0_REJECT`, because the capability patch is effectively a no-op and A2 still misses the same capability. |
| Harbor live LLM upload | `L4_PROMOTE_SANDBOXED` under a controlled upload scope, strengthened by repeatability smoke. |
| Harbor live LLM config | `L4_PROMOTE_SANDBOXED` under a controlled config scope, but less robust than upload because repeatability is not measured. |
| Negative controls | Robustness support, not a standalone deployment claim. |

## Relation To Prior Work

This project should not claim to invent feedback, self-revision, or Skill Packages. The honest positioning is:

- Self-Refine, Reflexion, and ExpeL motivate turning feedback into reusable experience, but they do not decide when a revised Skill Package deserves promotion.
- Voyager and other skill-library systems motivate accumulating reusable skills, but this project focuses on bounded deployable packages and evidence-backed promotion.
- DSPy and agent-system optimization work motivate programmatic optimization, but QGSE avoids relying on one metric as the promotion authority.
- SWE-agent style work reminds us that failure may originate from the interface, runner, verifier, contract, or target binding, not only from the Skill.
- Metamorphic testing and the oracle problem motivate robustness checks when no single perfect answer exists.
- Assurance-case and FMEA thinking motivate claim-argument-evidence structure and failure-origin attribution.

The differentiating problem is the qualification problem after posterior Skill revision: a patch may be proposed by feedback, but only qualification gates decide whether it can be accepted, quarantined, rejected, or promoted with a limited claim scope.

## Implementation Direction

The existing validity card layer is useful but too descriptive. It should be upgraded with a qualification card layer that records:

- `integrity_gate`
- `behavior_gate`
- `robustness_gate`
- `promotion_level`
- `failure_origin`
- `claim_scope`
- `next_required_evidence`

The new implementation entry point is `scripts/run_skill_qualification_cards.py`, which writes:

- `outputs/validation/skill_qualification_cards.json`
- `reports/SKILL_QUALIFICATION_CARD_STATUS.md`

This is the research spine: the system does not merely show that A2 can pass; it records why a Skill revision is or is not qualified for promotion.

## Mechanism Exploration

QGSE should remain the current best mechanism, not a frozen assumption. The repository now compares candidate promotion mechanisms:

- reward-delta-only;
- gate-only;
- weighted validity score;
- Pareto conservative;
- QGSE protocol.

Run:

```powershell
python scripts/compare_promotion_mechanisms.py
```

Outputs:

- `outputs/validation/promotion_mechanism_comparison.json`
- `reports/PROMOTION_MECHANISM_EXPLORATION.md`

Current result: QGSE is the best current mechanism because it separates `RevisionQualificationCard` from `EvidenceSupportCard`, preserves hard blockers, forces claim scope, and records failure origin. This conclusion should be revisited when stronger human-review, held-out, and metamorphic evidence is available.

Important boundary: "best current" means best under the current grounded-label interpretation. It is not yet validated by hidden external tasks or human usefulness labels.

The next candidate mechanism is a QGSE + Conservative Pareto hybrid. QGSE handles hard red lines, failure attribution, and claim scope; Pareto dominance prevents promotion when an improvement on one dimension is accompanied by regression in another critical dimension such as evidence grounding, false positives, cost, metamorphic stability, or human usefulness.

Challenge-set entry point:

```powershell
python scripts/run_promotion_mechanism_challenge_set.py
```

Outputs:

- `outputs/validation/promotion_mechanism_challenge_set.json`
- `reports/PROMOTION_MECHANISM_CHALLENGE_SET_STATUS.md`
