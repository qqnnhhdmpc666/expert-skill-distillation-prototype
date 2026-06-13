from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src"
import sys

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from skill_deployment import CAPABILITY_SPECS, ControlledTaskCase, select_controlled_task_cases


DATA_ROOT = ROOT / "data" / "task_cases"
GENERALIZATION_RUN_ROOT = ROOT / "runs" / "generalization"
OUTPUT_ROOT = ROOT / "outputs" / "skill_lifecycle_evidence"
VALIDATION_ROOT = ROOT / "outputs" / "validation"
REPORTS_ROOT = ROOT / "reports"


CAPABILITY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "UPLOAD_TYPE_MAGIC": ("content validation", "mime", "magic", "extension"),
    "UPLOAD_PATH_ISOLATION": ("path isolation", "non-public storage", "storage"),
    "UPLOAD_AUDIT_RETENTION": ("audit retention", "audit", "retention"),
    "AUTH_SCOPE_MATRIX": ("role/scope authorization", "role", "scope"),
    "AUTH_OBJECT_OWNERSHIP": ("object ownership", "ownership", "tenant boundary"),
    "AUTH_ERROR_ENVELOPE": ("error envelope", "error", "envelope"),
    "CONFIG_AUDIT_EXPORT": ("audit retention", "export sinks", "export sink", "audit"),
    "CONFIG_ENV_GUARD": ("separate prod from dev/test", "prod", "dev/test", "debug state"),
    "API_SCHEMA_CONTRACT": ("strict json report contract", "json report contract", "evidence spans"),
    "API_OVERBROAD_RISK": ("overbroad generic findings", "overbroad", "generic findings"),
    "DATA_REQUIRED_FIELD_COVERAGE": ("missing-column issues", "required field", "row sample"),
    "DATA_TEMPORAL_SPLIT_GUARD": ("temporal split hygiene", "cutoff rule", "offending row id"),
    "DATA_LABEL_ENUM_ALIGNMENT": ("label values", "declared contract", "unexpected label token"),
}

