from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from verify_api_review_json import verify_review


OUT_DIR = Path("outputs/mvp_vertical_slice/output_format_error_001")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def estimate_tokens(text: str) -> int:
    return max(1, round(len(text) / 4)) if text else 0


def build_bad_review() -> dict[str, Any]:
    return {
        "findings": [
            {
                "rule_id": "R001",
                "issue": "Authentication boundary is underspecified."
            },
            {
                "rule_id": "R002",
                "issue": "Request validation constraints are missing."
            }
        ]
    }


def build_execution_report(verification: dict[str, Any]) -> dict[str, Any]:
    return {
        "adapter": "local_output_contract_adapter_v1",
        "task_name": "api-review-output-format-error-001",
        "passed": verification["passed"],
        "final_status": "PASS" if verification["passed"] else "FAIL",
        "final_reward": verification["reward"],
        "attempt_count": 1,
        "status_trajectory": ["PASS" if verification["passed"] else "FAIL"],
        "reward_trajectory": [verification["reward"]],
        "failure_type": verification["failure_type"],
        "diagnosis": {
            "affected_rule_ids": ["OUTPUT_CONTRACT"] if verification["failure_type"] == "output_format_error" else [],
            "patch_ready": verification["failure_type"] == "output_format_error",
            "patch_hint": "Rewrite the compact skill output contract with required finding fields.",
            "verifier_stdout": verification["message"],
        },
        "cost": {
            "input_tokens": None,
            "output_tokens": estimate_tokens(json.dumps(build_bad_review(), ensure_ascii=False)),
            "skill_gen_calls": 0,
            "total_time_s": 0,
        },
    }


def patch_compact_skill(compact_v1: str) -> str:
    schema = """## Output Contract Patch

This patch addresses `output_format_error`, not `missing_rule`.

Return valid JSON only. Each item in `findings` must include all required fields:

```json
{
  "findings": [
    {
      "rule_id": "R001",
      "issue": "Concise issue description",
      "severity": "high|medium|low",
      "evidence": "Exact API spec excerpt or field name"
    }
  ]
}
```

Do not omit `severity` or `evidence`. Do not return markdown fences, prose, or partial objects.
"""
    return compact_v1.rstrip() + "\n\n" + schema


def build_repair_log(report: dict[str, Any]) -> str:
    return f"""# Output Format Error Repair Log

## Source Execution Report

- Task: {report['task_name']}
- Passed: {report['passed']}
- Failure type: {report['failure_type']}
- Affected contract: OUTPUT_CONTRACT
- Patch action: rewrite_output_contract

## Interpretation

This is not a `missing_rule` patch. The verifier did not fail because R005/R006 were absent from the compact skill. It failed because the agent output violated the required review JSON contract: each finding must include `rule_id`, `issue`, `severity`, and `evidence`.

## Patch

The compact skill v2 adds an explicit JSON schema and required-field instruction. The patch target is the output contract, not a domain review rule.
"""


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    compact_v1 = read_text(Path("outputs/mvp_vertical_slice/baseline_001/compact_skill_v1.md"))
    bad_review = build_bad_review()
    write_json(OUT_DIR / "bad_review.json", bad_review)
    verification = verify_review(OUT_DIR / "bad_review.json")
    report = build_execution_report(verification)
    compact_v2 = patch_compact_skill(compact_v1)
    validation_gate = {
        "gate": "output_contract_patch_gate_v0",
        "accepted": report["diagnosis"]["patch_ready"] and report["failure_type"] == "output_format_error",
        "affected_rule_ids": report["diagnosis"]["affected_rule_ids"],
        "patch_action": "rewrite_output_contract",
        "reasons": [
            "Patch accepted because verifier failure is output_format_error and affected target is OUTPUT_CONTRACT."
        ],
    }
    cost_summary = {
        "token_estimator": "round(characters / 4)",
        "compact_skill_v1_tokens": estimate_tokens(compact_v1),
        "compact_skill_v2_tokens": estimate_tokens(compact_v2),
        "token_increase_ratio": round((estimate_tokens(compact_v2) - estimate_tokens(compact_v1)) / estimate_tokens(compact_v1), 3),
        "failure_type": report["failure_type"],
        "patch_action": "rewrite_output_contract",
    }
    write_text(OUT_DIR / "compact_skill_v1.md", compact_v1)
    write_text(OUT_DIR / "compact_skill_v2.md", compact_v2)
    write_json(OUT_DIR / "verification_result.json", verification)
    write_json(OUT_DIR / "execution_report_spark.json", report)
    write_text(OUT_DIR / "repair_log_format.md", build_repair_log(report))
    write_json(OUT_DIR / "validation_gate.json", validation_gate)
    write_json(OUT_DIR / "cost_summary.json", cost_summary)
    write_json(
        OUT_DIR / "manifest.json",
        {
            "run_id": OUT_DIR.name,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "artifacts": [
                "bad_review.json",
                "verification_result.json",
                "execution_report_spark.json",
                "repair_log_format.md",
                "compact_skill_v1.md",
                "compact_skill_v2.md",
                "validation_gate.json",
                "cost_summary.json",
            ],
            "boundary": "Second failure taxonomy vertical slice only; not a complete taxonomy benchmark.",
        },
    )
    print(json.dumps({"output_dir": str(OUT_DIR), "failure_type": report["failure_type"], "patch_action": "rewrite_output_contract"}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
