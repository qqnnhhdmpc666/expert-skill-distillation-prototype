# Iterative Contract Runtime Status Snapshot

Date: 2026-06-13 Asia/Shanghai
Repository workspace: `expert-skill-distillation-prototype-main`

This snapshot summarizes the latest local state after the long autonomous Contract-Grounded Skill Evolution Runtime sprint. It is not a full worktree push. The local directory is currently not a git repository, and `gh` is not authenticated, so full code synchronization still requires git/gh auth or a tree-level upload path.

## Current Judgment

```text
controlled_internal: pass
security_depth: pass_local_bounded
non_oracle_execution: pass
non_oracle_effectiveness: pass
non_oracle_behavior: pass
live_llm_execution: pass
live_llm_effectiveness: partial
live_llm_behavior: partial
live_contract_effectiveness: pass
external_generalization: partial
holdout_generalization: pass_local_holdout
activation_ablation: supports_mechanism
mechanism_ablation: supports_mechanism
candidate_generation: pass
evolution_safety_gate: pass
evolution_improvement: demonstrated
evolution_maturity: improvement_demonstrated
external_harness: infra_blocked
open_source_prototype_readiness: pass
public_release_readiness: pass
open_source_readiness: prototype_pass
academic_claim_readiness: strong_candidate_with_external_gap
```

## Fresh Evidence Highlights

- Live contract representative validation: 7/7 completed, 7/7 after-normalizer pass, false positives 0, evidence exact match rate 1.0.
- External/semiexternal generalization: 12/12 completed, 9/12 effective pass, false positives 0, unsupported retained 3, ambiguous handled 1, live LLM pass rate 0.75.
- Mechanism ablation: supports mechanism, with active contract path preserving zero scope violations while all-capabilities/no-router/simple prompt variants show scope discipline failures.
- Iterative contract improvement: 5 candidates tested, 2 staged promotion proposals, best candidate `c006_combo`, score delta +0.05, false-positive delta 0, schema delta 0, unsupported-evidence delta 0, positive regressions 0.
- SWE-bench official harness remains infra_blocked due environment image/dependency download failure. No SWE-bench success is claimed.

## Key Local Artifacts

```text
reports/LIVE_CONTRACT_VALIDATION_STATUS.md
outputs/live_contract_validation/live_contract_validation_summary.json
reports/EXTERNAL_GENERALIZATION_VALIDATION_STATUS.md
outputs/external_generalization_validation/external_generalization_summary.json
reports/LIVE_MECHANISM_ABLATION_STATUS.md
outputs/mechanism_ablation/live_contract/live_mechanism_ablation_summary.json
reports/ITERATIVE_CONTRACT_IMPROVEMENT_STATUS.md
outputs/iterative_contract_improvement/iterative_contract_improvement_summary.json
reports/GRAND_AUTONOMOUS_SPRINT_STATUS.md
reports/ACADEMIC_CLAIM_READINESS_ASSESSMENT.md
reports/REPRESENTATIVE_VALIDATION_MATRIX.md
reports/FRAMEWORK_MATURITY_EVIDENCE_LEDGER.md
review_package/MANIFEST.json
```

## Validation Commands Passed

```text
python -m pytest -q
46 passed in 0.31s

python scripts\validate_task_cases.py
status=ok, case_count=8

skill-deploy validate-review-package
status=ok, error_count=0
```

## Secret Handling

The DeepSeek API key was used only as a process environment variable for live calls. A literal-key scan over reports, outputs, docs, review_package, scripts, src, agents, and top-level handoff/docs found no copy of the provided key. Generic scans only found placeholders and code variable names.

Because the key appeared in chat, rotation is still recommended.

## Boundary

This remains a research-grade prototype, not a production vulnerability scanner, not an official CyberSecEval/AutoPatchBench/CVE-Bench result, and not SWE-bench agent success. The new stronger claim is limited to a contract-grounded live runtime with staged improvement evidence and an explicit external official benchmark gap.
