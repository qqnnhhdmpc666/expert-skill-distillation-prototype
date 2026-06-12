from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .schemas import ExecutionReport, GateDecision, PatchPlan, SkillPackage, VerifierReport
from .token_budget import estimate_tokens


EVIDENCE_BUNDLE_FILES = (
    "trajectory.jsonl",
    "target_reads.json",
    "skill_reads.json",
    "verifier_feedback.json",
    "repair_patch.json",
    "qualification_decision.json",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def append_jsonl(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def read_text_if_exists(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def score_from_verifier(report: VerifierReport | dict[str, Any]) -> float:
    payload = report.to_dict() if isinstance(report, VerifierReport) else report
    scores = dict(payload.get("scores", {}))
    if bool(payload.get("pass", payload.get("passed", False))):
        pass_bonus = 1.0
    else:
        pass_bonus = 0.0
    values = [
        float(scores.get("capability_coverage_score", 0.0)),
        float(scores.get("evidence_binding_score", 0.0)),
        float(scores.get("output_contract_score", 0.0)),
        float(scores.get("regression_safety_score", 0.0)),
        pass_bonus,
    ]
    return round(sum(values) / len(values), 4)


def false_positive_count(report: VerifierReport | dict[str, Any]) -> int:
    payload = report.to_dict() if isinstance(report, VerifierReport) else report
    return len(payload.get("false_positive_capabilities", []))


def skill_cost(skill: SkillPackage | None, skill_text: str = "") -> int:
    if skill is None:
        return 0
    content = skill_text or json.dumps(skill.to_dict(), ensure_ascii=False, sort_keys=True)
    return estimate_tokens(content)


def write_evidence_bundle(
    bundle_dir: Path,
    *,
    case_id: str,
    backend: str,
    variant: str,
    target_text: str,
    skill: SkillPackage | None,
    skill_text: str,
    execution: ExecutionReport | dict[str, Any],
    verifier: VerifierReport | dict[str, Any],
    patch: PatchPlan | dict[str, Any] | None = None,
    qualification: GateDecision | dict[str, Any] | None = None,
    status: str = "completed",
    provenance: dict[str, Any] | None = None,
) -> dict[str, Any]:
    execution_payload = execution.to_dict() if isinstance(execution, ExecutionReport) else execution
    verifier_payload = verifier.to_dict() if isinstance(verifier, VerifierReport) else verifier
    patch_payload = patch.to_dict() if isinstance(patch, PatchPlan) else (patch or {})
    qualification_payload = (
        qualification.to_dict() if isinstance(qualification, GateDecision) else (qualification or {"decision": "not_applicable"})
    )
    bundle_dir.mkdir(parents=True, exist_ok=True)
    trajectory_path = bundle_dir / "trajectory.jsonl"
    if trajectory_path.exists():
        trajectory_path.unlink()
    append_jsonl(
        trajectory_path,
        {
            "event": "variant_started",
            "created_at": utc_now(),
            "case_id": case_id,
            "backend": backend,
            "variant": variant,
            "status": status,
        },
    )
    for finding in execution_payload.get("findings", []):
        append_jsonl(
            trajectory_path,
            {
                "event": "finding",
                "capability_id": finding.get("capability_id"),
                "evidence_span": finding.get("evidence_span"),
                "payload": finding,
            },
        )
    append_jsonl(
        trajectory_path,
        {
            "event": "verifier_feedback",
            "feedback_type": verifier_payload.get("feedback_type"),
            "passed": verifier_payload.get("pass", verifier_payload.get("passed", False)),
        },
    )
    write_json(
        bundle_dir / "target_reads.json",
        {
            "case_id": case_id,
            "target_digest": {
                "chars": len(target_text),
                "preview": target_text[:500],
            },
        },
    )
    write_json(
        bundle_dir / "skill_reads.json",
        {
            "variant": variant,
            "skill": skill.to_dict() if skill is not None else None,
            "skill_text_chars": len(skill_text),
            "skill_text_preview": skill_text[:500],
            "provenance": dict(provenance or {}),
        },
    )
    write_json(bundle_dir / "raw_output.json", execution_payload)
    write_json(bundle_dir / "verifier_feedback.json", verifier_payload)
    write_json(bundle_dir / "repair_patch.json", patch_payload)
    write_json(bundle_dir / "qualification_decision.json", qualification_payload)
    manifest = {
        "bundle_id": f"{case_id}_{variant}_{backend}",
        "created_at": utc_now(),
        "case_id": case_id,
        "backend": backend,
        "variant": variant,
        "status": status,
        "verifier_result": "pass" if bool(verifier_payload.get("pass", verifier_payload.get("passed", False))) else "fail",
        "verifier_feedback_type": verifier_payload.get("feedback_type"),
        "artifacts": ["raw_output.json", *EVIDENCE_BUNDLE_FILES],
        "score": score_from_verifier(verifier_payload),
        "token_cost_estimate": skill_cost(skill, skill_text),
        "safety_boundary": "defensive_review_only_no_exploit_generation",
    }
    if provenance:
        manifest["provenance"] = dict(provenance)
    write_json(bundle_dir / "summary.json", manifest)
    return manifest


@dataclass(frozen=True)
class MarginalUtilityResult:
    case_id: str
    backend: str
    variants: tuple[str, ...]
    scores: dict[str, float]
    costs: dict[str, int]
    false_positives: dict[str, int]
    metrics: dict[str, float]
    artifact_dir: str
    run_metadata: dict[str, dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "backend": self.backend,
            "variants": list(self.variants),
            "scores": dict(self.scores),
            "costs": dict(self.costs),
            "false_positives": dict(self.false_positives),
            "metrics": dict(self.metrics),
            "artifact_dir": self.artifact_dir,
            "run_metadata": dict(self.run_metadata),
        }


def build_marginal_utility_result(
    *,
    case_id: str,
    backend: str,
    variant_reports: dict[str, dict[str, Any]],
    variant_costs: dict[str, int],
    artifact_dir: Path,
    variant_metadata: dict[str, dict[str, Any]] | None = None,
) -> MarginalUtilityResult:
    required = ("no_skill", "skill_v1", "skill_v2", "upper_bound")
    scores = {variant: score_from_verifier(variant_reports[variant]) for variant in required}
    false_positives = {variant: false_positive_count(variant_reports[variant]) for variant in required}
    metrics = {
        "v2_over_v1_gain": round(scores["skill_v2"] - scores["skill_v1"], 4),
        "v2_over_no_skill_gain": round(scores["skill_v2"] - scores["no_skill"], 4),
        "gap_to_upper_bound": round(scores["upper_bound"] - scores["skill_v2"], 4),
        "cost_delta": float(variant_costs["skill_v2"] - variant_costs["skill_v1"]),
        "false_positive_delta": float(false_positives["skill_v2"] - false_positives["skill_v1"]),
        "metamorphic_delta": 0.0,
    }
    return MarginalUtilityResult(
        case_id=case_id,
        backend=backend,
        variants=required,
        scores=scores,
        costs=dict(variant_costs),
        false_positives=false_positives,
        metrics=metrics,
        artifact_dir=str(artifact_dir),
        run_metadata=dict(variant_metadata or {}),
    )
