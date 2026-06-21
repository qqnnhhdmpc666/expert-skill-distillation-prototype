# Public OSV Benchmark Plan and Pilot Status

Date: 2026-06-22

## Purpose

Replace the six handcrafted dev cases as the main evaluation substrate with a public, frozen and deterministic dependency-advisory pair benchmark. This track evaluates version/applicability decisions and later provides held-out tasks for comparing `direct_to_skill_ir` with `compiler_distilled_skill`.

It does not evaluate exploitability, reachability, runtime call paths or broad vulnerability discovery.

## Public sources

- OSV public API: `https://api.osv.dev/v1/vulns/<id>`
- OSV public schema: `https://raw.githubusercontent.com/ossf/osv-schema/main/validation/schema.json`
- Frozen source manifest: `data/public_osv_pilot/SOURCE_MANIFEST.json`
- Frozen records: `data/public_osv_pilot/records/`
- Frozen schema: `data/public_osv_pilot/schema/osv-schema.json`

The pilot fixes ten public advisory IDs before evaluation. Every raw HTTP response and the schema are persisted byte-for-byte with SHA-256. A fresh integrity check verified all 11 frozen files against the manifest.

## Deterministic construction

Generator: `public_osv_pair_generator.v1`

For each fixed record:

1. select the first PyPI affected entry with an `ECOSYSTEM` range;
2. select the latest valid listed affected version;
3. create one affected-version case;
4. create one first-fixed-boundary negative case;
5. add a package-absent negative control;
6. assign split using `sha256(case_id) mod 10`.

The agent/runtime-visible file is `inputs.jsonl`. Expected verdict and reason exist only in `gold.jsonl`. This separation prevents a tested Runtime or future candidate generator from reading evaluator-only fields.

Artifacts:

```text
data/public_osv_pilot/inputs.jsonl
data/public_osv_pilot/gold.jsonl
data/public_osv_pilot/split_manifest.json
data/public_osv_pilot/osv_snapshot.json
```

Frozen digests:

```text
input manifest: sha256:f0659c89cbabe287fa5111f07fdede2900813031aa774096ceecb3f1d3a6b47c
gold manifest:  sha256:c778fa27db1775c36a7249e539c6e69dd1ffe288788a919f885db0179d687bf7
schema:         sha256:7a511902b57297197b37298f6adaa2acb15f22b3f641bb9f547f19dcbe533ba8
```

## Pilot result

Fresh commands:

```powershell
python scripts\build_public_osv_pilot.py --output data\public_osv_pilot
python scripts\run_public_osv_pilot.py `
  --data-dir data\public_osv_pilot `
  --state-dir .tmp\public-osv-pilot-state `
  --output outputs\public_osv_pilot\reference_runtime_results.json
```

Observed:

```text
public records: 10
generated cases: 21
build/dev/heldout: 11 / 6 / 4
generator exclusions: 0
reference runtime completed: 21
verdict+reason pass: 21
false-safe: 0
missing prediction: 0
```

Fresh result:

```text
outputs/public_osv_pilot/reference_runtime_results.json
bundle: sha256:aa152778192b534391d1dc1a094c8e5b75b8aebccbff50c0eb83eed5b17a9e8f
evaluator: public_osv_pair_evaluator.v1
```

This is public-data evidence for snapshot ingestion, typed query, ReleaseBundle wiring and deterministic reference decision semantics. It is not compiler superiority: the reference backend is not condition-sensitive and no qualified AgentHost compared the five compiler conditions.

## Evaluator contract

The evaluator reports exact verdict/reason match, false-safe count, missing predictions and per-case rows. `runtime_failure`, missing prediction and unjustified `unresolved` cannot count as a correct negative.

OSV-Scanner is currently not installed in Windows or the discovered WSL distribution. When added, it will be a cross-check only. Disagreements must be classified as dependency discovery, normalization, data snapshot, range semantics or policy differences; scanner output will not replace frozen public gold.

## Scale plan

### Pilot gate: complete

- fixed public source records and schema;
- raw-byte provenance verified;
- deterministic generator and evaluator tested;
- public input separated from gold;
- fresh reference runtime run complete.

### Scale 1: 100-300 records

- pre-register package/advisory selection before fetching outcomes;
- include multiple packages and multiple range forms;
- retain all exclusions with machine-readable reasons;
- add malformed/unknown version and marker cases without changing held-out after inspection;
- publish source license and redistribution audit.

### Scale 2: condition-sensitive compiler comparison

Run the frozen five conditions through one qualified AgentHost under the same Bundle primitives, knowledge snapshot, permissions, task budget and evaluator:

```text
no_skill
full_material
direct_to_skill_ir
compiler_distilled_skill
human_authored_reference_skill (only if independently available)
```

Select models/prompts on build/dev only. Evaluate held-out once after manifest freeze. Report helpful/neutral/harmful, false-safe, abstention, cost and latency. Until this stage completes, `compiler_superiority = not_demonstrated`.

### Scale 3: external harness packaging

Package a subset as native deterministic tasks, then establish native-vs-Harbor parity. Harbor container execution alone is plumbing evidence, not benchmark validity.

## Claim status

```text
public_data_pipeline = pass_pilot
public_reference_runtime = pass_pilot
public_agenthost_effectiveness = not_tested
direct_vs_compiler_public_heldout = not_tested
compiler_superiority = not_demonstrated
osv_scanner_cross_check = blocked_not_installed
```

