# Skill-to-Agent Loop 001

## Positioning

This is an M5 probe: compact skill should not only enter the prompt; the agent should expose rule-application traces that a verifier can inspect.

| Case | Agent | Variant | Rule IDs | Has Trace | Local | Semantic | Trace |
|---|---|---|---|---|---|---|---|
| case001 | mock | candidate_C_compressed_skill | R001, R002, R003, R004, R005, R006 | False | True | True | False |
| case001 | mock | rule_id_shortcut_skill | R001, R002, R003, R004, R005, R006 | False | True | True | False |
| case001 | mock | protocolized_compressed_skill | R001, R002, R003, R004, R005, R006 | True | True | True | True |
| case002 | mock | candidate_C_compressed_skill | R001, R002, R003, R004, R005, R006 | False | True | True | False |
| case002 | mock | rule_id_shortcut_skill | R001, R002, R003, R004, R005, R006 | False | True | True | False |
| case002 | mock | protocolized_compressed_skill | R001, R002, R003, R004, R005, R006 | True | True | True | True |
| case001 | rightcode_gpt | candidate_C_compressed_skill | R001, R002, R003, R004, R005, R006 | True | False | False | False |
| case001 | rightcode_gpt | rule_id_shortcut_skill | R001, R002, R003, R004, R005, R006 | True | False | False | False |
| case001 | rightcode_gpt | protocolized_compressed_skill | R001, R002, R003, R004, R005, R006 | True | True | True | True |
| case002 | rightcode_gpt | candidate_C_compressed_skill | R001, R002, R003, R004, R005, R006 | True | False | False | False |
| case002 | rightcode_gpt | rule_id_shortcut_skill | R001, R002, R003, R004, R005, R006 | True | False | False | False |
| case002 | rightcode_gpt | protocolized_compressed_skill | R001, R002, R003, R004, R005, R006 | True | True | True | True |

## Conservative Conclusion

- Status: partially_supported
- Finding: Structured protocol helps distinguish rule-application traces from rule-id shortcut in this toy case.
- Boundary: Toy protocol probe only. It does not prove real complex-task correctness or a general agent protocol.
