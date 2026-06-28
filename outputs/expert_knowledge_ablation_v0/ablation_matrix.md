# Expert Knowledge Ablation v0 Matrix

| condition | executed | verifier_pass | evidence_completeness | failure_type | tokens | claim_counted |
| --- | --- | --- | ---: | --- | ---: | --- |
| `no_expert_knowledge` | `True` | `False` | 0.50 | `missing_knowledge` | 3531 | `True` |
| `raw_expert_material` | `True` | `False` | 0.50 | `missing_knowledge` | 3852 | `True` |
| `distilled_skill_only` | `True` | `False` | 0.50 | `missing_knowledge` | 3700 | `True` |
| `distilled_knowledge_only` | `True` | `False` | 0.50 | `missing_skill_rule` | 5155 | `True` |
| `distilled_skill_plus_knowledge` | `True` | `True` | 1.00 | `none` | 6047 | `True` |
| `distilled_skill_plus_controlled_access` | `True` | `True` | 1.00 | `none` | 4633 | `True` |
