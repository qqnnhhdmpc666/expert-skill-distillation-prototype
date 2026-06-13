from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
JSON_OUT = ROOT / "outputs" / "validation" / "promotion_mechanism_fairness_audit.json"
MD_OUT = ROOT / "reports" / "PROMOTION_MECHANISM_FAIRNESS_AUDIT.md"


def mechanism_rows() -> list[dict[str, Any]]:
    return [
        {
            "mechanism": "reward_delta_only",
            "input_bundle": ["A1 pass", "A2 pass"],
            "fairness_role": "intentionally weak baseline",
            "strawman_risk": "medium",
            "known_blind_spots": ["no repair attribution", "no scope", "no failure origin"],
            "verdict": "Keep only as a lower-bound baseline.",
        },
        {
            "mechanism": "gate_only",
            "input_bundle": ["gate decision"],
            "fairness_role": "ablation baseline for trusting the repair gate alone",
            "strawman_risk": "medium",
            "known_blind_spots": ["misses behavior gap", "misses no-op repair when gate accepts"],
            "verdict": "Keep only as a gate-ablation baseline.",
        },
        {
            "mechanism": "weighted_validity_score",
            "input_bundle": ["integrity", "behavior", "robustness"],
            "fairness_role": "reasonable score-based baseline",
            "strawman_risk": "low-medium",
            "known_blind_spots": ["can average away hard blockers", "scope is external to score"],
            "verdict": "Add a future vetoed-weighted variant for a stronger baseline.",
        },
        {
            "mechanism": "pareto_conservative",
            "input_bundle": ["integrity", "behavior", "robustness", "dominance regressions"],
            "fairness_role": "strong conservative baseline",
            "strawman_risk": "low",
            "known_blind_spots": ["less explicit failure-origin and scope language than QGSE"],
            "verdict": "Treat as the strongest current baseline, not a weak strawman.",
        },
        {
            "mechanism": "qgse_protocol",
            "input_bundle": ["integrity", "behavior", "robustness", "promotion level", "claim scope", "failure origin"],
            "fairness_role": "current grounded-label best",
            "strawman_risk": "n/a",
            "known_blind_spots": ["depends on current labels", "not externally/human validated"],
            "verdict": "Use as current default, with boundary.",
        },
        {
            "mechanism": "qgse_pareto_protocol",
            "input_bundle": ["QGSE bundle", "dominance regressions"],
            "fairness_role": "next candidate mechanism",
            "strawman_risk": "n/a",
            "known_blind_spots": ["currently strongest on synthetic challenge set only"],
            "verdict": "Advance as candidate, not final mechanism.",
        },
    ]


def main() -> int:
    payload = {
        "run_id": "promotion_mechanism_fairness_audit_001",
        "question": "Is the mechanism comparison fair, or did it use weak baselines?",
        "summary": {
            "same_evidence_bundle": "partially",
            "reason": "All mechanisms are evaluated on the same cards/challenge cases, but richer mechanisms intentionally consume richer fields such as failure_origin and claim_scope.",
            "main_risk": "QGSE and QGSE-Pareto may appear stronger because the challenge fields were designed around failure-origin and scope discipline.",
            "mitigation": "Keep Pareto conservative and future vetoed-weighted-score as stronger baselines; expand to artifact-backed and human-labeled challenges.",
        },
        "mechanisms": mechanism_rows(),
        "next_actions": [
            "Add vetoed_weighted_score baseline.",
            "Evaluate on artifact-backed challenge set.",
            "Add hidden/human usefulness labels before final mechanism claims.",
        ],
    }
    JSON_OUT.parent.mkdir(parents=True, exist_ok=True)
    JSON_OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    lines = [
        "# Promotion Mechanism Fairness Audit",
        "",
        f"Question: {payload['question']}",
        "",
        f"- Same evidence bundle: `{payload['summary']['same_evidence_bundle']}`",
        f"- Main risk: {payload['summary']['main_risk']}",
        f"- Mitigation: {payload['summary']['mitigation']}",
        "",
        "| Mechanism | Role | Strawman risk | Verdict |",
        "|---|---|---|---|",
    ]
    for row in payload["mechanisms"]:
        lines.append(f"| {row['mechanism']} | {row['fairness_role']} | {row['strawman_risk']} | {row['verdict']} |")
    lines.extend(["", "## Next Actions", ""])
    for item in payload["next_actions"]:
        lines.append(f"- {item}")
    lines.append("")
    MD_OUT.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print(json.dumps({"json": str(JSON_OUT), "report": str(MD_OUT)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
