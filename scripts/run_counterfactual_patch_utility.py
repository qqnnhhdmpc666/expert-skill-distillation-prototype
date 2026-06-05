from __future__ import annotations

import json
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from verify_api_review_json import verify_review


OUT_DIR = Path("outputs/mvp_vertical_slice/counterfactual_patch_utility_001")
PATCH_DIR = OUT_DIR / "patch_variants"
VERIFY_DIR = OUT_DIR / "verifier_results"
RANDOM_SEED = 260605

RULE_PATCHES = {
    "R003": {
        "text": "- [R003] Check error codes for validation, auth, permission, not found, duplicate, and server errors.",
        "finding": {
            "rule_id": "R003",
            "issue": "Error code coverage is incomplete.",
            "severity": "high",
            "evidence": "Error table only includes success and generic server error.",
        },
    },
    "R005": {
        "text": "- [R005] Check consistent envelope fields: code, message, request_id, and data.",
        "finding": {
            "rule_id": "R005",
            "issue": "Response envelope lacks request_id.",
            "severity": "medium",
            "evidence": "Response includes code, message, and data but no request_id.",
        },
    },
    "R006": {
        "text": "- [R006] Check whether mutation endpoints document idempotency or duplicate submission handling.",
        "finding": {
            "rule_id": "R006",
            "issue": "Mutation endpoint does not explain idempotency or duplicate submission behavior.",
            "severity": "medium",
            "evidence": "POST mutation endpoint does not document idempotency or duplicate handling.",
        },
    },
    "R007": {
        "text": "- [R007] Check request_id, trace metadata, and audit logging expectations.",
        "finding": {
            "rule_id": "R007",
            "issue": "Trace metadata and audit logging expectations are not documented.",
            "severity": "low",
            "evidence": "No audit logging section is present.",
        },
    },
}

OUTPUT_CONTRACT_PATCH = """## Output Contract Patch

Return valid JSON only. Each finding must include `rule_id`, `issue`, `severity`, and `evidence`. Do not omit required fields.
"""


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def estimate_tokens(text: str) -> int:
    return max(1, round(len(text) / 4)) if text else 0


def base_review_v1() -> dict[str, Any]:
    return read_json(Path("outputs/mvp_vertical_slice/agent_mock_api_review_001/review_v1.json"))


def full_review_v2() -> dict[str, Any]:
    return read_json(Path("outputs/mvp_vertical_slice/agent_mock_api_review_001/review_v2.json"))


def bad_format_review() -> dict[str, Any]:
    return read_json(Path("outputs/mvp_vertical_slice/output_format_error_001/bad_review.json"))


def normalize_review_with_contract(review: dict[str, Any]) -> dict[str, Any]:
    normalized = {"findings": []}
    for finding in review.get("findings", []):
        next_finding = dict(finding)
        next_finding.setdefault("severity", "medium")
        next_finding.setdefault("evidence", "Evidence field required by output contract patch.")
        normalized["findings"].append(next_finding)
    return normalized


def append_findings(review: dict[str, Any], rule_ids: list[str]) -> dict[str, Any]:
    next_review = {"findings": [dict(finding) for finding in review.get("findings", [])]}
    existing = {finding.get("rule_id") for finding in next_review["findings"]}
    for rule_id in rule_ids:
        if rule_id not in existing:
            next_review["findings"].append(dict(RULE_PATCHES[rule_id]["finding"]))
    return next_review


def run_verifier(review: dict[str, Any], failure_case: str, patch_variant: str) -> dict[str, Any]:
    review_path = PATCH_DIR / failure_case / f"{patch_variant}.review.json"
    result_path = VERIFY_DIR / failure_case / f"{patch_variant}.verification.json"
    write_json(review_path, review)
    result = verify_review(review_path)
    write_json(result_path, result)
    return result


def recovered_rules(before_missing: list[str], after_missing: list[str]) -> list[str]:
    return sorted(set(before_missing) - set(after_missing))


