# Real API Backend x Condition x Lane Matrix

| lane | backend | condition | execution_status | executed | pass | claim_counted | note |
| --- | --- | --- | --- | ---: | ---: | --- | --- |
| `document_to_agent_real_api` | `mini_swe_agent_real_llm` | `no_skill` | `executed` | 1 | 0 | `True` | real DeepSeek-backed agent row with local domain verifier |
| `document_to_agent_real_api` | `mini_swe_agent_real_llm` | `document_to_agent_bundle` | `executed` | 1 | 1 | `True` | real DeepSeek-backed agent row with local domain verifier |
| `skillsbench_micro` | `mini_swe_agent_real_llm` | `no_skill` | `blocked` | 0 | 0 | `False` | SkillsBench repository/package/data not available locally; no fabricated task used |
| `skillsbench_micro` | `mini_swe_agent_real_llm` | `document_to_agent_bundle` | `blocked` | 0 | 0 | `False` | SkillsBench repository/package/data not available locally; no fabricated task used |
| `skillgen_mapping` | `mini_swe_agent_real_llm` | `no_skill` | `skipped` | 0 | 0 | `False` | mapped_not_executed; official SkillGenBench/Anything2Skill harness not run |
| `skillgen_mapping` | `mini_swe_agent_real_llm` | `document_to_agent_bundle` | `skipped` | 0 | 0 | `False` | mapped_not_executed; official SkillGenBench/Anything2Skill harness not run |
| `swebench_micro` | `mini_swe_agent_real_llm` | `no_skill` | `blocked` | 0 | 0 | `False` | docker_cli_not_visible |
| `swebench_micro` | `mini_swe_agent_real_llm` | `document_to_agent_bundle` | `blocked` | 0 | 0 | `False` | docker_cli_not_visible |
