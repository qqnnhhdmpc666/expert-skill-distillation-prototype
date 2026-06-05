# Claim Boundary

This file defines safe wording for demos, reports, and discussions.

## Current Safe Positioning

Use one of these:

```text
risk-budgeted traceable skill deployment prototype
```

or:

```text
correctness-constrained expert skill deployment optimization
```

Avoid presenting the work as a mature universal compiler, benchmark, or replacement for SPARK.

## Relationship To SPARK-PDI And COLLEAGUE.SKILL

Safe wording:

```text
We build on COLLEAGUE.SKILL's inspectable skill artifact idea and SPARK-PDI's execution-evidence orientation. Our scoped exploration is correctness-constrained deployment in a controlled API-review family: budgeted compact skill generation, verifier-driven patching, validation gates, rule-application trace, and risk-budgeted selective trace.
```

Do not say:

```text
We comprehensively outperform SPARK-PDI or COLLEAGUE.SKILL.
```

Do not say:

```text
Every module in the prototype is original.
```

Do not say:

```text
The current prototype is already a mature open-source skill platform.
```

Repository maturity wording:

```text
The current repository is a reproducible, artifact-rich demo prototype. It has meaningful implementation depth, but compared with SPARK-PDI and COLLEAGUE.SKILL it is still weaker in package structure, formal tests, schema enforcement, dependency management, CI, and stable CLI/API design.
```

## What We Can Say

We can say:

- The prototype runs an end-to-end controlled API-review vertical loop.
- Expert materials are converted into full skill, evidence map, rule ledger, and compact skill artifacts.
- Compact skill content affects mock agent and RightCode `gpt-5.5` outputs in the controlled matrix.
- Harbor/verifier feedback can be converted into execution reports and rule-level patch proposals.
- `missing_rule` failures can patch domain rules such as R005/R006 into compact v2.
- `output_format_error` failures can patch output-contract constraints instead of domain rules.
- Validation gate can reject patches that introduce regression or exceed budget.
- Compressed compact wording can preserve executable semantics in the current toy audit.
- Trace verifier can distinguish rule-id shortcut from rule-application evidence in the toy protocol slice.
- Controlled holdout evidence shows patched compact improves coverage over compact_v1:

```text
compact_v1 avg coverage: 0.58
patched_compact avg coverage: 1.00
```

- Selective trace reduces overhead while preserving traceability for failure-critical rules in the toy slice:

```text
full_trace: 300 / 237, rejected
selective_trace R005/R006: 183 / 237, accepted and blocks shortcut
```

## What We Cannot Say

Do not say:

- We have proven general correctness.
- We have proven superiority over related work.
- The 4-case holdout is a benchmark.
- This is a mature skill compiler.
- This is a general self-evolving skill framework.
- `rule_ledger` alone is a strong new method.
- The trace protocol applies to all agents or tasks.
- RightCode GPT small-sample results prove model stability.
- Cost optimization is fully solved.
- We comprehensively beat SPARK-PDI or COLLEAGUE.SKILL.
- Every component is original.
- This is already a mature open-source platform.
- The current repository has the same engineering maturity as SPARK-PDI or COLLEAGUE.SKILL.

## Safe Main Claim

Use:

```text
The prototype demonstrates a risk-budgeted traceable skill deployment loop in a controlled API-review family: expert materials become evidence-grounded skills, verifier feedback drives patch proposals, validation gates prevent regression or over-budget deployment, and selective trace focuses rule-application evidence on high-risk rules.
```

## Unsafe Wording

Avoid:

```text
We propose a general expert skill compiler.
```

Avoid:

```text
Our method outperforms SPARK or COLLEAGUE.SKILL.
```

Avoid:

```text
The holdout set proves real-world generalization.
```

## Current Research Opening

The most promising research question is not whether we can log more fields. It is:

```text
Given material evidence, execution feedback, risk, and budget, how should a system decide which rules to keep, patch, compress, trace, accept, reject, or roll back?
```

## Baseline Attribution Boundary

Use component baselines to explain contribution sources:

- `direct_summary_skill`: tests whether structured rules help beyond direct summarization.
- `full_skill_no_compiler`: tests full-context upper-bound behavior and cost.
- `compact_no_feedback`: tests compacting without execution feedback.
- `patched_no_gate`: tests the value of validation gate.
- `patched_no_trace`: tests behavior without trace observability.
- `patched_selective_trace`: tests risk-budgeted trace allocation.

Do not call this a benchmark unless it is expanded into a larger, independently specified evaluation set.
