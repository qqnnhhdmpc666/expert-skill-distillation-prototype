from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


OUT_DIR = Path("outputs/mvp_vertical_slice/operator_transfer_audit_001")
API_MATRIX = Path("outputs/mvp_vertical_slice/revision_decision_matrix_001/decision_matrix.json")
API_NAIVE = Path("outputs/mvp_vertical_slice/naive_revision_ablation_001/summary.json")
CONFIG_SUMMARY = Path("outputs/mvp_vertical_slice/second_domain_config_security_001/summary.json")


FROZEN_SKELETON: dict[str, dict[str, Any]] = {
    "missing_rule": {
        "operator": "patch_rule",
        "promotion_gate": ["must_resolve_missing_rule", "must_not_regress", "must_not_exceed_budget"],
        "trace_policy": "trace failure-critical or newly patched residual rules when trace is required",
    },
    "output_contract_error": {
        "operator": "rewrite_output_contract",
        "promotion_gate": ["required_fields_present", "must_not_regress", "must_not_exceed_budget"],
        "trace_policy": "not required unless output evidence is also traced",
    },
    "regression_observed": {
        "operator": "reject_and_rollback",
        "promotion_gate": ["preserve_previously_covered_rules"],
        "trace_policy": "not applicable",
    },
    "trace_budget_pressure": {
        "operator": "risk_based_selective_trace",
        "promotion_gate": ["trace_required_rules_have_evidence", "must_not_exceed_budget"],
        "trace_policy": "select failure-critical/newly-patched rules before full trace",
    },
}


CONFIG_TRANSFER_ROWS: list[dict[str, Any]] = [
    {
        "feedback_type": "missing_rule",
        "api_review_operator": "patch_rule",
        "config_security_operator": "patch_rule",
        "evidence_in_config": "C006 audit retention is missing in direct_summary/compact_v1 and recovered by typed revision.",
        "reused_skeleton": True,
        "domain_specific_adapter": "C006 maps to audit logging retention/export instead of R006 idempotency.",
        "supporting_artifact": "second_domain_config_security_001",
    },
    {
        "feedback_type": "output_contract_error",
        "api_review_operator": "rewrite_output_contract",
        "config_security_operator": "rewrite_output_contract",
        "evidence_in_config": "always_append_domain_rules reaches coverage 1.0 but produces 27 output-contract errors.",
        "reused_skeleton": True,
        "domain_specific_adapter": "config findings require config_path in addition to rule_id/issue/severity/evidence.",
        "supporting_artifact": "second_domain_config_security_001",
    },
    {
        "feedback_type": "regression_observed",
        "api_review_operator": "reject_and_rollback",
        "config_security_operator": "reject_regression",
        "evidence_in_config": "accept_if_current_failure_fixed patches C006 but drops previously covered C003.",
        "reused_skeleton": True,
        "domain_specific_adapter": "regression target is C003 least privilege instead of R003 error-code coverage.",
        "supporting_artifact": "second_domain_config_security_001",
    },
    {
        "feedback_type": "trace_budget_pressure",
        "api_review_operator": "risk_based_selective_trace",
        "config_security_operator": "selective_trace_residual_rule",
        "evidence_in_config": "always_full_trace is 629/260 over budget; selective trace of C006 passes at 166/260.",
        "reused_skeleton": True,
        "domain_specific_adapter": "trace target is residual C006 rather than R005/R006.",
        "supporting_artifact": "second_domain_config_security_001",
    },
]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def render_summary(payload: dict[str, Any]) -> str:
    lines = [
        "# Operator Transfer Audit 001",
        "",
        "## Purpose",
        "",
        "Check whether the second-domain config-security slice reused the API-review typed revision skeleton, or effectively redesigned a new flow.",
        "",
        "## Frozen Skeleton",
        "",
        "| Feedback Type | Operator | Promotion Gate | Trace Policy |",
        "|---|---|---|---|",
    ]
    for feedback_type, item in payload["frozen_skeleton"].items():
        lines.append(
            f"| {feedback_type} | {item['operator']} | {', '.join(item['promotion_gate'])} | {item['trace_policy']} |"
        )
    lines.extend(
        [
            "",
            "## Transfer Rows",
            "",
            "| Feedback Type | API Operator | Config Operator | Reused? | Domain-Specific Adapter |",
            "|---|---|---|---|---|",
        ]
    )
    for row in payload["transfer_rows"]:
        lines.append(
            f"| {row['feedback_type']} | {row['api_review_operator']} | {row['config_security_operator']} | "
            f"{row['reused_skeleton']} | {row['domain_specific_adapter']} |"
        )
    lines.extend(
        [
            "",
            "## Conclusion",
            "",
            f"- Status: {payload['conclusion']['status']}",
            f"- Finding: {payload['conclusion']['finding']}",
            f"- Boundary: {payload['conclusion']['boundary']}",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    created_at = datetime.now(timezone.utc).isoformat()
    api_matrix = read_json(API_MATRIX)
    api_naive = read_json(API_NAIVE)
    config_summary = read_json(CONFIG_SUMMARY)
    reused_count = sum(1 for row in CONFIG_TRANSFER_ROWS if row["reused_skeleton"])
    payload = {
        "run_id": OUT_DIR.name,
        "created_at": created_at,
        "positioning": "transfer audit over two controlled domains; not a general transfer proof",
        "source_artifacts": {
            "api_review_operator_matrix": str(API_MATRIX),
            "api_review_naive_ablation": str(API_NAIVE),
            "config_security_probe": str(CONFIG_SUMMARY),
        },
        "frozen_skeleton": FROZEN_SKELETON,
        "api_review_matrix_rows": len(api_matrix),
        "api_review_naive_ablation_status": api_naive["conclusion"]["status"],
        "config_security_status": config_summary["conclusion"]["status"],
        "transfer_rows": CONFIG_TRANSFER_ROWS,
        "reuse_summary": {
            "reused_rows": reused_count,
            "total_rows": len(CONFIG_TRANSFER_ROWS),
            "new_operator_added": False,
            "method_logic_rewritten": False,
            "domain_specific_adapters": [
                row["domain_specific_adapter"] for row in CONFIG_TRANSFER_ROWS
            ],
        },
        "conclusion": {
            "status": "partially_supported",
            "finding": (
                "Config-security reuses the frozen typed revision skeleton for the tested feedback types: missing_rule, "
                "output_contract_error, regression_observed, and trace_budget_pressure. The domain-specific parts are rule semantics, "
                "required output fields such as config_path, and which residual rule receives trace."
            ),
            "boundary": (
                "This audit checks reuse over a hand-constructed second domain. It does not prove that the skeleton transfers to arbitrary "
                "expert-skill domains or complex trajectory settings."
            ),
        },
    }
    write_json(OUT_DIR / "summary.json", payload)
    write_json(OUT_DIR / "transfer_rows.json", CONFIG_TRANSFER_ROWS)
    write_text(OUT_DIR / "summary.md", render_summary(payload))
    write_json(
        OUT_DIR / "manifest.json",
        {
            "run_id": OUT_DIR.name,
            "created_at": created_at,
            "artifacts": ["summary.json", "summary.md", "transfer_rows.json", "manifest.json"],
            "boundary": payload["conclusion"]["boundary"],
        },
    )
    print(json.dumps({"output_dir": str(OUT_DIR), "status": payload["conclusion"]["status"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
