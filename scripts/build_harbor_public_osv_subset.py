from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path
from typing import Any

PREFERRED_KINDS = (
    "affected",
    "fixed_boundary",
    "package_absent_1_control",
    "advisory_missing_1_control",
    "marker_false_1_control",
    "version_unknown_1_control",
)


TASK_TOML = """version = "1.0"

[metadata]
author_name = "Expert Skill System"
author_email = "research@example.invalid"
difficulty = "easy"
category = "public-osv-parity-subset"
tags = ["osv", "python", "deterministic-verifier", "public-data", "subset"]

[verifier]
timeout_sec = 30.0

[agent]
timeout_sec = 30.0

[environment]
build_timeout_sec = 120.0
cpus = 1
memory = "1G"
storage = "2G"
"""


DOCKERFILE = """FROM ubuntu:24.04
WORKDIR /app
COPY case.json /app/case.json
"""


INSTRUCTION = """Read `/app/case.json` and write `/app/prediction.json` with exactly these fields:
`case_id`, `verdict`, and `reason_codes`. Determine whether the pinned package version is
covered by the frozen public OSV advisory data encoded in the task. Do not use the network.
"""


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def _write_lf(path: Path, text: str) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def _select_cases(inputs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    used: set[str] = set()
    for kind in PREFERRED_KINDS:
        for row in inputs:
            if row["case_kind"] == kind and row["case_id"] not in used:
                selected.append(row)
                used.add(row["case_id"])
                break
    return selected


def _expected_from_gold(case_id: str, gold_by_case: dict[str, dict[str, Any]]) -> dict[str, Any]:
    gold = gold_by_case[case_id]
    return {
        "case_id": case_id,
        "verdict": gold["expected_verdict"],
        "reason_codes": [gold["expected_reason"]],
    }


def _write_task(out_dir: Path, case: dict[str, Any], expected: dict[str, Any]) -> None:
    task_dir = out_dir / _slug(case["case_id"])
    if task_dir.exists():
        shutil.rmtree(task_dir)
    (task_dir / "environment").mkdir(parents=True)
    (task_dir / "solution").mkdir()
    (task_dir / "tests").mkdir()

    case_json = {
        "case_id": case["case_id"],
        "case_kind": case["case_kind"],
        "advisory_id": case["advisory_id"],
        "requirement": case.get("requirement"),
        "requirements": case.get("requirements"),
        "environment": case.get("environment"),
        "source_record_digest": case["source_record_digest"],
        "split": case["split"],
    }
    _write_lf(
        task_dir / "environment" / "case.json",
        json.dumps(case_json, ensure_ascii=False, indent=2) + "\n",
    )
    _write_lf(task_dir / "environment" / "Dockerfile", DOCKERFILE)
    _write_lf(task_dir / "task.toml", TASK_TOML)
    _write_lf(task_dir / "instruction.md", INSTRUCTION)

    expected_json = json.dumps(expected, sort_keys=False, separators=(",", ":"))
    source_digest = case["source_record_digest"]
    result_pass = json.dumps(
        {
            "schema_version": "public_osv_harbor_verifier.v1",
            "passed": True,
            "source_record_digest": source_digest,
            "case_kind": case["case_kind"],
        },
        separators=(",", ":"),
    )
    result_fail = json.dumps(
        {
            "schema_version": "public_osv_harbor_verifier.v1",
            "passed": False,
            "source_record_digest": source_digest,
            "case_kind": case["case_kind"],
        },
        separators=(",", ":"),
    )
    _write_lf(
        task_dir / "solution" / "solve.sh",
        "#!/bin/bash\n"
        "set -euo pipefail\n"
        "cat > /app/prediction.json <<'EOF'\n"
        f"{expected_json}\n"
        "EOF\n",
    )
    _write_lf(
        task_dir / "tests" / "test.sh",
        "#!/bin/bash\n"
        "set -euo pipefail\n"
        "mkdir -p /logs/verifier\n"
        f"expected='{expected_json}'\n"
        "actual=\"$(tr -d '\\r\\n' < /app/prediction.json)\"\n"
        'if [ "$actual" = "$expected" ]; then\n'
        "  echo 1 > /logs/verifier/reward.txt\n"
        f"  printf '%s\\n' '{result_pass}' > /logs/verifier/result.json\n"
        "else\n"
        "  echo 0 > /logs/verifier/reward.txt\n"
        f"  printf '%s\\n' '{result_fail}' > /logs/verifier/result.json\n"
        "  exit 1\n"
        "fi\n",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="data/public_osv_pilot")
    parser.add_argument("--output", default="data/harbor_tasks/public_osv_subset")
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    out_dir = Path(args.output)
    inputs = _load_jsonl(data_dir / "inputs.jsonl")
    gold_by_case = {row["case_id"]: row for row in _load_jsonl(data_dir / "gold.jsonl")}
    selected = _select_cases(inputs)
    if len(selected) != len(PREFERRED_KINDS):
        raise SystemExit(f"selected {len(selected)} cases, expected {len(PREFERRED_KINDS)}")

    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.iterdir():
        if old.is_dir():
            shutil.rmtree(old)
    for case in selected:
        _write_task(out_dir, case, _expected_from_gold(case["case_id"], gold_by_case))

    manifest = {
        "schema_version": "harbor_public_osv_subset_manifest.v1",
        "source_data_dir": str(data_dir),
        "task_count": len(selected),
        "case_ids": [case["case_id"] for case in selected],
        "case_kinds": [case["case_kind"] for case in selected],
        "claim_boundary": "Oracle/verifier parity subset only; not AgentHost or model effectiveness.",
    }
    _write_lf(out_dir / "SUBSET_MANIFEST.json", json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
