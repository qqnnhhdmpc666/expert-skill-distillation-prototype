# Audit Current State 2026-06-24

Scope: read-only audit of current repository state, except for creating this audit note. No core implementation files were modified.

Repository audited:

```text
C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main
```

## Executive Summary

The repo-level evaluation harness has real run-level ReleaseBundle pinning evidence, backed by an active binding and artifact registry entries. The initial audit found a per-task evidence packaging inconsistency: run-level files and task result rows said `real_release_bundle_pinned`, while each per-task `bundle_manifest.json` still reported `partial_local_manifest_only` even though it embedded a real `release_bundle.v1` manifest.

Follow-up fix status:

```text
before:
  run-level = real_release_bundle_pinned
  per-task = partial_local_manifest_only
  trajectory_provenance_bundle_fields = incomplete

after:
  run-level = real_release_bundle_pinned
  per-task = real_release_bundle_pinned
  trajectory_provenance_bundle_fields = complete
  current_head_run = regenerated
```

Current tests pass in the present working tree:

```text
python -m pytest -q
120 passed in 12.73s
```

But the working tree is dirty with 734 pre-audit status entries, almost entirely run outputs. The current HEAD differs from the commit recorded in the latest repo-level eval run provenance.

## 1. Repo-Level Eval Harness ReleaseBundle Pinning

Latest run output opened:

```text
outputs\repo_level_eval_runs\latest
```

Run-level files checked:

- `bundle_resolution.json`
- `run_manifest.json`
- `run_summary.json`
- `run_provenance.json`
- `task_results.jsonl`
- per-task `condition_manifest.json`
- per-task `bundle_manifest.json`
- per-task `trajectory_evidence\provenance.json`
- per-task `trajectory_evidence\bundle_manifest.json`

### Run-Level Evidence

`outputs\repo_level_eval_runs\latest\bundle_resolution.json` records:

```text
bundle_attachment_mode = real_release_bundle_pinned
resolution_source = active_binding
state_dir = .tmp\repo-level-eval-state
active_binding_generation = 1
bundle_digest = sha256:a38606f2d57160fe556467261c790e1d2b8e4dbac19ca1001d6f7ddc55817457
skill_digest = sha256:8a1738b57cee10f88b0827c515fe3cb02e7d2894a91a0258696812989b01f045
skill_artifact_digest = sha256:b1e0d32349fe46049d4655d89c87e425d593bdf4a54bf4aee5efea83853cbbdb
knowledge_projection_digest = sha256:0c1919fc0b30afe07c89310ef0e9c220d7f70b9cd3d0c70f1e6bf47722428e1a
knowledge_access_binding_digest = sha256:605312802a2ed4523dd493114fa53f690963ee1dc58a74aea4d6d8dd290022e9
```

`run_manifest.json` also records:

```text
bundle_attachment_mode = real_release_bundle_pinned
condition = C5_active_runtime
task_ids = dependency_use_triage_requests_demo,
           dependency_use_triage_declared_not_used,
           dependency_use_triage_version_not_affected
```

`run_summary.json` records:

```text
task_count = 3
pass_count = 3
fail_count = 0
bundle_attachment_mode = real_release_bundle_pinned
```

`task_results.jsonl` records `bundle_attachment_mode = real_release_bundle_pinned` for all three task rows.

### Active Binding and Artifact Registry Evidence

SQLite metadata check against `.tmp\repo-level-eval-state\metadata.sqlite` found:

```text
active_binding:
  binding_key = python-advisory
  bundle_digest = sha256:a38606f2d57160fe556467261c790e1d2b8e4dbac19ca1001d6f7ddc55817457
  generation = 1
  updated_at = 2026-06-23T16:14:20.924297+00:00
```

The artifact table contains:

```text
release_bundle.v1:
  digest = sha256:a38606f2d57160fe556467261c790e1d2b8e4dbac19ca1001d6f7ddc55817457
  artifact_id = release_bundle.v1:1d6f7ddc55817457
  size_bytes = 4623

skill_ir.v1:
  digest = sha256:8a1738b57cee10f88b0827c515fe3cb02e7d2894a91a0258696812989b01f045

knowledge_projection.v1:
  digest = sha256:0c1919fc0b30afe07c89310ef0e9c220d7f70b9cd3d0c70f1e6bf47722428e1a

agent_skill_artifact.v1:
  digest = sha256:b1e0d32349fe46049d4655d89c87e425d593bdf4a54bf4aee5efea83853cbbdb
```

