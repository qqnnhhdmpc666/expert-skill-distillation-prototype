# Expert Skill Distillation Prototype

This folder is the official workspace for the mentor-requested prototype task.

中文说明：本目录是“专家知识蒸馏原型系统”任务的正式交接与开发入口。之前位于 `C:\Users\老板\Desktop\new\expert_skill_distillation_prototype` 的内容只作为草稿参考，后续以 `D:\solution` 为准。

## Project Goal

Build a two-week demo prototype that distills expert knowledge into inspectable, correctable, reusable agent skill packages.

The prototype is inspired by:

- SPARK-PDI / Evidence Over Plans: Online Trajectory Verification for Skill Distillation
- COLLEAGUE.SKILL

The basic goal is to complete a runnable demo. If time allows, we will add an efficiency-aware extension such as compact invocation skills or cheaper verification.

## Folder Structure

```text
D:\solution
├── README.md
├── docs\
│   ├── HANDOFF.md
│   ├── ROLE_AND_TASKS.md
│   ├── TWO_WEEK_PLAN.md
│   ├── PAPER_READING_NOTES_TEMPLATE.md
│   ├── DATA_AND_PRIVACY_POLICY.md
│   ├── EXPERIMENT_LOG_TEMPLATE.md
│   └── DEMO_SCRIPT_TEMPLATE.md
├── src\
│   └── prototype code
├── data\
│   └── demo data only; avoid private or sensitive data
├── outputs\
│   └── generated skill packages and versions
├── reports\
│   └── paper notes, code audit, prototype reports
└── demo\
    └── demo script, screenshots, slides, assets
```

## Current Priority

1. Read and summarize SPARK-PDI.
2. Inspect COLLEAGUE.SKILL open-source code.
3. Decide whether SPARK-PDI can be reproduced directly or needs a simplified reproduction.
4. Choose a safe demo domain.
5. Implement basic expert-material-to-skill-package pipeline.
6. Add verification and feedback correction.
7. Add efficiency-aware extension if the basic demo is stable.

## Non-Goals

- Do not build a universal agent skill system in this two-week task.
- Do not use private expert data without permission.
- Do not overclaim automatic correctness.
- Do not force this prototype to become the next migration-system paper.

