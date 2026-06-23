# Compiler vs Direct-to-Skill-IR Evaluation

Date: 2026-06-23

```text
direct_generation = pass_real_deepseek_one_stage
treatment_distinct_ready = true
agent_host = hard_blocked_provider_protocol
comparison_status = prepared_condition_sensitive_eval_no_agenthost
compiler_superiority = not_evaluated
```

## Treatment integrity

`direct_to_skill_ir` now performs one real OpenAI-compatible model call from the same raw
expert and OSV materials directly to the target `skill_ir.v1` schema. It does not invoke
the Knowledge Compiler's extraction, evidence-binding, synthesis, or validation stages,
and it records `knowledge_ir_visible=false` and `heldout_gold_visible=false`.

The model response required one representation-only normalization: `source_node_ids` was
recomputed as the exact union of the direct node IDs actually referenced by the generated
Skill IR. This did not add instructions, evidence, modality, or domain content and is
recorded in the stage event.

The prepared treatments are now genuinely distinct:

| Artifact | Direct-to-Skill-IR | Compiler-distilled |
|---|---|---|
| Skill IR | `sha256:c513227062cc160d5b81806d6de578b12a5c7e13b3198fc750f7705a2e681dce` | `sha256:46fb52700610957ae3a77246009370676d8e3184e9627d35eab6aa3d3007dd91` |
| Agent artifact | `sha256:4a8c5580978f68ed14487933da9035e814c49d941af6b3ed1640370ba31d3b8d` | `sha256:b1e0d32349fe46049d4655d89c87e425d593bdf4a54bf4aee5efea83853cbbdb` |
| Build/Generation attestation | `sha256:51cfa5dff4f954e48e01c83452cf24cb221c17a95c94187ee2013ba8d15295e0` | `sha256:1c690cf1408010910b02302fd677dd783838fd83db34e4df86c517599e624aff` |

Prepared comparison artifact:

```text
sha256:9975ed5286570649941c444b2b72e7b5d3699dd7148cceffaba84aa16d7e1daa
```

It freezes seven hidden held-out cases, the same OSV snapshot, evaluator, task budget,
source visibility manifest, and `gold_hidden_from_agent=true`. The optional
`human_authored_reference_skill` remains `unavailable`; no held-out-informed reference was
invented.

## Why no effectiveness result is reported

The available Codex AgentHost has not qualified, so none of the four conditions
(`no_skill`, `full_material`, `direct_to_skill_ir`, `compiler_distilled_skill`) has been
executed through a mature treatment-sensitive AgentHost. ReferenceDecisionBackend results
would be condition-insensitive and are deliberately excluded.

Therefore the valid conclusion is only:

```text
compiler_superiority = prepared_condition_sensitive_eval_no_agenthost
```

Treatment distinction fixes the previous experiment-design defect; it does not itself
prove a Compiler benefit.