Implementation read-only check:

- `src\expert_skill_system\runtime\release_bundle_resolver.py` calls `BundleBuilder(workspace).load(resolved_digest)`.
- On success it returns `bundle_attachment_mode = real_release_bundle_pinned` and pulls `skill_digest`, `skill_artifact_digest`, and `knowledge_projection_digest` from the loaded ReleaseBundle manifest.
- `src\expert_skill_system\runtime\bundle.py` verifies the ReleaseBundle closure in `BundleBuilder.load(...)`.

Conclusion: the run-level pinning is real, not merely a report statement.

### Per-Task Evidence Packaging Caveat

Per-task `condition_manifest.json` records:

```text
active_bundle_digest = sha256:a38606f2d57160fe556467261c790e1d2b8e4dbac19ca1001d6f7ddc55817457
```

Per-task `bundle_manifest.json` embeds the full `release_bundle.v1` manifest, including the same skill IR, knowledge projection, knowledge access binding, agent artifact, verifier binding, provider policy, and dependency manifest refs.

However, the top-level per-task `bundle_manifest.json` and `trajectory_evidence\bundle_manifest.json` record:

```text
bundle_attachment_mode = partial_local_manifest_only
```

This is inconsistent with the run-level resolver and task rows. The likely cause is visible in the code path:

- `repo_eval_harness.py` passes the full `bundle_resolution` to `run_dependency_use_triage(...)`.
- `repo_security_task.py` passes only `bundle_resolution["bundle_manifest"]` into `build_injection_manifests(...)`.
- `skill_knowledge_injection.py` computes `bundle_attachment_mode` from the object it receives; the inner ReleaseBundle manifest does not itself contain `bundle_attachment_mode`, so it falls back to `partial_local_manifest_only`.

Trajectory provenance files currently include:

```text
task_digest
prediction_digest
verifier_result_digest
condition_manifest_digest
```

They do not directly include `bundle_digest`, `skill_digest`, or `knowledge_projection_digest`. Those are available through the condition manifest and embedded bundle manifest, but not first-class in `trajectory_evidence\provenance.json`.

Audit conclusion:

```text
real_bundle_pinning = true at resolver/run/task-result level
per_task_evidence_packaging = inconsistent
trajectory_provenance_bundle_fields = incomplete
claim_strength = implemented with evidence-packaging caveat
```

### Bundle Evidence Consistency Fix

The propagation bug was fixed by passing the complete bundle resolution envelope into injection and trajectory evidence code, instead of passing only the inner ReleaseBundle manifest.

New current-head run:

```text
python scripts\run_repo_level_eval.py --task-registry data\repo_security_tasks\registry.json --output outputs\repo_level_eval_runs\current_head --state-dir .tmp\repo-level-eval-state --use-active-binding
```

Observed result:

```text
task_count = 3
pass_count = 3
fail_count = 0
bundle_attachment_mode = real_release_bundle_pinned
bundle_digest = sha256:a38606f2d57160fe556467261c790e1d2b8e4dbac19ca1001d6f7ddc55817457
skill_digest = sha256:8a1738b57cee10f88b0827c515fe3cb02e7d2894a91a0258696812989b01f045
skill_artifact_digest = sha256:b1e0d32349fe46049d4655d89c87e425d593bdf4a54bf4aee5efea83853cbbdb
knowledge_projection_digest = sha256:0c1919fc0b30afe07c89310ef0e9c220d7f70b9cd3d0c70f1e6bf47722428e1a
knowledge_access_binding_digest = sha256:605312802a2ed4523dd493114fa53f690963ee1dc58a74aea4d6d8dd290022e9
```

Consistency check against `outputs\repo_level_eval_runs\current_head`:

```text
bundle_resolution.json = real_release_bundle_pinned
run_manifest.json = real_release_bundle_pinned
run_summary.json = real_release_bundle_pinned
run_provenance.json = real_release_bundle_pinned
aggregate_report.json = real_release_bundle_pinned
task_results.jsonl = real_release_bundle_pinned for all 3 tasks
tasks/<task_id>/bundle_manifest.json = real_release_bundle_pinned for all 3 tasks
tasks/<task_id>/condition_manifest.json = real_release_bundle_pinned for all 3 tasks
tasks/<task_id>/trajectory_evidence/bundle_manifest.json = real_release_bundle_pinned for all 3 tasks
tasks/<task_id>/trajectory_evidence/provenance.json = real_release_bundle_pinned for all 3 tasks
```

`trajectory_evidence\provenance.json` now directly includes:

```text
bundle_attachment_mode
bundle_digest
skill_digest
skill_artifact_digest
knowledge_projection_digest
knowledge_access_binding_digest
task_digest
prediction_digest
verifier_result_digest
condition_manifest_digest
```

The new `run_provenance.json` records:

```text
git_commit = e36eddb32a11c28c2db5782314e4b26c92ac0ad9
```

Updated conclusion:

```text
real_bundle_pinning = pass
per_task_evidence_packaging = pass
trajectory_provenance_bundle_fields = pass
current_head_run_reproduction = pass
repo_level_specific_bundle = not_yet
public_repo_snapshot = not_yet
compiler_superiority = not_evaluated
vulnerability_discovery_claim = not_claimed
```

## 2. Test Result, Commit, and Python Environment

Current HEAD:

```text
e36eddb32a11c28c2db5782314e4b26c92ac0ad9
2026-06-24 00:19:12 +0800
Add repo-level evaluation harness
```

Recent history:

```text
e36eddb Add repo-level evaluation harness
4a259cb Harden repo security vertical slice evidence
2c421f6 Add repo-level security vertical slice
1396617 Consolidate V1 public docs and Harbor subset parity
c0bbbe6 Validate public OSV agent evidence gates
```

Important provenance mismatch:

```text
outputs\repo_level_eval_runs\latest\run_provenance.json
git_commit = 4a259cb4997d60b3347e8a5a846c81714e3a0679
```

That commit is:

```text
4a259cb4997d60b3347e8a5a846c81714e3a0679
2026-06-24 00:01:13 +0800
Harden repo security vertical slice evidence
```

Therefore, the latest checked run output was generated at the previous commit, while the currently checked test result was run at current HEAD plus dirty working tree.

Python environment:

```text
python --version
Python 3.13.13

where.exe python
C:\Users\31552\AppData\Local\Programs\Python\Python313\python.exe
C:\msys64\ucrt64\bin\python.exe
C:\Users\31552\AppData\Local\Microsoft\WindowsApps\python.exe

sys.executable
C:\Users\31552\AppData\Local\Programs\Python\Python313\python.exe

platform
Windows-11-10.0.26200-SP0
```

Commands run during audit:

```text
$env:PYTHONDONTWRITEBYTECODE='1'; python -m pytest -q -p no:cacheprovider
118 passed in 7.51s

python -m pytest -q
118 passed in 7.05s
```

Commands run after Bundle Evidence Consistency Fix:

```text
python scripts\run_repo_level_eval.py --task-registry data\repo_security_tasks\registry.json --output outputs\repo_level_eval_runs\current_head --state-dir .tmp\repo-level-eval-state --use-active-binding
pass, 3/3 tasks

python -m pytest tests\v1 -q
66 passed in 13.78s

python -m pytest -q
120 passed in 12.73s

python -m ruff check src\expert_skill_system tests\v1 scripts
failed, 296 legacy lint errors

python -m ruff check <new-or-touched files>
All checks passed
```

Interpretation:

```text
test_status = pass
test_commit = current HEAD e36eddb + dirty working tree
clean_commit_claim = not available because worktree has 734 pre-audit status entries
```

## 3. Git Status Governance

Pre-audit status count:

```text
TOTAL = 734
```

Status code counts:

```text
deleted = 408
modified = 88
untracked = 238
```

Category counts:

| Category | Count | Status mix |
|---|---:|---|
| source code | 0 | none |
| tests | 0 | none |
| docs/reports | 2 | 2 modified |
| fixtures | 0 | none |
| run outputs | 731 | 408 deleted, 86 modified, 237 untracked |
| temporary artifacts | 1 | 1 untracked |

