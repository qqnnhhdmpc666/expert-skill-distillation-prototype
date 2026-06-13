# SPARK / COLLEAGUE.SKILL / SkillGen / SkillGrad Gap Ledger

## Mainline

Project trunk:

`expert material -> capability normalization -> Skill Package -> execution -> verifier feedback -> typed repair -> Skill evolution -> evidence-qualified promotion`

Boundary:

- QGSE / QGSE-Pareto are promotion-gate layers, not the whole project.
- This ledger tracks structural gaps to adjacent systems work; it does not claim scale parity.

## Gap Table

| Dimension | Related work pressure | Current status | Gap severity | Next implementation | Artifact needed | Stop criterion |
|---|---|---|---|---|---|---|
| Expert-material provenance | COLLEAGUE.SKILL stresses inspectable skill lineage | Controlled provenance now exists per task case in `outputs/skill_lifecycle_evidence/generalization/*/distillation_bundle/` with `source_material.md`, `extracted_candidates.json`, `capability_provenance.json`, and `distillation_trace.json` | medium | Move from keyword projection to stronger distiller outputs with confidence and rejection traces | `capability_provenance.json`, `distillation_trace.json` | At least 5 promoted skills have auditable source spans and post-repair attribution |
| Trajectory evidence | SPARK emphasizes environment-grounded trajectory evidence | Standardized trajectory bundles now exist for offline controlled cases and live Harbor/local repair loops, but offline bundles are still artifact normalization rather than full command/stdout trajectories | high | Unify live runner logging into one append-only trajectory writer across local and Harbor backends | `trajectory.jsonl`, `agent_steps.json`, `target_reads.json` | At least 2 Harbor live repair loops and 1 local live non-security loop share one trajectory schema |
| Success/failure contrastive evolution | SkillGen uses success/failure contrast and net effect | `outputs/validation/skill_net_effect_matrix.json` now exposes no-skill / v1 / v2 deltas on the shared suite, but still at controlled verifier score level | medium | Add per-capability success/failure contrast cards and regression deltas | `skill_net_effect_matrix.json`, per-case contrast cards | Every promoted skill shows no-skill / v1 / v2 comparison and at least one retained failure case |
| Patch evolution mechanism | SkillGrad / SkillGen pressure on update operator quality | Typed repair registry is shared and audited; capability/boundary/contract operators exist and are aligned with policy | medium | Add stronger operator-selection evidence and no-op detection beyond current API/config case studies | `outputs/validation/repair_policy_alignment.json`, `reports/QGSE_FAILURE_CASE_STUDY_CONFIG_API.md` | No known repair feedback type falls back silently; no-op patch detection is automatic |
| With-skill / without-skill net effect | SkillGen asks whether skill actually helps | Controlled matrix now shows average no-skill -> v2 gain `1.0` and upload v1 -> v2 gain `0.6667`, but only for verifier-scored controlled cases | medium | Extend the same matrix to Harbor live loops and negative controls | `outputs/validation/skill_net_effect_matrix.json` | At least 2 live loops and 5 controlled cases share one net-effect report |
| Regression / false-promotion defense | QGSE / challenge-set pressure | Negative controls, verifier stress, promotion challenge sets, fairness audit, and qualification cards are already artifact-backed | low-to-medium | Add stronger baseline mechanisms such as vetoed weighted score and confidence-bounded promotion | `outputs/validation/promotion_mechanism_*.json` | Strong baseline comparison exists and false promotion remains avoided on internal challenge sets |
| Harbor/runtime scale | SPARK pressure on runnable task scale | Harbor upload/config repair loops exist, plus repeatability smoke on upload; live Harbor path is still narrow and partially replay-adapted | high | Add one more live Harbor task family and route more execution through shared runner abstractions | `outputs/harbor_llm_repair_loop_*`, `reports/HARBOR_*` | At least 2 Harbor live families with bounded repair loops and shared trajectory/export path |
| Human usefulness review | Real deployment pressure beyond verifier | Structured reviewer-prep packets now exist in `outputs/reviewer_readiness/`, including opening claims, show-first artifacts, and rubric fields, but they are still internal preparation rather than external/human judgments | medium-to-high | Attach at least one external or advisor-scored review over a promoted skill | reviewer packet + scored external notes | At least 1 promoted skill has external/human usefulness review attached |
| Versioned lifecycle / deployability | COLLEAGUE.SKILL lifecycle pressure | A generated installation registry now exists in `outputs/installed_skills/` with version directories, active manifests, deployment records, and rollback history; still a prototype surface rather than a production package manager | medium | Add CLI lifecycle verbs and scope-aware activation/deactivation beyond generated receipts | lifecycle manifest, install/rollback record | One promoted skill can be installed, scoped, and rolled back via a documented path |
| Review package / reproducibility maturity | Systems artifact expectation | Review package export and validation already work; new lifecycle evidence is now ready to export too | low | Include lifecycle evidence and gap ledger in export by default and keep validation green | `review_package_export.zip`, `scripts/validate_review_package.py` | Export contains lifecycle bundles, gap ledger, and passes validation with zero errors |

## Current reading

- Strongest closed-loop evidence is still controlled rather than open-world.
- The biggest remaining structural gaps are live trajectory richness, Harbor scale, and human usefulness review.
- The biggest newly reduced gap is provenance: expert note -> normalized capability -> v1/v2 -> repair attribution is now explicit and exportable.

## Honest comparison

What now looks meaningfully closer:

- SPARK-style emphasis on posterior evidence over prior intent
- COLLEAGUE-style versioned skill artifacts and lifecycle traceability
- SkillGen-style net-effect and retained failure evidence
- SkillGrad-style pressure toward structured update operators rather than free-form rewriting

What is still clearly behind:

- live trajectory richness
- broad task scale
- open-world usefulness proof
- stronger multi-mechanism promotion benchmarks
- mature deploy/install/rollback surface
