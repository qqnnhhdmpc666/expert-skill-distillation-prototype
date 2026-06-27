# Legacy Prototype Notes

This file describes the earlier controlled `skill_deployment` lane. It is retained for traceability, but it is not the current V1 main path.

Current V1 main path:

```text
Expert Skill Distillation System
= Knowledge Compiler
+ Skill Runtime
+ Pluggable Knowledge Provider
+ External Verification
+ Safe Evolution
```

Use these current entry points instead:

- `README.md`
- `docs/QUICKSTART.md`
- `docs/CLAIM_BOUNDARY.md`
- `docs/design_v03/SYSTEM_ARCHITECTURE_FREEZE_V1.md`
- `reports/PUBLIC_VALIDATION_AND_AGENT_USABILITY_STATUS.md`

The old `skill-deploy` CLI, `secure_code_review` installed Skill package, and local defensive mini-suite are earlier prototype evidence. They can be useful as legacy baselines, but they should not be described as the active V1 architecture.

Current status summary:

- Core local system: `pass`
- Independent DeepSeek Judge: `pass`
- Harbor public OSV parity: `public_task_parity_subset_pass`
- AgentHost: `hard_blocked_no_compatible_mature_host`
- Compiler-vs-Direct: `prepared_condition_sensitive_eval_no_agenthost`
- Compiler superiority: not evaluated

Do not use this legacy lane to claim production vulnerability scanning, official benchmark success, mature AgentHost execution, or broad autonomous Skill evolution.
