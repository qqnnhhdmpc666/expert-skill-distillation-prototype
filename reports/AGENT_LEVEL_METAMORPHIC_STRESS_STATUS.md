# Agent-Level Metamorphic Stress Status

Overall pass: `False`

This is agent-level because the local non-oracle semantic agent reads the transformed target and Skill manifest, emits findings, and then the verifier checks the metamorphic relation. It is still deterministic and not a live LLM stress test.

A failed relation is retained as useful evidence: it marks a skill-to-agent or detector-to-evidence limitation that should constrain promotion scope.

| Case | Scenario | Transform | Findings | Feedback | Control passed |
|---|---|---|---:|---|---|
| agent_upload_clean_target | upload_security | clean target removes upload weaknesses | 1 | false_positive_risk | False |
| agent_config_clean_target | config_security | clean production config | 1 | false_positive_risk | False |
| agent_data_quality_row_shuffle | data_quality | row/order presentation shuffle | 3 | unsupported_evidence | False |
| agent_api_injected_risk | api_review | inject overbroad endpoint risk | 2 | pass | True |
