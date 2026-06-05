# Skill-to-Agent Execution Protocol

This document introduces M5 in the method-discovery loop:

```text
Skill-to-Agent Execution Protocol
```

It does not replace M2. M2 asks how to generate a compact skill under budget. M5 asks how that compact skill should be invoked by an agent so that rule use is observable and verifiable.

## Motivation

The M2.2 semantic-preservation audit showed that compressed wording can preserve compact rule semantics in a toy slice. But there is a deeper risk:

```text
An agent may output rule IDs without truly applying rules to case evidence.
```

If the verifier only checks rule-id coverage, compact skills can drift toward shortcut tables rather than executable expert knowledge.

## Hypothesis

Compact skill used as a plain prompt may lose correctness in complex tasks. A structured invocation protocol can make the agent expose a rule-application trace, helping distinguish mechanical rule-id output from real rule application.

## Trigger Condition

Use M5 when:

- compact skill has been compressed,
- verifier may only check rule-id coverage,
- agent output lacks evidence linkage,
- or semantic verifier flags template-like findings.

## Protocol Schema

```json
{
  "rule_applications": [
    {
      "rule_id": "R005",
      "applicable": true,
      "trigger_condition_found": "response envelope missing request_id",
      "evidence_span": "Response JSON has code, message, data",
      "finding_id": "F5",
      "confidence": "medium"
    }
  ],
  "findings": [
    {
      "id": "F5",
      "rule_id": "R005",
      "issue": "Response envelope lacks request_id.",
      "severity": "medium",
      "evidence": "Response contains code, message, and data but no request_id."
    }
  ]
}
```

## Decision Rule

Do not only pass compact skill to the agent. Require:

- `rule_applications` for each finding,
- `evidence_span` grounded in case text,
- `trigger_condition_found` tied to the rule,
- matching `finding_id`,
- confidence label,
- and a non-template finding.

## Alternative / Counterfactual

Compare:

- plain compressed skill + simple verifier,
- rule-id shortcut skill + stricter verifier,
- protocolized compressed skill + trace verifier.

## Current Artifact

```text
outputs/mvp_vertical_slice/skill_to_agent_loop_001
```

## Conservative Claim

If protocolized compressed skill passes the trace verifier while rule-id shortcut fails, the current conclusion is:

```text
partially_supported: structured skill-to-agent protocol helps distinguish semantic rule use from rule-id shortcut in this toy case.
```

Do not claim:

- real complex-task correctness is proven,
- a general agent protocol is proven,
- or this replaces trajectory-level verification.

## Integration With Compact Compilation

M5 is now integrated with M2 and M3 in:

```text
outputs/mvp_vertical_slice/traceable_compiler_integration_001
```

The integrated deployment artifact is no longer just:

```text
compact_skill.md
```

It is:

```text
compact skill rules
+ invocation protocol
+ trace verifier contract
```

Current finding:

- Plain compressed skill can pass simple/semantic verification but still fail trace verification.
- Protocolized compressed skill can pass trace verification.
- The current protocol adds enough tokens to exceed the fixed budget.
- The validation gate therefore rejects the protocolized candidate under the current constraint.

Conservative interpretation:

```text
partially_supported_with_protocol_overhead
```

The protocol is useful as a verifier contract, but it must be compressed or amortized before it can be treated as a low-cost deployment layer.
