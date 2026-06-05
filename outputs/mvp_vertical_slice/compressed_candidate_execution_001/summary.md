# Compressed Candidate Execution 001

## Positioning

This slice checks whether candidate_C can drive agent output beyond rule-id coverage, using both the existing local verifier and a stricter semantic verifier.

| Case | Agent | Rule IDs | Local Pass | Semantic Pass | Missing | Notes |
|---|---|---|---|---|---|---|
| case001 | mock | R001, R002, R003, R004, R005, R006 | True | True | none | mock agent uses rule IDs from skill and deterministic findings; semantic verifier checks field and trigger content. |
| case002 | mock | R001, R002, R003, R004, R005, R006 | True | True | none | mock agent uses rule IDs from skill and deterministic findings; semantic verifier checks field and trigger content. |
| case001 | rightcode_gpt | R001, R002, R003, R004, R005, R006 | True | True | none | External LLM run; skipped if endpoint credentials are unavailable. |
| case002 | rightcode_gpt | R001, R002, R003, R004, R005, R006 | True | True | none | External LLM run; skipped if endpoint credentials are unavailable. |

## Conclusion

- Status: partially_supported
- Finding: Candidate_C passes semantic execution validation for available agents in this toy slice.
- Boundary: Toy execution validation only. Passing this slice does not prove a general fixed-budget compiler.
