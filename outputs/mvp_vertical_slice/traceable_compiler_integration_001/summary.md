# Traceable Compiler Integration 001

## Positioning

This integration slice combines fixed-budget compact rules, validation gate checks, and skill-to-agent trace protocol.

| Variant | Tokens | Protocol Tokens | Simple | Semantic | Trace | Regression | Gate |
|---|---:|---:|---|---|---|---|---|
| A_plain_compact_skill | 265 / 237 | 0 | False | False | False | True | not gated |
| B_compressed_compact_skill | 195 / 237 | 0 | True | True | False | False | not gated |
| C_compressed_plus_protocol | 300 / 237 | 160 | True | True | True | False | not gated |
| D_compressed_plus_protocol_plus_gate | 300 / 237 | 160 | True | True | True | False | reject_over_budget |

## Questions

- Protocol overhead acceptable: False
- Trace verifier blocks shallow output: True

## Conservative Conclusion

- Status: partially_supported_with_protocol_overhead
- Finding: Protocolized variant passes trace verification but exceeds the fixed token budget.
- Boundary: Toy integration slice only. It does not prove general correctness or a universal compiler.
