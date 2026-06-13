# Reviewer Guide

## Start Here

Open:

```text
review_package/index.html
```

Then inspect:

```text
outputs/system_acceptance_001/summary.md
outputs/validation/generalization_suite.md
outputs/validation/ablation_summary.md
outputs/wsl_harbor_real_upload_001/summary.md
reports/MORNING_STATUS_0800.md
```

## What To Look For

1. Does the same pipeline run multiple task families?
2. Do different tasks produce different feedback?
3. Does feedback drive typed repair?
4. Does gate prevent regressions?
5. Are outputs backed by artifacts rather than page-only explanations?

## What Not To Assume

Do not interpret this as a universal vulnerability scanner or a full SPARK-PDI reproduction. The evidence is controlled prototype evidence.
