from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from skill_deployment.evidence import write_json, write_text  # noqa: E402


OUTPUT_ROOT = ROOT / "outputs" / "external_security_validation"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_payload(target_sample_count: int) -> dict:
    return {
        "run_id": "cyberseceval_style_defensive_small_sample_scaffold",
        "created_at": utc_now(),
        "status": "scaffold_not_executed",
        "target_sample_count": target_sample_count,
        "benchmark_order": [
            "CyberSecEval4_or_AutoPatchBench_style_defensive_subset",
            "SecureAgentBench_reference_subset_later",
            "CVE_Bench_defensive_sandbox_subset_later",
            "SWE_bench_non_security_transfer_later",
        ],
        "required_case_chain": [
            "baseline_no_skill",
            "skill_v1",
            "skill_v2_or_evolved",
            "verifier",
            "marginal_utility",
            "qualification_card",
            "reviewer_packet",
        ],
        "required_metrics": [
            "detection_or_patch_validation_score",
            "schema_compliance",
            "false_positive_delta",
            "cost_delta",
            "v2_over_v1_gain",
            "v2_over_no_skill_gain",
            "gap_to_upper_bound",
        ],
        "sample_categories_required": [
            "success",
            "failure",
            "no_marginal_gain",
            "false_positive_risk",
        ],
        "safety_boundary": {
            "allowed": ["defensive_detection", "explanation", "fix_recommendation", "patch_validation"],
            "forbidden": [
                "exploit_generation",
                "attack_chain_execution",
                "unauthorized_target_testing",
                "reusable_exploitation_steps_in_external_reports",
            ],
            "cve_policy": "CVE-style tasks must run only inside local sandbox or benchmark artifacts.",
        },
        "claim_boundary": "No external benchmark result is claimed until real cases are downloaded, executed, and validated.",
    }


def render_markdown(payload: dict) -> str:
    lines = [
        "# External Security Validation Scaffold",
        "",
        f"- Status: `{payload['status']}`",
        f"- Target sample count: `{payload['target_sample_count']}`",
        "",
        "## Benchmark Order",
        "",
    ]
    for item in payload["benchmark_order"]:
        lines.append(f"- `{item}`")
    lines.extend(
        [
            "",
            "## Safety Boundary",
            "",
            "- Defensive detection, explanation, fix recommendation, and patch validation only.",
            "- No exploit generation, attack-chain execution, unauthorized target testing, or reusable exploitation steps.",
            "- No external result claim until real benchmark cases are executed and validated.",
            "",
        ]
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the P2 external defensive security validation scaffold.")
    parser.add_argument("--target-sample-count", type=int, default=30)
    parser.add_argument("--output-dir", default=str(OUTPUT_ROOT))
    args = parser.parse_args(argv)
    payload = build_payload(args.target_sample_count)
    out_dir = Path(args.output_dir)
    write_json(out_dir / "cyberseceval_style_small_sample_scaffold.json", payload)
    write_text(out_dir / "cyberseceval_style_small_sample_scaffold.md", render_markdown(payload))
    print(json.dumps({"output": str(out_dir / "cyberseceval_style_small_sample_scaffold.json"), "status": payload["status"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
