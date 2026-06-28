# Expert Knowledge Ablation v0 Failure Attribution

| condition | failure_type | can_drive_revision |
| --- | --- | --- |
| `no_expert_knowledge` | `missing_knowledge` | `True` |
| `raw_expert_material` | `missing_knowledge` | `True` |
| `distilled_skill_only` | `missing_knowledge` | `True` |
| `distilled_knowledge_only` | `missing_skill_rule` | `True` |
| `distilled_skill_plus_knowledge` | `none` | `False` |
| `distilled_skill_plus_controlled_access` | `none` | `False` |
