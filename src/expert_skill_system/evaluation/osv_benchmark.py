from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

from packaging.version import InvalidVersion, Version

from ..core.canonical import sha256_json

GENERATOR_VERSION = "public_osv_pair_generator.v1"
EVALUATOR_VERSION = "public_osv_pair_evaluator.v1"


@dataclass(frozen=True)
class GeneratedBenchmark:
    inputs: tuple[dict[str, Any], ...]
    gold: tuple[dict[str, Any], ...]
    exclusions: tuple[dict[str, str], ...]


def stable_split(case_id: str) -> str:
    bucket = int(hashlib.sha256(case_id.encode("utf-8")).hexdigest()[:8], 16) % 10
    if bucket < 6:
        return "build"
    if bucket < 8:
        return "dev"
    return "heldout"


def build_public_osv_cases(records: list[dict[str, Any]]) -> GeneratedBenchmark:
    inputs: list[dict[str, Any]] = []
    gold: list[dict[str, Any]] = []
    exclusions: list[dict[str, str]] = []
    for record in sorted(records, key=lambda item: str(item.get("id", ""))):
        record_id = str(record.get("id", ""))
        affected = _first_supported_pypi_affected(record)
        if affected is None:
            exclusions.append({"record_id": record_id, "reason": "NO_SUPPORTED_PYPI_ECOSYSTEM_RANGE"})
            continue
        package = str(affected["package"]["name"])
        ranges = affected.get("ranges", [])
        versions = affected.get("versions", [])
        affected_version = _latest_listed_affected_version(versions, ranges)
        fixed_version = _first_fixed_version(ranges)
        if affected_version is None:
            exclusions.append({"record_id": record_id, "reason": "NO_VALID_LISTED_AFFECTED_VERSION"})
            continue
        _append_case(
            inputs,
            gold,
            record,
            package,
            affected_version,
            "affected",
            "advisory_applicable",
            "VERSION_IN_RANGE",
        )
        if fixed_version is not None:
            _append_case(
                inputs,
                gold,
                record,
                package,
                fixed_version,
                "fixed_boundary",
                "advisory_not_applicable",
                "VERSION_OUT_OF_RANGE",
            )
        else:
            exclusions.append({"record_id": record_id, "reason": "NO_VALID_FIXED_BOUNDARY"})
    if inputs:
        record_id = str(inputs[0]["advisory_id"])
        source_digest = str(inputs[0]["source_record_digest"])
        case_id = f"{record_id}__package_absent"
        inputs.append(
            _input_case(
                case_id=case_id,
                advisory_id=record_id,
                requirement="benchmark-control-package==1.0.0",
                source_record_digest=source_digest,
                case_kind="package_absent_control",
            )
        )
        gold.append(_gold_case(case_id, "advisory_not_applicable", "PACKAGE_NOT_PRESENT"))
    inputs.sort(key=lambda item: item["case_id"])
    gold.sort(key=lambda item: item["case_id"])
    return GeneratedBenchmark(tuple(inputs), tuple(gold), tuple(exclusions))


def evaluate_predictions(
    inputs: list[dict[str, Any]], gold: list[dict[str, Any]], predictions: list[dict[str, Any]]
) -> dict[str, Any]:
    input_ids = {str(item["case_id"]) for item in inputs}
    gold_by_id = {str(item["case_id"]): item for item in gold}
    prediction_by_id = {str(item["case_id"]): item for item in predictions}
    rows: list[dict[str, Any]] = []
    for case_id in sorted(input_ids):
        expected = gold_by_id.get(case_id)
        actual = prediction_by_id.get(case_id)
        verdict_match = bool(expected and actual and actual.get("verdict") == expected.get("expected_verdict"))
        reason_match = bool(
            expected
            and actual
            and expected.get("expected_reason") in set(actual.get("reason_codes", []))
        )
        rows.append(
            {
                "case_id": case_id,
                "split": next(item["split"] for item in inputs if item["case_id"] == case_id),
                "verdict_match": verdict_match,
                "reason_match": reason_match,
                "passed": verdict_match and reason_match,
                "missing_prediction": actual is None,
                "expected": expected,
                "actual": actual,
            }
        )
    passed = sum(bool(row["passed"]) for row in rows)
    false_safe = sum(
        bool(
            row["actual"]
            and row["actual"].get("verdict") == "advisory_not_applicable"
            and row["expected"]
            and row["expected"].get("expected_verdict") == "advisory_applicable"
        )
        for row in rows
    )
    return {
        "schema_version": EVALUATOR_VERSION,
        "input_manifest_digest": sha256_json(inputs),
        "gold_manifest_digest": sha256_json(gold),
        "prediction_digest": sha256_json(predictions),
        "case_count": len(rows),
        "passed_count": passed,
        "accuracy": passed / len(rows) if rows else 0.0,
        "false_safe_count": false_safe,
        "missing_prediction_count": sum(bool(row["missing_prediction"]) for row in rows),
        "rows": rows,
    }


