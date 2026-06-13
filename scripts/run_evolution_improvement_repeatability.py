from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from skill_deployment.install_state import read_skill_version  # noqa: E402
from skill_deployment.evidence import write_json, write_text  # noqa: E402

import scripts.run_defensive_security_mini_suite as mini  # noqa: E402
import scripts.run_iterative_contract_improvement as iter_ci  # noqa: E402


OUTPUT_ROOT = ROOT / "outputs" / "evolution_repeatability"
REPORT = ROOT / "reports" / "EVOLUTION_IMPROVEMENT_REPEATABILITY_STATUS.md"
SUMMARY_PATH = ROOT / "outputs" / "iterative_contract_improvement" / "iterative_contract_improvement_summary.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def api_key_present() -> bool:
    return bool(os.environ.get("OPENAI_API_KEY"))


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_promoted_candidates(summary: dict[str, Any]) -> list[dict[str, Any]]:
    candidates = []
    for item in summary.get("candidates", []):
        if ((item.get("promotion_decision") or {}).get("decision")) != "staged_promotion_proposal":
            continue
        candidate_dir = Path(str(item.get("candidate_dir") or ""))
        if not candidate_dir.exists():
            continue
        package, text, _manifest = read_skill_version(candidate_dir)
        candidates.append(
            {
                "candidate_id": item["candidate_id"],
                "title": item.get("title"),
                "candidate_dir": candidate_dir,
                "package": package,
                "text": text,
            }
        )
    return candidates


