from __future__ import annotations

import argparse
import json
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from expert_skill_system.core.canonical import sha256_bytes, sha256_json
from expert_skill_system.evaluation.osv_benchmark import GENERATOR_VERSION, build_public_osv_cases

DEFAULT_IDS = (
    "GHSA-34jh-p97f-mpxf",
    "GHSA-462w-v97r-4m45",
    "GHSA-9hjg-9r4m-mvj7",
    "GHSA-v845-jxx5-vc9f",
    "GHSA-x84v-xcm2-53pg",
    "PYSEC-2017-98",
    "PYSEC-2018-28",
    "PYSEC-2019-217",
    "PYSEC-2021-66",
    "PYSEC-2023-74",
)
SCHEMA_URL = "https://raw.githubusercontent.com/ossf/osv-schema/main/validation/schema.json"
API_ROOT = "https://api.osv.dev/v1/vulns"


def fetch_json(url: str, timeout: float) -> tuple[dict[str, Any], bytes]:
    request = urllib.request.Request(url, headers={"User-Agent": "expert-skill-osv-pilot/1.0"})
    with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 - fixed public endpoints
        payload = response.read()
    return json.loads(payload), payload


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_raw(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def write_jsonl(path: Path, rows: tuple[dict[str, Any], ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="data/public_osv_pilot")
    parser.add_argument("--timeout", type=float, default=45.0)
    args = parser.parse_args()
    output = Path(args.output)
    schema, schema_bytes = fetch_json(SCHEMA_URL, args.timeout)
    write_raw(output / "schema" / "osv-schema.json", schema_bytes)
    records: list[dict[str, Any]] = []
    sources: list[dict[str, Any]] = []
    for record_id in DEFAULT_IDS:
        url = f"{API_ROOT}/{record_id}"
        record, raw = fetch_json(url, args.timeout)
        records.append(record)
        frozen_path = output / "records" / f"{record_id}.json"
        write_raw(frozen_path, raw)
        sources.append(
            {
                "record_id": record_id,
                "url": url,
                "frozen_path": frozen_path.as_posix(),
                "sha256": sha256_bytes(raw),
            }
        )
    benchmark = build_public_osv_cases(records)
    write_json(output / "osv_snapshot.json", {"vulns": records})
    write_jsonl(output / "inputs.jsonl", benchmark.inputs)
    write_jsonl(output / "gold.jsonl", benchmark.gold)
    splits = {
        name: [item["case_id"] for item in benchmark.inputs if item["split"] == name]
        for name in ("build", "dev", "heldout")
    }
    write_json(
        output / "split_manifest.json",
        {
            "schema_version": "public_osv_split_manifest.v1",
            "generator_version": GENERATOR_VERSION,
            "selection_rule": "fixed_record_ids; affected and first fixed boundary; sha256(case_id) mod 10",
            "splits": splits,
            "input_digest": sha256_json(list(benchmark.inputs)),
            "gold_digest": sha256_json(list(benchmark.gold)),
        },
    )
    write_json(
        output / "SOURCE_MANIFEST.json",
        {
            "schema_version": "public_osv_source_manifest.v1",
            "captured_at": datetime.now(UTC).isoformat(),
            "dataset_source": "OSV public API",
            "schema_url": SCHEMA_URL,
            "schema_sha256": sha256_bytes(schema_bytes),
            "generator_version": GENERATOR_VERSION,
            "record_ids": list(DEFAULT_IDS),
            "records": sources,
            "exclusions": list(benchmark.exclusions),
            "license_note": "Each OSV record retains upstream source metadata; verify upstream licenses before redistribution.",
        },
    )
    print(
        json.dumps(
            {
                "status": "built",
                "output": str(output.resolve()),
                "records": len(records),
                "cases": len(benchmark.inputs),
                "splits": {key: len(value) for key, value in splits.items()},
                "exclusions": len(benchmark.exclusions),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