Post-fix working tree note:

```text
The 734 count above is the original read-only audit snapshot. After the narrow bundle-evidence fix, regression tests, report updates, and regenerated current_head run, the working tree has 745 status entries:
source code = 6
tests = 3
docs/reports = 5
fixtures = 0
run outputs = 729
temporary artifacts = 2
other = 0
```

Subtree concentration:

| Path group | Count | Status mix |
|---|---:|---|
| `outputs/teaching_utility_v02` | 695 | 408 deleted, 77 modified, 210 untracked |
| `outputs/installed_skills` | 12 | 4 modified, 8 untracked |
| `outputs/open_world_closed_loop` | 9 | 4 modified, 5 untracked |
| `outputs/open_world_distillation_validation` | 4 | 4 untracked |
| `outputs/evolution_repeatability` | 2 | 2 untracked |
| `outputs/public_osv_pilot` | 2 | 2 untracked |
| `reports` | 2 | 2 modified |
| `.tmp` | 1 | 1 untracked |
| `outputs/harbor_public_osv_subset` | 1 | 1 untracked |
| `outputs/repo_level_eval_runs` | 1 | 1 untracked |
| `outputs/repo_security_vertical_slice` | 1 | 1 untracked |
| `outputs/repo_security_vertical_slice_followup` | 1 | 1 untracked |
| `outputs/runtime_runs` | 1 | 1 untracked |
| `outputs/test_tmp` | 1 | 1 untracked |
| `review_package` | 1 | 1 modified |

Tracked report/review-package changes:

```text
reports/REVIEW_PACKAGE_INTEGRITY_STATUS.md
reports/review_package_integrity_status.json
review_package/MANIFEST.json
```

Diff stat for those three:

```text
3 files changed, 9 insertions(+), 9 deletions(-)
```

Visible untracked latest evidence dirs include:

```text
outputs\repo_level_eval_runs\
outputs\repo_security_vertical_slice\
outputs\repo_security_vertical_slice_followup\
outputs\public_osv_pilot\reference_runtime_results_v2.json
outputs\harbor_public_osv_subset\public-osv-subset-20260623\
```

### Governance Recommendations

Do not bulk-delete anything yet. First split outputs into evidence classes:

1. Curated evidence to retain in repo or review package:
   - `outputs/repo_level_eval_runs/current_head`
   - `outputs/repo_security_vertical_slice_followup`
   - `outputs/public_osv_pilot/reference_runtime_results_v2.json`
   - `outputs/harbor_public_osv_subset/public-osv-subset-20260623`
   - small aggregate reports and manifests with digests.

2. Heavy raw traces to keep out of normal git history unless explicitly needed:
   - most of `outputs/teaching_utility_v02`
   - repeated agent raw step logs
   - model call traces
   - transient stdout/stderr directories.

3. Temporary local state to ignore or archive outside source control:
   - `.tmp/`
   - `outputs/test_tmp/`
   - ad hoc runtime scratch outputs.

4. Deleted tracked outputs need a deliberate decision:
   - If old tracked teaching traces are obsolete, remove them in a dedicated cleanup commit with a replacement summary manifest.
   - If they remain part of evidence, restore or archive them before cleanup.

Recommended cleanup sequence:

1. Create a manifest-first evidence policy: commit small `summary.json`, `aggregate_report.*`, `run_manifest.json`, `bundle_resolution.json`, and digest manifests; keep large raw traces external or zipped in `review_package`.
2. Make one dedicated "curate latest evidence" commit for reports/manifests.
3. Make one separate "prune obsolete generated outputs" commit only after confirming old teaching traces are no longer needed.
4. Add or tighten `.gitignore` rules for `.tmp/`, `outputs/test_tmp/`, and raw repeated run traces.
5. Keep source/test changes separate from generated-output commits.

## 4. Next Priorities by Blocker Type

### System Maturity Blocker

Main issue: repo-level harness evidence packaging is now consistent, but the system still lacks clean evidence governance, a repo-level-specific ReleaseBundle, and full-repo lint hygiene.

Priority actions:

1. Build and pin a repo-level-specific ReleaseBundle instead of reusing the `python-advisory` bundle.
2. Resolve full-repo ruff failures in legacy scripts separately from harness work.
3. Stabilize artifact governance so a clean checkout can reproduce the same audit without 700+ output diffs.