def render_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Evolution Improvement Repeatability Status",
        "",
        f"Generated at: `{payload['generated_at']}`",
        "",
        "This run measures whether previously promoted live-feedback candidate proposals remain promotable across fresh reruns.",
        "",
        "## Fresh Command",
        "",
        "```powershell",
        "skill-deploy evolution-repeatability --installed secure_code_review --repeats 3 --base-url https://api.deepseek.com --model deepseek-v4-flash",
        "```",
        "",
        "## Summary",
        "",
        f"- Candidate count: `{payload['candidate_count']}`",
        f"- Repeat count: `{payload['repeat_count']}`",
        f"- Stable promotion candidates: `{', '.join(payload['stable_promotion_candidates']) if payload['stable_promotion_candidates'] else 'none'}`",
        f"- `stable_evolution_improvement`: `{payload['stable_evolution_improvement']}`",
        "",
        "## Candidate Repeatability",
        "",
        "| Candidate | Promotions / repeats | Stable | Mean delta | Worst delta | Any FP regression | Any scope violation |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for item in payload["candidates"]:
        lines.append(
            f"| {item['candidate_id']} | {item['promotion_count']}/{payload['repeat_count']} | {item['stable_promotion']} | "
            f"{item['mean_score_delta']} | {item['worst_score_delta']} | {item['any_false_positive_regression']} | {item['any_scope_violation']} |"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- This is repeatability of fixed candidate proposals under fresh live reruns.",
            "- It is stronger than a single proposal artifact, but it is not proof of universal autonomous-search stability.",
            "- No candidate was auto-installed during this run.",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Rerun promoted live-feedback candidates and measure proposal stability.")
    parser.add_argument("--installed", default="secure_code_review")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--base-url", default=os.environ.get("OPENAI_BASE_URL") or "https://api.deepseek.com")
    parser.add_argument("--model", default=os.environ.get("MODEL") or os.environ.get("OPENAI_MODEL") or "deepseek-v4-flash")
    parser.add_argument("--timeout-seconds", type=float, default=60.0)
    args = parser.parse_args(argv)

    summary = read_json(SUMMARY_PATH, {})
    promoted_candidates = load_promoted_candidates(summary)
    if not promoted_candidates:
        payload = {
            "generated_at": utc_now(),
            "repeat_count": args.repeats,
            "candidate_count": 0,
            "stable_evolution_improvement": "blocked_no_promoted_candidates",
            "stable_promotion_candidates": [],
            "candidates": [],
            "blocked_reason": f"no staged promotion proposal found in {SUMMARY_PATH}",
            "api_key_present": api_key_present(),
        }
        write_json(OUTPUT_ROOT / "evolution_repeatability_summary.json", payload)
        write_text(REPORT, render_report(payload))
        print(json.dumps(payload, indent=2))
        return 1

    base, base_text, active_dir, pointer = iter_ci.load_active(args.installed)
    active_spec = mini.VariantSpec("active", base, base_text, active_dir, "active_installed_package")
    cases = iter_ci.validation_cases()

    candidate_summaries: list[dict[str, Any]] = []
    for candidate in promoted_candidates:
        repeat_rows: list[dict[str, Any]] = []
        promotion_count = 0
        any_fp_regression = False
        any_scope_violation = False
        score_deltas: list[float] = []
        for repeat_index in range(1, args.repeats + 1):
            repeat_root = OUTPUT_ROOT / candidate["candidate_id"] / f"repeat_{repeat_index:02d}"
            active_rows = [
                iter_ci.run_case(
                    case_payload=case_payload,
                    spec=active_spec,
                    pointer=pointer,
                    output_dir=repeat_root / "active",
                    base_url=args.base_url,
                    model=args.model,
                    timeout_seconds=args.timeout_seconds,
                )
                for case_payload in cases
            ]
            candidate_spec = mini.VariantSpec(candidate["candidate_id"], candidate["package"], candidate["text"], candidate["candidate_dir"], "iterative_contract_candidate")
            candidate_rows = [
                iter_ci.run_case(
                    case_payload=case_payload,
                    spec=candidate_spec,
                    pointer=pointer,
                    output_dir=repeat_root / "candidate",
                    base_url=args.base_url,
                    model=args.model,
                    timeout_seconds=args.timeout_seconds,
                )
                for case_payload in cases
            ]
            validation, decision = iter_ci.decide_candidate(active_rows, candidate_rows)
            promoted = decision["decision"] == "staged_promotion_proposal"
            if promoted:
                promotion_count += 1
            any_fp_regression = any_fp_regression or validation["false_positive_delta"] > 0
            any_scope_violation = any_scope_violation or bool(validation["scope_violation"])
            score_deltas.append(float(validation["score_delta"]))
            repeat_rows.append(
                {
                    "repeat_index": repeat_index,
                    "validation_result": validation,
                    "promotion_decision": decision,
                    "active_rows": active_rows,
                    "candidate_rows": candidate_rows,
                }
            )
        stable = promotion_count == args.repeats and not any_fp_regression and not any_scope_violation and all(delta > 0 for delta in score_deltas)
        candidate_summary = {
            "candidate_id": candidate["candidate_id"],
            "title": candidate["title"],
            "promotion_count": promotion_count,
            "stable_promotion": stable,
            "mean_score_delta": round(sum(score_deltas) / len(score_deltas), 4) if score_deltas else 0.0,
            "worst_score_delta": round(min(score_deltas), 4) if score_deltas else 0.0,
            "any_false_positive_regression": any_fp_regression,
            "any_scope_violation": any_scope_violation,
            "score_deltas": score_deltas,
            "repeats": repeat_rows,
        }
        candidate_summaries.append(candidate_summary)

    stable_candidates = [item["candidate_id"] for item in candidate_summaries if item["stable_promotion"]]
    payload = {
        "generated_at": utc_now(),
        "installed_skill": args.installed,
        "repeat_count": args.repeats,
        "candidate_count": len(candidate_summaries),
        "api_key_present": api_key_present(),
        "stable_promotion_candidates": stable_candidates,
        "stable_evolution_improvement": "pass" if stable_candidates else "partial",
        "candidates": candidate_summaries,
    }
    write_json(OUTPUT_ROOT / "evolution_repeatability_summary.json", payload)
    write_text(REPORT, render_report(payload))
    print(
        json.dumps(
            {
                "status": payload["stable_evolution_improvement"],
                "stable_promotion_candidates": stable_candidates,
                "report": str(REPORT),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
