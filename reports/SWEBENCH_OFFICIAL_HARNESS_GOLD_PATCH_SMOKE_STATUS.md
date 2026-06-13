# SWE-bench Official Harness Gold-Patch Smoke Status

Date: 2026-06-12
Run id: `swebench_gold_patch_smoke_requests_20260612`

## Boundary

- Official SWE-bench harness only
- One fixed SWE-bench Lite instance
- No custom evaluator
- No Harbor bridge
- No `skill_llm_patch` attempt without model env

## Fresh Commands

```powershell
skill-deploy external-swebench gold-smoke --run-id swebench_gold_patch_smoke_requests_20260612 --instance-id psf__requests-1963 --backend official_docker --attempt-mirrors
```

Official harness call path:

`/opt/spark/swebench-tools/swebench-venv/bin/python -m swebench.harness.run_evaluation`

## Dataset Instance Metadata

- `instance_id`: `psf__requests-1963`
- `repo`: `psf/requests`
- `base_commit`: `110048f9837f8441ea536804115e80b69f400277`
- `problem_statement_hash`: `ab31a283ce6fd03aff660d11dda4d5773faa92984ecdd44e97d65c1f8774098c`
- `gold_patch_hash`: `deb8b9018ea0271b2b9dc2d883bf5fb0ca9a721ecc9a93718065926fbec4ed74`
- `test_patch_hash`: `d54962cb131f871dcfb26c9d5b4518da0c701fd998915837bec0b3d80d9492a0`
- `dataset_source`: `https://huggingface.co/datasets/SWE-bench/SWE-bench_Lite`
- `official_dataset.json`: `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\external_swebench\swebench_gold_patch_smoke_requests_20260612\official_dataset.json`

## Docker / Image Status

- WSL distro: `Ubuntu-24.04-Codex`
- Docker available: `True`
- Registry mirrors: `[]`
- `ubuntu:22.04` ready: `True`
- `ubuntu:22.04` source: `existing_local_image`
- Docker status artifact: `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\external_swebench\swebench_gold_patch_smoke_requests_20260612\docker_status.json`

Docker pull attempts:

- No pull attempt was needed because `ubuntu:22.04` already existed locally.

Gold official command:

```text
'/opt/spark/swebench-tools/swebench-venv/bin/python' -m swebench.harness.run_evaluation --dataset_name '/mnt/c/Users/31552/Documents/New project/expert-skill-distillation-prototype-main/outputs/external_swebench/swebench_gold_patch_smoke_requests_20260612/official_dataset.json' --split test --instance_ids 'psf__requests-1963' --predictions_path '/mnt/c/Users/31552/Documents/New project/expert-skill-distillation-prototype-main/outputs/external_swebench/swebench_gold_patch_smoke_requests_20260612/predictions/gold_patch.jsonl' --max_workers 1 --timeout 1800 --run_id 'swebench_gold_patch_smoke_requests_20260612_gold_patch' --report_dir '/mnt/c/Users/31552/Documents/New project/expert-skill-distillation-prototype-main/outputs/external_swebench/swebench_gold_patch_smoke_requests_20260612/evaluation/gold_patch/official_reports' --namespace none
```

## Results

- `gold_patch`: `infra_failed` (`official_harness_infra_failed`)
- `empty_patch`: `empty_patch_skipped_by_official_harness` (`empty_patch_skipped_by_official_harness`)
- `skill_llm_patch`: `blocked_by_missing_model_env`

## Gold-Patch Detail

- Official report: `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\external_swebench\swebench_gold_patch_smoke_requests_20260612\gold_patch.swebench_gold_patch_smoke_requests_20260612_gold_patch.json`
- Result artifact: `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\external_swebench\swebench_gold_patch_smoke_requests_20260612\evaluation\gold_patch\results.json`
- Blocked reason: `Official harness environment-image build failed during conda package download from repo.anaconda.com: Content-Length mismatch after network timeout.`
- Run-instance log: `None`
- Build-image log: `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\external_swebench\swebench_gold_patch_smoke_requests_20260612\logs\build_images\env\sweb.env.py.x86_64.1f92e6d7cef88badc4f744__latest\build_image.log`

## Empty-Patch Detail

`empty_patch` is recorded as `empty_patch_skipped_by_official_harness` when the official harness skips empty predictions. This is a harness baseline behavior, not a model or Skill failure.

## Skill-LLM Patch Status

`skill_llm_patch` is `blocked_by_missing_model_env`. Reason: MODEL or OPENAI_MODEL is not configured for a non-oracle SWE-bench patch attempt.

## Claim

- `official_harness_gold_patch_smoke`: `infra_blocked`
- `software_patch_review` external effectiveness: `not_claimed`

## Remaining Gap

- Resolve the recorded infrastructure blocker, then rerun this exact one-instance gold-patch smoke.
