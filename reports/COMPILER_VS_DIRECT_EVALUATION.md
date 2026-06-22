# Compiler vs Direct-to-Skill-IR Evaluation

Date: 2026-06-23

```text
public_protocol = prepared
condition_sensitive_execution = not_run
condition_content_identical = true
agent_host = hard_blocked
compiler_superiority = not_demonstrated
```

Fresh command:

```powershell
eskill --state-dir .tmp/public-comparison-state prepare-public-comparison `
  --data-dir data/public_osv_pilot
```

The protocol freezes seven public held-out cases, the hidden evaluator gold digest, one
OSV snapshot, one task budget, and five diagnostic conditions. No evaluator-only field is
present in Agent-visible inputs. Artifact:

```text
sha256:d17b1deec32220963b91de1d51324c1ec1a249394ce54a749e8013c2370dcd39
```

## Integrity finding

The current deterministic `direct_to_skill_ir` and `compiler_distilled_skill` paths produce
the same Skill IR digest and the same Agent artifact digest. Therefore the current direct
baseline is not treatment-distinct and cannot support a Compiler benefit claim. This is an
implementation gap, not a positive result.

The comparison has two independent blockers:

1. `DIRECT_AND_COMPILER_AGENT_ARTIFACTS_IDENTICAL`
2. `QUALIFIED_AGENTHOST_UNAVAILABLE`

`human_authored_reference_skill` is explicitly unavailable and is not represented as human
gold. Prepared artifacts are not evidence of open-world extraction, AgentHost effectiveness,
or Compiler superiority.
