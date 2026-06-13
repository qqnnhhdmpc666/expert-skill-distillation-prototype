# Method Validity Audit

## Core method, stated narrowly

The current core method is:

> scenario-conditioned expert material is compiled into a deployable Skill Package; execution artifacts are checked by a deterministic verifier; verifier feedback is mapped to typed repair operators; a gate decides whether the repaired package should be promoted to A2.

This is **not** “the pipeline” in the vague sense. The real method kernel is:

1. typed capability package
2. deterministic verifier surface
3. feedback taxonomy
4. typed posterior repair
5. promotion gate

## What the current verifier really validates

Strongly validated in controlled slices:

- capability coverage
- missing capability detection
- output contract compliance
- evidence-field presence
- some false-positive rejection
- some unsupported-evidence rejection
- controlled regression blocking through the gate

Weakly or not yet validated:

- deep semantic correctness of natural-language findings
- human usefulness of A2 relative to A1
- open-world transfer
- adversarial prompt attacks on the LLM path
- broad robustness to semantically tricky but schema-correct reports
- causal sufficiency of one verifier score as a proxy for “better skill”

## Is A1 -> A2 improvement attributable?

### Yes, in the narrow controlled sense

The current best evidence for attribution is:

- `outputs/validation/generalization_suite.json`
- `outputs/validation/ablation_summary.json`
- `outputs/harbor_llm_repair_loop_upload_001/summary.json`
- `outputs/harbor_llm_repair_loop_config_001/summary.json`

These show:

- different failures trigger different repair actions
- different repair strategies produce different outcomes
- Harbor upload and config loops each improve after a specific repair

### But attribution is not fully causal proof

Current limits:

- offline deterministic paths partially encode expected capability structure
- LLM prompts still operate in a narrow controlled setup
- no human intervention audit quantifies whether the repaired report is genuinely more useful, not just verifier-compliant

## Leakage / overfitting risk audit

### Real risks

1. offline deterministic execution uses capability-specific evidence hints
2. repair operators know the expected capability set
3. verifier success is still the dominant acceptance criterion
4. the current task suite is small and intentionally shaped

### Mitigations already present

1. negative controls reject unsupported evidence and clean-target false positives
2. Harbor LLM loops use real agent outputs rather than hand-authored A2 JSON
3. repeatability smoke reduces the chance that one Harbor upload pass is a fluke
4. claim-boundary docs already avoid open-world generalization claims

## Strongest current evidence

1. five-task offline controlled suite
2. two-task executable ablation
3. two negative controls
4. Harbor upload LLM repair loop
5. Harbor config LLM repair loop
6. Harbor upload repeatability smoke

## Weakest current assumptions

1. verifier pass still stands in for “better skill” too often
2. semantic quality and usefulness are not independently judged
3. cross-task transfer beyond five controlled families is unmeasured
4. repeatability is only measured on one Harbor upload slice
5. local “semantic” agents are still deterministic heuristics

## Top 10 Risks

1. verifier overfitting to the package/report contract
2. hidden dependence on expected capabilities
3. controlled task bias
4. missing human usefulness evaluation
5. weak open-world robustness evidence
6. prompt sensitivity under broader Harbor LLM usage
7. limited negative-control coverage
8. repair operators looking strong only because the failure taxonomy is small
9. semantic-but-wrong reports passing if they satisfy schema and keyword evidence
10. research claims drifting from controlled evidence into general agent claims

## Next 5 Highest-Value Fixes

1. add a small human review sheet for A1 vs A2 usefulness
2. broaden negative controls beyond unsupported evidence / clean-config false positives
3. add at least one more Harbor LLM task with repeated runs
4. separate verifier modules into coverage, evidence, schema, and regression layers with independent reports
5. add one holdout task family that requires new observation structure, not just new capability IDs

## Verdict

Current method validity is best described as **moderate controlled evidence**. The system clearly demonstrates typed posterior repair over inspectable Skill Packages. It does **not** yet demonstrate open-world autonomous skill improvement in the strong sense.
