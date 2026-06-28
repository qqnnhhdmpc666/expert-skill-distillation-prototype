# Expert Knowledge Ablation + Controlled Access v0 Status

- expert_knowledge_ablation_v0_status: `pass`
- backend: `mini_swe_agent_real_llm`
- model: `deepseek-chat`
- real_mini_swe_agent_executed_count: `6`
- anti_leakage_status: `pass`
- knowledge_access_status: `pass`
- claim_boundary_status: `pass`

## Conditions
- no_expert_knowledge: executed=`True`, pass=`False`, failure=`missing_knowledge`
- raw_expert_material: executed=`True`, pass=`False`, failure=`missing_knowledge`
- distilled_skill_only: executed=`True`, pass=`False`, failure=`missing_knowledge`
- distilled_knowledge_only: executed=`True`, pass=`False`, failure=`missing_skill_rule`
- distilled_skill_plus_knowledge: executed=`True`, pass=`True`, failure=`none`
- distilled_skill_plus_controlled_access: executed=`True`, pass=`True`, failure=`none`

## Boundary

This is a bounded mechanism micro-study. It is not an official benchmark result, compiler-superiority result, production-readiness result, or proof that expert knowledge transfer is solved.