def make_record(
    *,
    failure_case: str,
    original_failure_type: str,
    patch_variant: str,
    patch_action: str,
    type_correct: bool,
    affected_rule_ids: list[str],
    sampled_rule_ids: list[str],
    base_tokens: int,
    patch_text: str,
    before_missing: list[str],
    verification: dict[str, Any],
    notes: str,
    random_seed: int | None = None,
) -> dict[str, Any]:
    after_missing = verification.get("missing_rule_ids", [])
    hit_affected = bool(set(sampled_rule_ids) & set(affected_rule_ids))
    failure_resolved = verification["passed"] if original_failure_type == "missing_rule" else verification["failure_type"] != original_failure_type
    return {
        "failure_case": failure_case,
        "original_failure_type": original_failure_type,
        "patch_variant": patch_variant,
        "patch_action": patch_action,
        "type_correct": type_correct,
        "affected_rule_ids": affected_rule_ids,
        "sampled_rule_ids": sampled_rule_ids,
        "random_seed": random_seed,
        "whether_hit_affected_rule": hit_affected,
        "added_tokens": max(0, estimate_tokens(patch_text) - base_tokens),
        "verifier_passed": verification["passed"],
        "recovered_rules": recovered_rules(before_missing, after_missing),
        "failure_resolved": failure_resolved,
        "whether_patch_was_type_correct": type_correct,
        "verifier_result": verification,
        "notes": notes,
    }


def rule_patch_text(rule_ids: list[str]) -> str:
    if not rule_ids:
        return ""
    return "\n".join(str(RULE_PATCHES[rule_id]["text"]) for rule_id in rule_ids)


def missing_rule_experiment(rng: random.Random) -> list[dict[str, Any]]:
    failure_case = "missing_rule"
    original_failure = run_verifier(base_review_v1(), failure_case, "original_failure")
    before_missing = original_failure["missing_rule_ids"]
    base_patch_tokens = 0
    rows: list[dict[str, Any]] = []

    variants = [
        ("no_patch", "none", False, [], ["R005", "R006"], base_review_v1(), ""),
        (
            "random_patch_any",
            "random_rule_patch",
            None,
            rng.sample(["R003", "R005", "R006", "R007"], 2),
            None,
            None,
            "Randomly sampled two candidate rules from a small rule pool.",
        ),
        (
            "random_patch_non_affected",
            "random_rule_patch",
            False,
            rng.sample(["R003", "R007"], 2),
            None,
            None,
            "Randomly sampled only non-affected rules.",
        ),
        ("wrong_type_patch", "rewrite_output_contract", False, [], ["R005", "R006"], normalize_review_with_contract(base_review_v1()), "Wrong type: rewrites output contract but does not add R005/R006."),
        ("compiler_patch", "patch_into_compact_v2", True, ["R005", "R006"], ["R005", "R006"], append_findings(base_review_v1(), ["R005", "R006"]), "Type-correct compiler patch adds affected missing rules."),
        ("full_skill_or_oracle_patch", "upper_bound_full_review", True, ["R005", "R006"], ["R001", "R002", "R003", "R004", "R005", "R006"], full_review_v2(), "Upper bound only; not part of fair budget comparison."),
    ]

    for patch_variant, patch_action, type_correct, sampled, affected_override, review_override, notes in variants:
        sampled_rule_ids = sampled
        review = review_override
        if review is None:
            review = append_findings(base_review_v1(), sampled_rule_ids)
        if type_correct is None:
            type_correct = bool(set(sampled_rule_ids) & {"R005", "R006"})
        patch_text = rule_patch_text(sampled_rule_ids) if sampled_rule_ids else (OUTPUT_CONTRACT_PATCH if patch_action == "rewrite_output_contract" else "")
        verification = run_verifier(review, failure_case, patch_variant)
        rows.append(
            make_record(
                failure_case=failure_case,
                original_failure_type="missing_rule",
                patch_variant=patch_variant,
                patch_action=patch_action,
                type_correct=bool(type_correct),
                affected_rule_ids=affected_override if affected_override is not None else ["R005", "R006"],
                sampled_rule_ids=sampled_rule_ids,
                base_tokens=base_patch_tokens,
                patch_text=patch_text,
                before_missing=before_missing,
                verification=verification,
                notes=notes,
                random_seed=RANDOM_SEED if patch_variant.startswith("random") else None,
            )
        )
    return rows