LIVE_LOOP_SPECS: tuple[dict[str, str], ...] = (
    {
        "run_id": "harbor_llm_repair_loop_upload_001",
        "kind": "harbor_llm_repair_loop",
        "path": str(ROOT / "outputs" / "harbor_llm_repair_loop_upload_001"),
    },
    {
        "run_id": "harbor_llm_repair_loop_config_001",
        "kind": "harbor_llm_repair_loop",
        "path": str(ROOT / "outputs" / "harbor_llm_repair_loop_config_001"),
    },
    {
        "run_id": "live_llm_repair_loop_upload_001",
        "kind": "local_live_llm_repair_loop",
        "path": str(ROOT / "outputs" / "live_llm_repair_loop_upload_001"),
    },
    {
        "run_id": "live_llm_repair_loop_data_quality_001",
        "kind": "local_live_llm_repair_loop",
        "path": str(ROOT / "outputs" / "live_llm_repair_loop_data_quality_001"),
    },
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> Any:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def split_clauses(text: str) -> list[str]:
    normalized = " ".join(text.split())
    if not normalized:
        return []
    sentences = re.split(r"[.;]\s+", normalized)
    clauses: list[str] = []
    for sentence in sentences:
        parts = re.split(r",|\band\b", sentence)
        for part in parts:
            clause = part.strip(" -")
            if clause:
                clauses.append(clause)
    return clauses or [normalized]


def find_source_span(text: str, capability_id: str) -> tuple[str, str, list[str]]:
    keywords = [item.lower() for item in CAPABILITY_KEYWORDS.get(capability_id, ())]
    clauses = split_clauses(text)
    best_clause = text.strip()
    best_hits: list[str] = []
    best_score = -1
    for clause in clauses:
        lower_clause = clause.lower()
        hits = [keyword for keyword in keywords if keyword in lower_clause]
        score = len(hits)
        if score > best_score:
            best_score = score
            best_clause = clause
            best_hits = hits
    if best_score > 0:
        return best_clause, "clause_keyword_match", best_hits
    return text.strip(), "full_note_fallback", []


def relative_to_root(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def capability_provenance_rows(case: ControlledTaskCase, run_dir: Path, manifest_v2: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    source_mapping = read_json(run_dir / "provenance" / "source_to_skill_mapping.json") or []
    a1_report = read_json(run_dir / "verifier" / "A1_report.json") or {}
    repair_decision = read_json(run_dir / "revision" / "repair_decision.json") or {}
    gate_decision = read_json(run_dir / "revision" / "gate_decision.json") or {}
    after_capabilities = list(manifest_v2.get("capabilities", [])) or list(case.expected_capabilities)

    extracted_candidates: list[dict[str, Any]] = []
    provenance: list[dict[str, Any]] = []
    for index, capability_id in enumerate(case.expected_capabilities, start=1):
        spec = CAPABILITY_SPECS[capability_id]
        source_span, resolution, keyword_hits = find_source_span(case.expert_material, capability_id)
        mapping_row = next(
            (
                item
                for item in source_mapping
                if item.get("capability_id") == capability_id
                or item.get("rule_id") == capability_id
                or str(item.get("skill_file", "")).endswith(f"#{capability_id}")
            ),
            {},
        )
        selected_in_v1 = capability_id in case.v1_capabilities
        selected_in_v2 = capability_id in after_capabilities
        repair_added = capability_id not in case.v1_capabilities and capability_id in after_capabilities
        extracted_candidates.append(
            {
                "candidate_id": f"cand_{index:02d}",
                "natural_language_capability": spec.title,
                "normalized_capability_id": capability_id,
                "source_span": source_span,
                "projection_method": resolution,
                "keyword_hits": keyword_hits,
                "selected_in_v1": selected_in_v1,
                "selected_in_v2": selected_in_v2,
            }
        )
        provenance.append(
            {
                "capability_id": capability_id,
                "title": spec.title,
                "source_span": source_span,
                "source_span_resolution": resolution,
                "keyword_hits": keyword_hits,
                "skill_v1_included": selected_in_v1,
                "skill_v2_included": selected_in_v2,
                "added_by_repair": repair_added,
                "a1_feedback_type": a1_report.get("feedback_type", "unknown"),
                "repair_action": repair_decision.get("repair_action", "unknown"),
                "gate_decision": gate_decision.get("decision", "unknown"),
                "mapping_artifact": mapping_row or None,
                "justification": (
                    "kept in compact skill_v1"
                    if selected_in_v1
                    else (
                        "promoted into skill_v2 after verifier feedback"
                        if repair_added
                        else "retained only as an expected capability in this controlled task"
                    )
                ),
            }
        )
    trace = {
        "case_id": case.case_id,
        "task_family": case.task_family,
        "method": "controlled keyword projection from expert material into normalized capability registry",
        "boundary": "This is provenance for a controlled task family. It is artifact-backed, but it is not a claim of open-world expert-material induction.",
        "steps": [
            {
                "stage": "ingest_expert_material",
                "artifact": relative_to_root(run_dir / "source_materials" / "expert_material.md"),
                "note": "Scenario-conditioned expert note is loaded as the source of distillation.",
            },
            {
                "stage": "project_natural_language_candidates",
                "artifact": "extracted_candidates.json",
                "note": "Candidate capabilities are projected from expert clauses before normalization.",
            },
            {
                "stage": "normalize_to_capability_registry",
                "artifact": "capability_provenance.json",
                "note": "Candidates are normalized to shared capability ids reused by execution, verifier, and repair.",
            },
            {
                "stage": "compile_skill_v1",
                "artifact": relative_to_root(run_dir / "skills" / "skill_v1" / "manifest.json"),
                "note": "Compact v1 selects a subset of capabilities for the first execution attempt.",
            },
            {
                "stage": "verifier_feedback",
                "artifact": relative_to_root(run_dir / "verifier" / "A1_report.json"),
                "note": "Posterior feedback determines whether evolution is needed.",
            },
            {
                "stage": "compile_skill_v2",
                "artifact": relative_to_root(run_dir / "skills" / "skill_v2" / "manifest.json"),
                "note": "Typed repair updates capability coverage, boundary logic, or output contract.",
            },
        ],
    }
    return extracted_candidates, provenance, trace


def build_evolution_lessons(case: ControlledTaskCase, run_dir: Path, manifest_v2: dict[str, Any]) -> dict[str, Any]:
    a1_report = read_json(run_dir / "verifier" / "A1_report.json") or {}
    a2_report = read_json(run_dir / "verifier" / "A2_report.json") or {}
    repair = read_json(run_dir / "revision" / "repair_decision.json") or {}
    lessons_by_feedback = {
        "missing_capability": "Capability coverage can be compact in v1, but missing critical capability ids must become explicit repair targets.",
        "ownership_boundary_missing": "Boundary-oriented failures are not fixed by adding more findings alone; the skill must force ownership/tenant checks into evidence collection.",
        "output_contract_error": "Capability presence is insufficient when the output contract is loose; repair must tighten how evidence and fixes are emitted.",
        "false_positive_risk": "Skills need negative guidance as well as positive guidance so repaired versions avoid widening scope and hallucinating findings.",
        "target_context_missing": "Observation steps must be first-class repair operators because many failures are caused by weak target grounding rather than wrong rule selection.",
        "pass": "This controlled case did not require posterior evolution after v1.",
    }
    return {
        "case_id": case.case_id,
        "a1_failure_pattern": a1_report.get("feedback_type", "unknown"),
        "a2_outcome": "pass" if a2_report.get("pass") else "fail",
        "repair_action": repair.get("repair_action", "unknown"),
        "contrastive_lesson": lessons_by_feedback.get(
            a1_report.get("feedback_type", "unknown"),
            "Posterior evidence should remain the trigger for evolution; unsupported patterns must stay as audit evidence instead of being silently promoted.",
        ),
        "persistent_memory_note": {
            "before_capabilities": list(case.v1_capabilities),
            "after_capabilities": list(manifest_v2.get("capabilities", [])),
            "operator_id": repair.get("operator_id"),
            "preferred_action": repair.get("preferred_action"),
        },
    }


def coverage_score(report: dict[str, Any]) -> float:
    return float((report.get("scores") or {}).get("capability_coverage_score", 0.0))


def build_generalization_bundle(case: ControlledTaskCase) -> dict[str, Any]:
    run_dir = GENERALIZATION_RUN_ROOT / case.case_id
    out_dir = OUTPUT_ROOT / "generalization" / case.case_id
    distill_dir = out_dir / "distillation_bundle"
    trajectory_dir = out_dir / "trajectory_bundle"

    manifest_v1 = read_json(run_dir / "skills" / "skill_v1" / "manifest.json") or {}
    manifest_v2 = read_json(run_dir / "skills" / "skill_v2" / "manifest.json") or {}
    skill_v1 = (run_dir / "skills" / "skill_v1" / "SKILL.md").read_text(encoding="utf-8")
    skill_v2 = (run_dir / "skills" / "skill_v2" / "SKILL.md").read_text(encoding="utf-8")
    a0_output = read_json(run_dir / "attempts" / "A0" / "agent_output.json") or {}
    a1_output = read_json(run_dir / "attempts" / "A1" / "agent_output.json") or {}
    a2_output = read_json(run_dir / "attempts" / "A2" / "agent_output.json") or {}
    a0_report = read_json(run_dir / "verifier" / "A0_report.json") or {}
    a1_report = read_json(run_dir / "verifier" / "A1_report.json") or {}
    a2_report = read_json(run_dir / "verifier" / "A2_report.json") or {}
    repair = read_json(run_dir / "revision" / "repair_decision.json") or {}
    gate = read_json(run_dir / "revision" / "gate_decision.json") or {}
    extracted_candidates, provenance, distillation_trace = capability_provenance_rows(case, run_dir, manifest_v2)
    evolution_lessons = build_evolution_lessons(case, run_dir, manifest_v2)

    write_text(distill_dir / "source_material.md", case.expert_material + "\n")
    write_json(distill_dir / "extracted_candidates.json", extracted_candidates)
    write_json(distill_dir / "capability_provenance.json", provenance)
    write_json(distill_dir / "skill_manifest_v1.json", manifest_v1)
    write_json(distill_dir / "skill_manifest_v2.json", manifest_v2)
    write_text(distill_dir / "SKILL_v1.md", skill_v1)
    write_text(distill_dir / "SKILL_v2.md", skill_v2)
    write_json(distill_dir / "distillation_trace.json", distillation_trace)
    write_json(distill_dir / "evolution_lessons.json", evolution_lessons)

    trace_a1 = read_jsonl(run_dir / "attempts" / "A1" / "trace.jsonl")
    trace_a2 = read_jsonl(run_dir / "attempts" / "A2" / "trace.jsonl")
    trajectory_rows: list[dict[str, Any]] = [
        {
            "stage": "source_ingest",
            "event": "load_expert_material",
            "artifact": relative_to_root(run_dir / "source_materials" / "expert_material.md"),
        },
        {
            "stage": "compile",
            "event": "skill_v1_compiled",
            "artifact": relative_to_root(run_dir / "skills" / "skill_v1" / "manifest.json"),
            "capabilities": manifest_v1.get("capabilities", []),
        },
    ]
    trajectory_rows.extend({"stage": "A1", **row} for row in trace_a1)
    trajectory_rows.append(
        {
            "stage": "A1",
            "event": "verifier_feedback",
            "feedback_type": a1_report.get("feedback_type"),
            "scores": a1_report.get("scores", {}),
        }
    )
    trajectory_rows.append(
        {
            "stage": "revision",
            "event": "typed_repair",
            "repair_action": repair.get("repair_action"),
            "gate_decision": gate.get("decision"),
            "before_capabilities": repair.get("before_capabilities", []),
            "after_capabilities": repair.get("after_capabilities", []),
        }
    )
    trajectory_rows.extend({"stage": "A2", **row} for row in trace_a2)
    trajectory_rows.append(
        {
            "stage": "A2",
            "event": "verifier_feedback",
            "feedback_type": a2_report.get("feedback_type"),
            "scores": a2_report.get("scores", {}),
            "pass": a2_report.get("pass"),
        }
    )
    write_jsonl(trajectory_dir / "trajectory.jsonl", trajectory_rows)
    write_json(
        trajectory_dir / "target_reads.json",
        {
            "A1": [row for row in trace_a1 if row.get("event") == "read_target"],
            "A2": [row for row in trace_a2 if row.get("event") == "read_target"],
        },
    )
    write_json(
        trajectory_dir / "skill_reads.json",
        {
            "A1": [row for row in trace_a1 if row.get("event") == "read_skill"],
            "A2": [row for row in trace_a2 if row.get("event") == "read_skill"],
        },
    )
    write_json(
        trajectory_dir / "agent_steps.json",
        {
            "A0": {"stdout_path": relative_to_root(run_dir / "attempts" / "A0" / "stdout.log")},
            "A1": {
                "stdout_path": relative_to_root(run_dir / "attempts" / "A1" / "stdout.log"),
                "stderr_path": relative_to_root(run_dir / "attempts" / "A1" / "stderr.log"),
            },
            "A2": {
                "stdout_path": relative_to_root(run_dir / "attempts" / "A2" / "stdout.log"),
                "stderr_path": relative_to_root(run_dir / "attempts" / "A2" / "stderr.log"),
            },
        },
    )
    write_json(trajectory_dir / "raw_output.json", {"A0": a0_output, "A1": a1_output, "A2": a2_output})
    write_json(trajectory_dir / "verifier_feedback.json", {"A0": a0_report, "A1": a1_report, "A2": a2_report})
    write_json(trajectory_dir / "repair_patch.json", {"patch_plan": repair, "gate_decision": gate})
    write_json(
        trajectory_dir / "qualification_decision.json",
        {
            "decision": "candidate_for_controlled_promotion" if a2_report.get("pass") else "do_not_promote",
            "scope": "controlled offline evidence only",
            "reason": "This bundle is pre-promotion lifecycle evidence. Formal promotion remains governed by qualification cards and broader robustness checks.",
        },
    )
    write_json(
        trajectory_dir / "summary.json",
        {
            "case_id": case.case_id,
            "task_family": case.task_family,
            "a0_pass": a0_report.get("pass"),
            "a1_pass": a1_report.get("pass"),
            "a2_pass": a2_report.get("pass"),
            "a0_coverage": coverage_score(a0_report),
            "a1_coverage": coverage_score(a1_report),
            "a2_coverage": coverage_score(a2_report),
            "feedback_type": a1_report.get("feedback_type"),
            "repair_action": repair.get("repair_action"),
            "boundary": "Controlled generalization-suite evidence. The trajectory bundle is standardized, but it is not a live Harbor or open-world execution trace.",
        },
    )
    return {
        "case_id": case.case_id,
        "task_family": case.task_family,
        "bundle_dir": relative_to_root(out_dir),
        "distillation_bundle": relative_to_root(distill_dir),
        "trajectory_bundle": relative_to_root(trajectory_dir),
        "feedback_type": a1_report.get("feedback_type"),
        "repair_action": repair.get("repair_action"),
        "a2_pass": a2_report.get("pass"),
        "net_effect": {
            "a0_coverage": coverage_score(a0_report),
            "a1_coverage": coverage_score(a1_report),
            "a2_coverage": coverage_score(a2_report),
            "reward_proxy_delta": round(coverage_score(a2_report) - coverage_score(a1_report), 4),
        },
    }


def build_live_loop_bundle(spec: dict[str, str]) -> dict[str, Any] | None:
    loop_dir = Path(spec["path"])
    if not loop_dir.exists():
        return None
    out_dir = OUTPUT_ROOT / "live_loops" / spec["run_id"] / "trajectory_bundle"
    summary = read_json(loop_dir / "summary.json") or {}
    validity_card = read_json(loop_dir / "validity_card.json") or {}
    a1_report = read_json(loop_dir / "A1" / "verifier_report.json") or {}
    a2_report = read_json(loop_dir / "A2" / "verifier_report.json") or {}
    patch_plan = read_json(loop_dir / "revision" / "patch_plan.json") or {}
    gate_decision = read_json(loop_dir / "revision" / "gate_decision.json") or {}
    target_reads_a1 = read_json(loop_dir / "A1" / "target_reads.json") or {}
    target_reads_a2 = read_json(loop_dir / "A2" / "target_reads.json") or {}
    skill_manifest_a1 = read_json(loop_dir / "A1" / "skill_manifest.json") or {}
    skill_manifest_a2 = read_json(loop_dir / "A2" / "skill_manifest.json") or {}
    model_calls_a1 = read_json(loop_dir / "A1" / "model_calls.json") or {}
    model_calls_a2 = read_json(loop_dir / "A2" / "model_calls.json") or {}
    process_a1 = read_json(loop_dir / "A1" / "process.json") or {}
    process_a2 = read_json(loop_dir / "A2" / "process.json") or {}
    security_report_a1 = read_json(loop_dir / "A1" / "security_report.json") or {}
    security_report_a2 = read_json(loop_dir / "A2" / "security_report.json") or {}

    a1_summary = dict(summary.get("A1", {})) if isinstance(summary.get("A1"), dict) else {}
    a2_summary = dict(summary.get("A2", {})) if isinstance(summary.get("A2"), dict) else {}

    def merged_verifier_view(report: dict[str, Any], stage_summary: dict[str, Any]) -> dict[str, Any]:
        merged = dict(report)
        if "pass" not in merged and "pass" in stage_summary:
            merged["pass"] = stage_summary.get("pass")
        if "feedback_type" not in merged:
            if stage_summary.get("feedback_type"):
                merged["feedback_type"] = stage_summary.get("feedback_type")
            elif merged.get("schema_errors"):
                merged["feedback_type"] = "output_contract_error"
            elif merged.get("missing"):
                merged["feedback_type"] = "missing_capability"
        if "scores" not in merged and stage_summary:
            merged["scores"] = {
                "capability_coverage_score": stage_summary.get("coverage"),
                "evidence_binding_score": stage_summary.get("evidence_binding"),
                "output_contract_score": stage_summary.get("schema_correctness"),
                "regression_safety_score": stage_summary.get("regression_safety"),
            }
        return merged

    a1_view = merged_verifier_view(a1_report, a1_summary)
    a2_view = merged_verifier_view(a2_report, a2_summary)

    trajectory_rows = [
        {
            "stage": "A1",
            "event": "skill_loaded",
            "skill_manifest_artifact": relative_to_root(loop_dir / "A1" / "skill_manifest.json"),
            "capabilities": skill_manifest_a1.get("capabilities", []),
        },
        {
            "stage": "A1",
            "event": "target_read_set",
            "read_files": target_reads_a1.get("read_files", []),
            "skill_files": target_reads_a1.get("skill_files", []),
        },
        {
            "stage": "A1",
            "event": "agent_run_completed",
            "process": process_a1,
            "model_call_present": bool(model_calls_a1),
        },
        {
            "stage": "A1",
            "event": "verifier_feedback",
            "feedback_type": a1_view.get("feedback_type"),
            "pass": a1_view.get("pass"),
            "scores": a1_view.get("scores", {}),
        },
        {
            "stage": "revision",
            "event": "typed_repair",
            "repair_action": patch_plan.get("repair_action"),
            "gate_decision": gate_decision.get("decision"),
        },
        {
            "stage": "A2",
            "event": "skill_loaded",
            "skill_manifest_artifact": relative_to_root(loop_dir / "A2" / "skill_manifest.json"),
            "capabilities": skill_manifest_a2.get("capabilities", []),
        },
        {
            "stage": "A2",
            "event": "target_read_set",
            "read_files": target_reads_a2.get("read_files", []),
            "skill_files": target_reads_a2.get("skill_files", []),
        },
        {
            "stage": "A2",
            "event": "agent_run_completed",
            "process": process_a2,
            "model_call_present": bool(model_calls_a2),
        },
        {
            "stage": "A2",
            "event": "verifier_feedback",
            "feedback_type": a2_view.get("feedback_type"),
            "pass": a2_view.get("pass"),
            "scores": a2_view.get("scores", {}),
        },
    ]
    write_jsonl(out_dir / "trajectory.jsonl", trajectory_rows)
    write_json(out_dir / "target_reads.json", {"A1": target_reads_a1, "A2": target_reads_a2})
    write_json(out_dir / "skill_reads.json", {"A1": skill_manifest_a1, "A2": skill_manifest_a2})
    write_json(out_dir / "agent_steps.json", {"A1": process_a1, "A2": process_a2, "model_calls": {"A1": model_calls_a1, "A2": model_calls_a2}})
    write_json(out_dir / "raw_output.json", {"A1": security_report_a1, "A2": security_report_a2})
    write_json(out_dir / "verifier_feedback.json", {"A1": a1_view, "A2": a2_view})
    write_json(out_dir / "repair_patch.json", {"patch_plan": patch_plan, "gate_decision": gate_decision})
    write_json(
        out_dir / "qualification_decision.json",
        {
            "card_id": validity_card.get("card_id"),
            "claim_boundary": validity_card.get("claim_boundary"),
            "summary": validity_card.get("summary"),
        },
    )
    write_json(
        out_dir / "summary.json",
        {
            "run_id": spec["run_id"],
            "kind": spec["kind"],
            "source_artifact": relative_to_root(loop_dir),
            "a1_pass": a1_view.get("pass"),
            "a2_pass": a2_view.get("pass"),
            "feedback_type": a1_view.get("feedback_type"),
            "repair_action": patch_plan.get("repair_action"),
            "boundary": summary.get("boundary") or validity_card.get("claim_boundary"),
        },
    )
    return {
        "run_id": spec["run_id"],
        "kind": spec["kind"],
        "trajectory_bundle": relative_to_root(out_dir),
        "a1_pass": a1_view.get("pass"),
        "a2_pass": a2_view.get("pass"),
        "feedback_type": a1_view.get("feedback_type"),
        "repair_action": patch_plan.get("repair_action"),
    }


def build_net_effect_matrix(rows: list[dict[str, Any]]) -> dict[str, Any]:
    matrix = []
    for row in rows:
        matrix.append(
            {
                "case_id": row["case_id"],
                "task_family": row["task_family"],
                "no_skill_coverage": row["net_effect"]["a0_coverage"],
                "skill_v1_coverage": row["net_effect"]["a1_coverage"],
                "skill_v2_coverage": row["net_effect"]["a2_coverage"],
                "skill_v2_minus_v1": round(row["net_effect"]["a2_coverage"] - row["net_effect"]["a1_coverage"], 4),
                "skill_v2_minus_no_skill": round(row["net_effect"]["a2_coverage"] - row["net_effect"]["a0_coverage"], 4),
                "feedback_type": row["feedback_type"],
                "repair_action": row["repair_action"],
                "a2_pass": row["a2_pass"],
            }
        )
    promoted = [item for item in matrix if item["a2_pass"]]
    return {
        "run_id": "skill_net_effect_matrix_001",
        "created_at": utc_now(),
        "case_count": len(matrix),
        "rows": matrix,
        "summary": {
            "all_a2_pass": all(item["a2_pass"] for item in matrix),
            "average_v1_to_v2_gain": round(sum(item["skill_v2_minus_v1"] for item in matrix) / len(matrix), 4) if matrix else 0.0,
            "average_no_skill_to_v2_gain": round(sum(item["skill_v2_minus_no_skill"] for item in matrix) / len(matrix), 4) if matrix else 0.0,
            "promoted_case_count": len(promoted),
        },
        "boundary": "This is a controlled net-effect matrix over the shared offline suite. It measures verifier-scored improvement, not open-world utility.",
    }


def render_status_report(index_payload: dict[str, Any], net_effect: dict[str, Any]) -> str:
    generalization_rows = index_payload.get("generalization", [])
    live_rows = index_payload.get("live_loops", [])
    lines = [
        "# Skill Lifecycle Evidence Status",
        "",
        f"- Updated: `{utc_now()}`",
        f"- Generalization cases with standardized distillation + trajectory bundles: `{len(generalization_rows)}`",
        f"- Live repair loops with standardized trajectory bundles: `{len(live_rows)}`",
        f"- Average v1->v2 gain (controlled verifier coverage): `{net_effect['summary']['average_v1_to_v2_gain']}`",
        "",
        "## What was added",
        "",
        "- A standardized distillation bundle for each controlled task case.",
        "- A standardized trajectory bundle for each controlled generalization run.",
        "- A standardized trajectory bundle for Harbor/local live repair loops where A1, revision, and A2 already exist.",
        "- A verifier-scored no-skill / skill-v1 / skill-v2 net-effect matrix.",
        "",
        "## Why this matters",
        "",
        "- The mainline is now easier to audit as `expert material -> normalized capabilities -> skill_v1 -> execution -> verifier feedback -> repair -> skill_v2`.",
        "- Provenance is no longer only implied by scattered files; it is exposed as capability-level provenance rows with explicit source spans and repair attribution.",
        "- Trajectory evidence is no longer only a directory tree; it is normalized into bundle files that make A1/A2 comparison easier to inspect and export.",
        "",
        "## Controlled boundaries",
        "",
        "- Provenance extraction is still controlled keyword projection over curated task-case expert notes, not broad open-world expert-material induction.",
        "- Offline trajectory bundles are standardized artifact bundles, not full SPARK-style live command/stdout trajectories.",
        "- Harbor/local live bundles are still narrow scenario evidence rather than broad multi-task autonomous proof.",
        "",
        "## Generalization bundle index",
        "",
        "| Case | Family | Feedback | Repair | A2 | Bundle |",
        "|---|---|---|---|---|---|",
    ]
    for row in generalization_rows:
        lines.append(
            f"| {row['case_id']} | {row['task_family']} | {row['feedback_type']} | {row['repair_action']} | {row['a2_pass']} | `{row['bundle_dir']}` |"
        )
    lines.extend(
        [
            "",
            "## Live loop bundle index",
            "",
            "| Run | Kind | Feedback | Repair | A2 | Bundle |",
            "|---|---|---|---|---|---|",
        ]
    )
    for row in live_rows:
        lines.append(
            f"| {row['run_id']} | {row['kind']} | {row['feedback_type']} | {row['repair_action']} | {row['a2_pass']} | `{row['trajectory_bundle']}` |"
        )
    lines.extend(
        [
            "",
            "## Net-effect reading",
            "",
            f"- All controlled A2 reruns pass: `{net_effect['summary']['all_a2_pass']}`",
            f"- Average no-skill -> v2 gain: `{net_effect['summary']['average_no_skill_to_v2_gain']}`",
            f"- Matrix artifact: `outputs/validation/skill_net_effect_matrix.json`",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    cases = select_controlled_task_cases(DATA_ROOT, "upload,auth,config,api_review,data_quality")
    generalization_rows = [build_generalization_bundle(case) for case in cases]
    live_rows = [row for row in (build_live_loop_bundle(spec) for spec in LIVE_LOOP_SPECS) if row is not None]
    net_effect = build_net_effect_matrix(generalization_rows)
    index_payload = {
        "run_id": "skill_lifecycle_evidence_001",
        "created_at": utc_now(),
        "generalization": generalization_rows,
        "live_loops": live_rows,
    }
    write_json(OUTPUT_ROOT / "index.json", index_payload)
    write_json(VALIDATION_ROOT / "skill_net_effect_matrix.json", net_effect)
    write_text(REPORTS_ROOT / "SKILL_LIFECYCLE_EVIDENCE_STATUS.md", render_status_report(index_payload, net_effect))
    print(
        json.dumps(
            {
                "index": relative_to_root(OUTPUT_ROOT / "index.json"),
                "net_effect": relative_to_root(VALIDATION_ROOT / "skill_net_effect_matrix.json"),
                "status_report": relative_to_root(REPORTS_ROOT / "SKILL_LIFECYCLE_EVIDENCE_STATUS.md"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
