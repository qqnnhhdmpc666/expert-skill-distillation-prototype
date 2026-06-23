# Harbor External Evaluation Status

Date: 2026-06-23

```text
harbor_plumbing = pass
public_task_adapter = pass_pair_smoke
native_vs_harbor_parity = pass_2_of_2
external_evaluation_backend = public_task_parity_partial
external_evaluation_pass = true_for_declared_pair_only
agent_effectiveness = not_evaluated
```

## Fresh command

```powershell
wsl.exe -d Ubuntu-24.04-Codex -- `
  /opt/spark/harbor-src-locked/.venv/bin/harbor run `
  --path '/mnt/c/Users/31552/Documents/New project/expert-skill-distillation-prototype-main/data/harbor_tasks/public_osv_pair' `
  --agent oracle --env docker --n-concurrent 1 `
  --jobs-dir '/mnt/c/Users/31552/Documents/New project/expert-skill-distillation-prototype-main/outputs/harbor_public_osv_pair' `
  --job-name public-osv-pair-20260623 --force-build `
  --export-traces --export-verifier-metadata
```

Environment:

```text
WSL = Ubuntu-24.04-Codex
Harbor = 0.1.45
Docker client/server = 29.1.3
Docker API = 1.52
OS/arch = linux/amd64
base image = ubuntu:24.04 (image id 92f09d8fdb8c)
```

## Pair-level result

The same frozen public OSV record, `PYSEC-2018-28`, was evaluated in the native reference
runtime and as two Harbor Docker tasks.

| Case | Native verdict / reason | Harbor reward | Harbor verifier | Task checksum |
|---|---|---:|---|---|
| `PYSEC-2018-28__affected` | `advisory_applicable / VERSION_IN_RANGE` | 1.0 | pass | `9a3022dfa183f1408cbae18b4a83277f10a27e66a77cc9ab17bead3d845c8c39` |
| `PYSEC-2018-28__fixed_boundary` | `advisory_not_applicable / VERSION_OUT_OF_RANGE` | 1.0 | pass | `46022e73e438eb1ca6da8709c12ee84abb93f38464ca312c6583ef3c3b2b8588` |

Harbor summary: 2 trials, 0 errors, mean reward 1.0. The native v2 evaluator also passed
both rows and the complete 33-case pilot with false-safe count 0.

## Raw evidence

- Harbor job result:
  `outputs/harbor_public_osv_pair/public-osv-pair-20260623/result.json`
  (`sha256:61297f1d4bcf212550446e2b195c293aa855fabcc4b1679d9d177543875b6e42`)
- affected verifier result/reward/stdout:
  `outputs/harbor_public_osv_pair/public-osv-pair-20260623/pysec-2018-28-affected__wDqHKCH/verifier/`
- fixed verifier result/reward/stdout:
  `outputs/harbor_public_osv_pair/public-osv-pair-20260623/pysec-2018-28-fixed__YYRnURf/verifier/`
- native results:
  `outputs/public_osv_pilot/reference_runtime_results_v2.json`
  (`sha256:5a7bb17c91e732003e89c2efc3a9830ab40b6e91326a1d6499467cf6432823bd`)

Both verifier result files are real Harbor artifacts and bind to frozen source record digest
`sha256:9e797ddf6daa453869b8d270676615145579f3bf5115e67dc5e69052974e034b`.

## Boundary

This proves native/Harbor verifier parity for two public dependency-advisory boundary
tasks. The oracle adapter does not emit Harbor ATIF trajectories, so trace export reported
an explicit unsupported-format warning. This does not invalidate verifier parity, but it
means the run does not prove trajectory capture or non-oracle Agent usefulness. Broader
dataset parity and AgentHost execution remain separate gates.