def _append_case(
    inputs: list[dict[str, Any]],
    gold: list[dict[str, Any]],
    record: dict[str, Any],
    package: str,
    version: str,
    case_kind: str,
    verdict: str,
    reason: str,
) -> None:
    record_id = str(record["id"])
    case_id = f"{record_id}__{case_kind}"
    inputs.append(
        _input_case(
            case_id=case_id,
            advisory_id=record_id,
            requirement=f"{package}=={version}",
            source_record_digest=sha256_json(record),
            case_kind=case_kind,
        )
    )
    gold.append(_gold_case(case_id, verdict, reason))


def _input_case(
    *, case_id: str, advisory_id: str, requirement: str, source_record_digest: str, case_kind: str
) -> dict[str, Any]:
    return {
        "schema_version": "public_osv_pair_input.v1",
        "case_id": case_id,
        "advisory_id": advisory_id,
        "requirement": requirement,
        "environment": {
            "python_version": "3.11",
            "python_full_version": "3.11.9",
            "sys_platform": "linux",
            "platform_system": "Linux",
            "implementation_name": "cpython",
        },
        "case_kind": case_kind,
        "split": stable_split(case_id),
        "source_record_digest": source_record_digest,
    }


def _gold_case(case_id: str, verdict: str, reason: str) -> dict[str, Any]:
    return {
        "schema_version": "public_osv_pair_gold.v1",
        "case_id": case_id,
        "expected_verdict": verdict,
        "expected_reason": reason,
    }


def _first_supported_pypi_affected(record: dict[str, Any]) -> dict[str, Any] | None:
    for affected in record.get("affected", []):
        package = affected.get("package", {})
        if package.get("ecosystem") != "PyPI" or not package.get("name"):
            continue
        if any(item.get("type") == "ECOSYSTEM" for item in affected.get("ranges", [])):
            return affected
    return None


def _latest_listed_affected_version(versions: list[str], ranges: list[dict[str, Any]]) -> str | None:
    valid: list[tuple[Version, str]] = []
    for text in versions:
        try:
            version = Version(text)
        except InvalidVersion:
            continue
        if _is_affected(version, ranges):
            valid.append((version, text))
    if not valid:
        return None
    return max(valid, key=lambda item: item[0])[1]


def _first_fixed_version(ranges: list[dict[str, Any]]) -> str | None:
    for range_item in ranges:
        if range_item.get("type") != "ECOSYSTEM":
            continue
        for event in range_item.get("events", []):
            text = event.get("fixed")
            if text:
                try:
                    Version(str(text))
                except InvalidVersion:
                    continue
                return str(text)
    return None


def _is_affected(version: Version, ranges: list[dict[str, Any]]) -> bool:
    affected = False
    for range_item in ranges:
        if range_item.get("type") != "ECOSYSTEM":
            continue
        current = False
        for event in range_item.get("events", []):
            try:
                if "introduced" in event and (event["introduced"] == "0" or version >= Version(event["introduced"])):
                    current = True
                if "fixed" in event and version >= Version(event["fixed"]):
                    current = False
                if "last_affected" in event and version > Version(event["last_affected"]):
                    current = False
                if "limit" in event and version >= Version(event["limit"]):
                    current = False
            except InvalidVersion:
                return False
        affected = affected or current
    return affected