### Public Repo / Generalization Blocker

Main issue: current repo-level dependency-use triage tasks are `local_public_like_demo`, not true public repo benchmark instances.

Priority actions:

1. Replace or supplement local fixtures with a small true public repo snapshot.
2. Record source URL, license, commit digest, file digests, and immutable snapshot manifest.
3. Add human/third-party authored hidden gold for dependency-use triage.
4. Expand from 3 local fixtures to a small representative matrix: used+affected, declared-not-used, used-not-affected, version-unknown, advisory-missing, package-absent.
5. Keep OSV applicability separate from exploitability/reachability.

### AgentHost / Effectiveness Blocker

Main issue: no mature treatment-sensitive AgentHost has executed the frozen compiler-vs-direct conditions.

Current known blocker:

```text
Codex 0.137 requires Responses-compatible provider.
Current DeepSeek route is Chat Completions-compatible.
OpenHands is not installed locally.
```

Priority actions:

1. Provide a valid Responses-compatible provider credential for Codex, or install and qualify OpenHands/SWE-agent with the current provider.
2. Run a bounded AgentHost qualification task that consumes Bundle-derived material and emits schema-valid output.
3. Only after qualification, run the four frozen conditions:
   - no_skill
   - full_material
   - direct_to_skill_ir
   - compiler_distilled_skill
4. Do not count reference deterministic backend outputs as AgentHost effectiveness.
5. Avoid a local protocol proxy unless it is independently specified and qualified as infrastructure.

### Paper Claim Blocker

Main issue: the strongest defensible claim is system/lifecycle maturity, not compiler superiority or production security effectiveness.

Allowed claim shape:

```text
The project implements an evidence-grounded Skill lifecycle runtime with real ReleaseBundle pinning, repo-level deterministic evaluation harnesses, bounded public OSV/Harbor verifier parity, and conservative evolution gates.
```

Blocked claims:

```text
compiler superiority over direct generation = not evaluated
mature AgentHost effectiveness = not evaluated
official external benchmark performance = not demonstrated
production vulnerability scanner readiness = not claimed
stable autonomous open-world evolution = not proven
OSV applicability as exploitability/reachability = not claimed
```

Paper priority actions:

1. Make a claim table that maps every claim to an artifact path and evidence type.
2. Treat repo-level harness as a reproducibility contribution, not effectiveness evidence.
3. Present the per-task bundle-mode inconsistency as a fixed audit item before submission.
4. Use Harbor/OSV results only as verifier parity and deterministic runtime evidence.
5. Delay any "compiler beats direct" claim until AgentHost execution exists.

## 5. Completion Audit for Bundle Evidence Goal

Acceptance check against `outputs\repo_level_eval_runs\current_head`:

```text
run_level_and_per_task_bundle_mode_agree = pass
per_task_bundle_manifest_real_release_bundle_pinned = pass
per_task_trajectory_bundle_manifest_real_release_bundle_pinned = pass
trajectory_provenance_direct_bundle_fields = pass
task_results_aggregate_and_per_task_evidence_agree = pass
current_head_run_output_generated = pass
run_provenance_git_commit = e36eddb32a11c28c2db5782314e4b26c92ac0ad9
regression_tests_cover_real_and_partial_modes = pass
status_report_conservative = pass
no_public_benchmark_agenthost_compiler_or_vulnerability_claim_added = pass
```

Final validation commands rerun during completion audit:

```text
python -m pytest tests\v1 -q
66 passed in 8.14s

python -m pytest -q
120 passed in 9.20s

python -m ruff check <new-or-touched files>
All checks passed

python -m ruff check src\expert_skill_system tests\v1 scripts
failed, 296 existing lint errors
```

## Bottom Line

The harness has genuinely loaded a real ReleaseBundle, passed three deterministic repo-level tasks, and now records the same bundle evidence from run-level files down to per-task trajectory provenance. The current repository also passes 120 tests under Python 3.13.13. Remaining risks are evidence governance, legacy full-ruff failures, use of the `python-advisory` bundle rather than a repo-level-specific bundle, and local-fixture-only task scope.