def output_format_experiment(rng: random.Random) -> list[dict[str, Any]]:
    failure_case = "output_format_error"
    original_failure = run_verifier(bad_format_review(), failure_case, "original_failure")
    before_missing = original_failure["missing_rule_ids"]
    base_patch_tokens = 0
    random_rule = rng.choice(["R003", "R005", "R006", "R007"])
    variants = [
        ("no_patch", "none", False, ["OUTPUT_CONTRACT"], [], bad_format_review(), ""),
        ("random_rule_patch", "random_rule_patch", False, [random_rule], [random_rule], append_findings(bad_format_review(), [random_rule]), "Random content rule patch; does not fix missing required fields in existing findings."),
        ("wrong_missing_rule_patch", "patch_into_compact_v2", False, ["R005", "R006"], ["R005", "R006"], append_findings(bad_format_review(), ["R005", "R006"]), "Wrong type: adds missing-rule content but does not fix output contract."),
        ("output_contract_patch", "rewrite_output_contract", True, ["OUTPUT_CONTRACT"], [], normalize_review_with_contract(bad_format_review()), "Type-correct patch fills required fields."),
        ("full_contract_patch", "full_contract_patch", True, ["OUTPUT_CONTRACT"], [], normalize_review_with_contract(full_review_v2()), "Upper bound: complete review plus valid output contract."),
    ]
    rows: list[dict[str, Any]] = []
    for patch_variant, patch_action, type_correct, affected, sampled_rule_ids, review, notes in variants:
        patch_text = OUTPUT_CONTRACT_PATCH if "contract" in patch_action else rule_patch_text(sampled_rule_ids)
        verification = run_verifier(review, failure_case, patch_variant)
        rows.append(
            make_record(
                failure_case=failure_case,
                original_failure_type="output_format_error",
                patch_variant=patch_variant,
                patch_action=patch_action,
                type_correct=type_correct,
                affected_rule_ids=affected,
                sampled_rule_ids=sampled_rule_ids,
                base_tokens=base_patch_tokens,
                patch_text=patch_text,
                before_missing=before_missing,
                verification=verification,
                notes=notes,
                random_seed=RANDOM_SEED if patch_variant.startswith("random") else None,
            )
        )
    return rows


def render_summary(rows: list[dict[str, Any]]) -> str:
    lines = [
        "# Counterfactual Patch Utility 001",
        "",
        "## Positioning",
        "",
        "This is a toy counterfactual experiment. It tests whether type-correct failure attribution plus patch action better explains compact skill recovery than no patch, random patch, or wrong-type patch. It is not a benchmark.",
        "",
        f"- Random seed: `{RANDOM_SEED}`",
        "",
        "| Failure Case | Patch Variant | Action | Type Correct | Sampled Rules | Hit Affected | Added Tokens | Failure Resolved | Passed | Recovered Rules | Notes |",
        "|---|---|---|---|---|---|---:|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['failure_case']} | {row['patch_variant']} | {row['patch_action']} | {row['type_correct']} | "
            f"{', '.join(row['sampled_rule_ids']) if row['sampled_rule_ids'] else 'none'} | {row['whether_hit_affected_rule']} | "
            f"{row['added_tokens']} | {row['failure_resolved']} | {row['verifier_passed']} | "
            f"{', '.join(row['recovered_rules']) if row['recovered_rules'] else 'none'} | {row['notes']} |"
        )
    lines.extend(
        [
            "",
            "## Conservative Interpretation",
            "",
            "- If compiler patches outperform no/random/wrong-type patches, this partially supports the failure-to-patch mapping mechanism.",
            "- Random patches may occasionally hit affected rules because the toy rule pool is small; such hits must be reported, not hidden.",
            "- Full skill or oracle patches are upper bounds and are not part of the fair token-budget comparison.",
            "- For output-format failures, `failure_resolved` can be true even if `verifier_passed` is false: this means the format failure was fixed, but other missing-rule failures remain.",
            "- This experiment does not prove a general patch compiler.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    PATCH_DIR.mkdir(parents=True, exist_ok=True)
    VERIFY_DIR.mkdir(parents=True, exist_ok=True)
    rng = random.Random(RANDOM_SEED)
    rows = missing_rule_experiment(rng) + output_format_experiment(rng)
    write_json(OUT_DIR / "per_failure_results.json", rows)
    summary = {
        "run_id": OUT_DIR.name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "random_seed": RANDOM_SEED,
        "positioning": "toy counterfactual method exploration; not a benchmark",
        "records": rows,
        "conclusion": "partially_supported" if any(row["patch_variant"] == "compiler_patch" and row["failure_resolved"] for row in rows) else "inconclusive",
    }
    write_json(OUT_DIR / "summary.json", summary)
    write_text(OUT_DIR / "summary.md", render_summary(rows))
    write_text(OUT_DIR / "README.md", render_summary(rows))
    write_json(
        OUT_DIR / "manifest.json",
        {
            "run_id": OUT_DIR.name,
            "created_at": summary["created_at"],
            "artifacts": ["summary.json", "summary.md", "per_failure_results.json", "patch_variants/", "verifier_results/", "README.md"],
            "boundary": "Toy counterfactual; supports mechanism exploration only.",
        },
    )
    print(json.dumps({"output_dir": str(OUT_DIR), "records": len(rows), "random_seed": RANDOM_SEED}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
