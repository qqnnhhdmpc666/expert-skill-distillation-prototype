# Two-Week Plan

## Day 1-2: Paper and Code Intake

Tasks:

- read SPARK-PDI enough to understand the reproducible pipeline;
- inspect whether SPARK-PDI has code;
- inspect COLLEAGUE.SKILL repository;
- decide if COLLEAGUE.SKILL code is reusable or only conceptually useful.

Outputs:

- `D:\solution\reports\SPARK_PDI_REPRO_NOTES.md`
- `D:\solution\reports\COLLEAGUE_SKILL_CODE_AUDIT.md`

## Day 3-4: Demo Scenario and Data

Choose one safe domain:

- API / code-review expert skill.

Tasks:

- prepare small demo corpus;
- verify no sensitive data;
- define skill package schema;
- define MVP closed loop and comparison variants.

Outputs:

- `D:\solution\docs\MVP_DESIGN.md`
- `D:\solution\data\README_DATA.md`
- `D:\solution\docs\SKILL_PACKAGE_SCHEMA.md`

## Day 5-7: Basic Distillation Pipeline

Tasks:

- document ingestion;
- evidence chunking;
- capability extraction;
- behavior extraction;
- skill package generation;
- structural validation.

Outputs:

- runnable prototype under `D:\solution\src`
- `D:\solution\outputs\example_skill_package_v1.json`

## Day 8-9: Verification and Correction

Tasks:

- checklist verifier;
- evidence coverage verifier;
- contradiction / unsupported claim check;
- execution-feedback patch;
- version update.

Outputs:

- `D:\solution\outputs\example_skill_package_v2.json`
- `D:\solution\reports\VERIFICATION_REPORT.md`

## Day 10-11: 执行优化与成本对比

Recommended optimization:

- no skill vs full skill vs compact skill v1 vs compact skill v2.

Metrics:

- token count;
- call count;
- retry count;
- verifier calls;
- checklist pass retention;
- correction rounds.

Output:

- `D:\solution\reports\EFFICIENCY_REPORT.md`

## Day 12-13: Demo Assembly

Tasks:

- prepare demo script;
- prepare input/output examples;
- prepare screenshots;
- prepare prototype report.

Outputs:

- `D:\solution\demo\DEMO_SCRIPT.md`
- `D:\solution\reports\PROTOTYPE_REPORT.md`

## Day 14: Buffer and Polish

Tasks:

- fix environment;
- clean docs;
- remove sensitive data;
- test demo end-to-end.
