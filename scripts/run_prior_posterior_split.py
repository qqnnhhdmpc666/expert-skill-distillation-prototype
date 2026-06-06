from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


OUT_DIR = Path("outputs/mvp_vertical_slice/prior_posterior_split_001")
API_POSTERIOR = Path("outputs/mvp_vertical_slice/posterior_revision_signal_audit_001/summary.json")
API_NAIVE = Path("outputs/mvp_vertical_slice/naive_revision_ablation_001/summary.json")
CONFIG_SUMMARY = Path("outputs/mvp_vertical_slice/second_domain_config_security_001/summary.json")


DOMAIN_SPLITS: list[dict[str, Any]] = [
    {
        "domain": "api_review",
        "residual_rule": "R006 idempotency / duplicate submission",
        "prior_signals": [
            "expert material contains API review rules",
            "R006 exists in full skill evidence",
            "rule priority is medium rather than high",
            "initial compact selection prefers R001-R004",
        ],
        "posterior_signals": [
            "Harbor/verifier reports missing_rule for R005/R006",
            "compact_v1 fails while compact_v2 passes",
            "rollback gate observes R003 regression in fixed-budget patch",
            "trace budget pressure shows full trace over budget",
        ],
        "prior_only_decision": {
            "decision": "likely_drop_or_deprioritize_residual_rule",
            "expected_result": "misses R006 under compact budget",
            "supported_by": "direct_summary_miss_analysis_001 and real_effect_eval_001",
        },
        "posterior_only_decision": {
            "decision": "patch affected missing rules and trace failure-critical rules",
            "expected_result": "recovers residual missing rules after verifier failure",
            "supported_by": "harbor_api_review_001/002, counterfactual_patch_utility_001, selective_trace_compiler_001",
        },
        "prior_plus_posterior_decision": {
            "decision": "preserve prior high-salience rules while patching posterior failure-critical rules and gating regression",
            "expected_result": "best current deployment decision",
            "supported_by": "validation_aware_compiler_001, rollback_gate_001, risk_trace_policy_robustness_001",
        },
        "posterior_required_for": [
            "identifying R006/R005 as failure-critical in compact deployment",
            "rejecting a patch that drops R003",
            "allocating trace to failure-critical rules rather than arbitrary high-priority rules",
        ],
        "prior_sufficient_for": [
            "building the initial full skill",
            "covering high-salience rules such as auth, validation, errors, and sensitive data",
        ],
    },
    {
        "domain": "config_security",
        "residual_rule": "C006 audit logging retention/export",
        "prior_signals": [
            "expert material contains configuration security rules",
            "C006 exists in full skill evidence",
            "C006 priority is medium and residual-deployment-critical",
            "initial compact/direct summary covers C001-C005",
        ],
        "posterior_signals": [
            "direct_summary/compact_v1 miss C006 in two cases",
            "always_append reveals output_contract_error",
            "accept_if_current_failure_fixed regresses C003",
            "always_full_trace and full skill exceed the budget",
        ],
        "prior_only_decision": {
            "decision": "likely_keep C001-C005 and omit C006",
            "expected_result": "coverage 0.825; misses two C006 instances",
            "supported_by": "second_domain_config_security_001 direct_summary_skill and compact_v1_no_revision",
        },
        "posterior_only_decision": {
            "decision": "patch C006, repair output contract, and trace C006",
            "expected_result": "recovers C006 but needs gate to avoid C003 regression and over-budget trace",
            "supported_by": "second_domain_config_security_001 strategy comparisons",
        },
        "prior_plus_posterior_decision": {
            "decision": "keep C001-C005, patch C006, preserve C003, use compact trace for C006, reject full trace/full skill over budget",
            "expected_result": "4/4 pass and accepted at 166/260",
            "supported_by": "second_domain_config_security_001 type_specific_operator_plus_gate_and_selective_trace",
        },
        "posterior_required_for": [
            "marking C006 as a residual deployment miss",
            "discovering that append-only repair breaks output contract",
            "detecting C003 regression under accept-if-fixed",
            "choosing selective trace instead of full trace under budget",
        ],
        "prior_sufficient_for": [
            "building the initial full skill",
            "covering salient rules C001-C005",
            "defining the output contract requirement before execution",
        ],
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
        "# Prior Posterior Split 001",
        "",
        "## Purpose",
        "",
        "Separate what prior expert-material signals can decide from what posterior verifier/execution signals add.",
        "",
        "| Domain | Prior-Only Decision | Posterior-Only Decision | Prior+Posterior Decision | Posterior Required For |",
        "|---|---|---|---|---|",
    ]
    for item in payload["domain_splits"]:
        lines.append(
            f"| {item['domain']} | {item['prior_only_decision']['decision']} | "
            f"{item['posterior_only_decision']['decision']} | {item['prior_plus_posterior_decision']['decision']} | "
            f"{'; '.join(item['posterior_required_for'])} |"
        )
    lines.extend(
        [
            "",
            "## Aggregate Interpretation",
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
    api_posterior = read_json(API_POSTERIOR)
    api_naive = read_json(API_NAIVE)
    config_summary = read_json(CONFIG_SUMMARY)
    posterior_required_items = sum(len(item["posterior_required_for"]) for item in DOMAIN_SPLITS)
    prior_sufficient_items = sum(len(item["prior_sufficient_for"]) for item in DOMAIN_SPLITS)
    payload = {
        "run_id": OUT_DIR.name,
        "created_at": created_at,
        "positioning": "diagnostic split over two controlled domains; not a causal proof",
        "source_artifacts": {
            "api_posterior_signal_audit": str(API_POSTERIOR),
            "api_naive_revision_ablation": str(API_NAIVE),
            "config_security_probe": str(CONFIG_SUMMARY),
        },
        "source_status": {
            "api_posterior_signal": api_posterior["conclusion"]["status"],
            "api_naive_ablation": api_naive["conclusion"]["status"],
            "config_security": config_summary["conclusion"]["status"],
        },
        "domain_splits": DOMAIN_SPLITS,
        "aggregate": {
            "domains": [item["domain"] for item in DOMAIN_SPLITS],
            "posterior_required_items": posterior_required_items,
            "prior_sufficient_items": prior_sufficient_items,
            "main_pattern": "prior builds broad initial skill; posterior identifies residual deployment-critical misses and unsafe revisions",
        },
        "conclusion": {
            "status": "partially_supported",
            "finding": (
                "Across the two controlled domains, prior signals are sufficient for initial full skills and many salient rules, "
                "but posterior signals are needed to identify residual deployment-critical misses, wrong repair type, regression, "
                "and trace-budget pressure. This is the current closest bridge to SPARK's posterior-evidence motivation."
            ),
            "boundary": (
                "This is a diagnostic split, not a causal or statistical proof. Prior-only decisions are represented by controlled "
                "summary/compact baselines, not by an exhaustive prior optimizer."
            ),
        },
    }
    write_json(OUT_DIR / "summary.json", payload)
    write_json(OUT_DIR / "domain_splits.json", DOMAIN_SPLITS)
    write_text(OUT_DIR / "summary.md", render_summary(payload))
    write_json(
        OUT_DIR / "manifest.json",
        {
            "run_id": OUT_DIR.name,
            "created_at": created_at,
            "artifacts": ["summary.json", "summary.md", "domain_splits.json", "manifest.json"],
            "boundary": payload["conclusion"]["boundary"],
        },
    )
    print(json.dumps({"output_dir": str(OUT_DIR), "status": payload["conclusion"]["status"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
