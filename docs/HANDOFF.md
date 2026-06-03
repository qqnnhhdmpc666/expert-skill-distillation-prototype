# Project Handoff

## One-Sentence Task

Build a runnable prototype that distills expert materials or verified trajectories into inspectable, correctable, reusable agent skill packages for a project demo in about two weeks.

## Official Workspace

All work should be placed under:

```text
D:\solution
```

Previous draft documents under `C:\Users\老板\Desktop\new\expert_skill_distillation_prototype` are not the official workspace.

## Background

The mentor requested support for a project demo based on two recent skill-distillation directions:

1. **SPARK-PDI / Evidence Over Plans**
   - Focus: online trajectory verification for skill distillation.
   - Key idea: distill skills from evidence-backed execution trajectories rather than only from prior plans.
   - Status: needs reproduction or simplified reproduction.

2. **COLLEAGUE.SKILL**
   - Focus: distill expert/person/role materials into skill packages.
   - Status: has open-source code; inspect and reuse if practical.

## Current Role

The current role is prototype support:

- read the papers;
- audit available code;
- reproduce or approximate the SPARK-PDI mechanism;
- build a basic expert-knowledge distillation pipeline;
- add verification;
- add lightweight invocation optimization after the verified distillation loop works;
- prepare a demo.

## Minimum Deliverable

At demo time, we should show:

1. input expert materials;
2. generated skill package;
3. verification/checking process;
4. feedback correction or version update;
5. short report explaining limitations.

## Optional Add-On

If the basic prototype works, add lightweight invocation optimization:

- compact invocation package;
- full vs compact token comparison;
- cheap-first verifier cascade;
- correction round count;
- efficiency report.

## Relationship to Main Research

This task is related to skill migration but is not identical to the future main paper.

Potential research lessons:

- distilled expert skills may contain target-specific or harmful details;
- capability and behavior tracks may transfer differently;
- evidence verification can inspire verifier-guided repair;
- compact invocation may inspire runtime burden reduction.
