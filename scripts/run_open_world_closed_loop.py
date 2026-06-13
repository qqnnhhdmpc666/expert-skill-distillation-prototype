from __future__ import annotations

import argparse
import difflib
import json
import os
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from skill_deployment import resolve_installed_skill, score_from_verifier  # noqa: E402
from skill_deployment.evidence import false_positive_count, write_json, write_text  # noqa: E402
from skill_deployment.install_state import load_active_pointer  # noqa: E402
from skill_deployment.openai_compat import call_chat_completion_json  # noqa: E402
from skill_deployment.schemas import SkillPackage  # noqa: E402

import scripts.run_defensive_security_mini_suite as mini  # noqa: E402
from scripts.run_external_generalization_validation import download_sources, materialize_cases  # noqa: E402
from scripts.run_open_world_distillation_validation import select_validation_cases  # noqa: E402


OUTPUT_ROOT = ROOT / "outputs" / "open_world_closed_loop"
SUMMARY_PATH = OUTPUT_ROOT / "open_world_closed_loop_summary.json"
REPORT = ROOT / "reports" / "OPEN_WORLD_CLOSED_LOOP_STATUS.md"
OPEN_WORLD_SUMMARY = ROOT / "outputs" / "open_world_distillation_validation" / "open_world_distillation_validation_summary.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def api_key_present() -> bool:
    return bool(os.environ.get("OPENAI_API_KEY"))


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_text(path: Path, default: str = "") -> str:
    if not path.exists():
        return default
    return path.read_text(encoding="utf-8-sig")


def excerpt(text: str, *, limit: int = 1200) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3].rstrip() + "..."


def source_failure_rows() -> list[dict[str, Any]]:
    summary = read_json(OPEN_WORLD_SUMMARY, {})
    return [row for row in summary.get("distilled_rows", []) if not row.get("effective_pass")]


def source_guard_rows() -> list[dict[str, Any]]:
    summary = read_json(OPEN_WORLD_SUMMARY, {})
    return [
        row
        for row in summary.get("distilled_rows", [])
        if row.get("effective_pass")
        and row.get("clean_or_negative")
        and row.get("task_family") == "config_security"
    ]


def load_cases() -> list[dict[str, Any]]:
    source_status = download_sources(OUTPUT_ROOT / "validation_sources")
    return select_validation_cases(materialize_cases(source_status))


def clone_package(base: SkillPackage, *, version: str) -> SkillPackage:
    metadata = json.loads(json.dumps(dict(base.metadata or {})))
    metadata["open_world_closed_loop"] = True
    metadata["candidate_generation_sources"] = ["open-world failure feedback", "public-material distilled skill text", "verifier feedback", "evidence summary"]
    metadata["verifier_only_oracle_fields_read"] = False
    return SkillPackage(
        skill_id=base.skill_id,
        version=version,
        task_family=base.task_family,
        capabilities=base.capabilities,
        output_contract=base.output_contract,
        trace_contract=base.trace_contract,
        metadata=metadata,
    )


def summarized_failure_feedback(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for row in rows:
        artifact_dir = Path(str(row.get("artifact_dir") or ""))
        verifier = read_json(artifact_dir / "verifier_report.json", {})
        summary = read_json(artifact_dir / "variant_summary.json", {})
        normalized = read_json(artifact_dir / "normalized_execution.json", {})
        target_excerpt = excerpt(read_text(artifact_dir / "target" / "target.md"))
        prior_findings = [
            {
                "capability_id": finding.get("capability_id"),
                "issue": finding.get("issue"),
                "evidence_span": finding.get("evidence_span"),
            }
            for finding in normalized.get("findings", [])
            if isinstance(finding, dict)
        ]
        result.append(
            {
                "case_id": row.get("case_id"),
                "task_family": row.get("task_family"),
                "feedback_type": row.get("feedback_type"),
                "missing_capabilities": verifier.get("missing_capabilities", []),
                "false_positive_capabilities": verifier.get("false_positive_capabilities", []),
                "activated_capability_group": summary.get("activated_capability_group"),
                "summary_score": summary.get("score"),
                "target_excerpt": target_excerpt,
                "prior_findings": prior_findings,
                "normalizer_taxonomy": summary.get("post_normalization_verifier_taxonomy", []),
            }
        )
    return result


def summarized_guard_feedback(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for row in rows:
        artifact_dir = Path(str(row.get("artifact_dir") or ""))
        normalized = read_json(artifact_dir / "normalized_execution.json", {})
        result.append(
            {
                "case_id": row.get("case_id"),
                "task_family": row.get("task_family"),
                "target_excerpt": excerpt(read_text(artifact_dir / "target" / "target.md")),
                "observed_findings": normalized.get("findings", []),
                "expected_behavior": "keep_no_findings_or_do_not_get_worse",
            }
        )
    return result


def apply_capability_edits(base_text: str, edits: list[dict[str, Any]]) -> str:
    lines = base_text.splitlines()
    for edit in edits:
        capability_id = str(edit.get("capability_id") or "").strip()
        replacement_review_rule = str(edit.get("replacement_review_rule") or "").strip()
        replacement_evidence_pattern = str(edit.get("replacement_evidence_pattern") or "").strip()
        replacement_fix_shape = str(edit.get("replacement_fix_shape") or "").strip()
        additional_lessons = [str(item).strip() for item in edit.get("additional_lessons", []) if str(item).strip()]
        if not capability_id or not replacement_review_rule:
            continue
        capability_index = next((i for i, line in enumerate(lines) if line.startswith(f"  - `{capability_id}`:")), None)
        if capability_index is None:
            continue
        section_end = len(lines)
        for i in range(capability_index + 1, len(lines)):
            if lines[i].startswith("  - `") or lines[i].startswith("### ") or lines[i].startswith("## "):
                section_end = i
                break
        review_index = next((i for i in range(capability_index + 1, section_end) if lines[i].startswith("    - review_rule:")), None)
        if review_index is not None:
            lines[review_index] = f"    - review_rule: {replacement_review_rule}"
        evidence_index = next((i for i in range(capability_index + 1, section_end) if lines[i].startswith("    - evidence_pattern:")), None)
        if evidence_index is not None and replacement_evidence_pattern:
            lines[evidence_index] = f"    - evidence_pattern: `{replacement_evidence_pattern}`"
        fix_index = next((i for i in range(capability_index + 1, section_end) if lines[i].startswith("    - fix_shape:")), None)
        if fix_index is not None and replacement_fix_shape:
            lines[fix_index] = f"    - fix_shape: {replacement_fix_shape}"
        insert_after = next((i for i in range(capability_index + 1, section_end) if lines[i].startswith("    - fix_shape:")), section_end - 1)
        lesson_lines = [f'    - distilled_public_lesson: "{lesson}"' for lesson in additional_lessons if lesson]
        if lesson_lines:
            insert_at = insert_after + 1
            while insert_at < len(lines) and lines[insert_at].startswith("    - distilled_public_lesson:"):
                insert_at += 1
            lines[insert_at:insert_at] = lesson_lines
    return "\n".join(lines).rstrip() + "\n"


def relevant_capability_ids(feedback_rows: list[dict[str, Any]]) -> list[str]:
    capability_ids: set[str] = set()
    for row in feedback_rows:
        for capability_id in row.get("missing_capabilities", []):
            if capability_id:
                capability_ids.add(str(capability_id))
        for finding in row.get("prior_findings", []):
            capability_id = str(finding.get("capability_id") or "").strip()
            if capability_id:
                capability_ids.add(capability_id)
    return sorted(capability_ids)


def skill_excerpt_for_capabilities(base_text: str, capability_ids: list[str]) -> str:
    if not capability_ids:
        return base_text[:4000]
    lines = base_text.splitlines()
    segments: list[str] = []

    review_start = next((i for i, line in enumerate(lines) if line.startswith("## Review Protocol")), None)
    if review_start is not None:
        review_end = next((i for i in range(review_start + 1, len(lines)) if lines[i].startswith("## ") and i > review_start), len(lines))
        segments.extend(lines[review_start:review_end])
        segments.append("")

    group_starts = [i for i, line in enumerate(lines) if line.startswith("### ")]
    for group_index, start in enumerate(group_starts):
        end = group_starts[group_index + 1] if group_index + 1 < len(group_starts) else next(
            (i for i in range(start + 1, len(lines)) if lines[i].startswith("## ") and not lines[i].startswith("### ")),
            len(lines),
        )
        group_lines = lines[start:end]
        if any(f"`{capability_id}`" in line for capability_id in capability_ids for line in group_lines):
            segments.extend(group_lines)
            segments.append("")

    excerpt_text = "\n".join(segments).strip()
    return excerpt_text if excerpt_text else base_text[:4000]


def refine_capability_edits(
    edits: list[dict[str, Any]],
    *,
    feedback_rows: list[dict[str, Any]],
    guard_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[str]]:
    refined: list[dict[str, Any]] = []
    refinement_notes: list[str] = []
    saw_combo_failure = any(
        any(str(finding.get("capability_id") or "").strip() == "CONFIG_AUDIT_EXPORT" for finding in row.get("prior_findings", []))
        for row in feedback_rows
    )
    for original in edits:
        edit = json.loads(json.dumps(original))
        capability_id = str(edit.get("capability_id") or "").strip()
        if capability_id == "CONFIG_ENV_GUARD":
            review_rule = str(edit.get("replacement_review_rule") or "").strip()
            evidence_pattern = str(edit.get("replacement_evidence_pattern") or "").strip()
            fix_shape = str(edit.get("replacement_fix_shape") or "").strip()
            lessons = [str(item).strip() for item in edit.get("additional_lessons", []) if str(item).strip()]
            if "comments, file names, or debugging notes alone do not count as explicit isolation" not in review_rule.lower():
                review_rule = review_rule.rstrip(".") + ". Comments, file names, or debugging notes alone do not count as explicit isolation."
                refinement_notes.append("config_env_guard_explicit_isolation_clause_added")
            if "explicit dev-only profile or environment gate" not in review_rule.lower():
                review_rule = review_rule.rstrip(".") + ". Only an explicit dev-only profile or environment gate can suppress this finding."
                refinement_notes.append("config_env_guard_dev_only_guard_clause_added")
            if "comments or file naming" not in evidence_pattern.lower():
                evidence_pattern = evidence_pattern.rstrip(".") + "; comments or file naming without explicit gating still count as in-scope evidence"
                refinement_notes.append("config_env_guard_evidence_pattern_tightened")
            if "local dev-only override" not in fix_shape.lower():
                fix_shape = fix_shape.rstrip(".") + " Prefer local dev-only overrides or environment variables for non-production secrets."
                refinement_notes.append("config_env_guard_fix_shape_refined")
            if saw_combo_failure and not any("same target span can justify both" in lesson.lower() for lesson in lessons):
                lessons.append("The same target span can justify both CONFIG_AUDIT_EXPORT and CONFIG_ENV_GUARD when audit gaps and unisolated secrets appear together.")
                refinement_notes.append("config_env_guard_combo_lesson_added")
            edit["replacement_review_rule"] = review_rule
            edit["replacement_evidence_pattern"] = evidence_pattern
            edit["replacement_fix_shape"] = fix_shape
            edit["additional_lessons"] = lessons
        refined.append(edit)
    return refined, refinement_notes


def candidate_addition(rows: list[dict[str, Any]]) -> str:
    sections = [
        "## Open-World Closed-Loop Candidate",
        "",
        "This candidate is generated from the remaining bounded open-world failure rows.",
        "Keep dependency/version-risk, regex DoS, and server-side execution review out of scope.",
        "",
    ]
    families = {str(row.get("task_family") or "") for row in rows}
    if "config_security" in families:
        sections.extend(
            [
                "### Config Security Completion",
                "",
                "- Emit `CONFIG_AUDIT_EXPORT` when a production-facing audit block is enabled but `retention_days`, `export_sink`, or equivalent review destination is empty or missing.",
                "- Emit `CONFIG_ENV_GUARD` when a configuration file contains hardcoded API keys, session secrets, credentials, or debug-style defaults that should not live in committed application config.",
                "- Hardcoded secrets remain concrete findings even if a file is named `development` when the committed config is still reachable, shared, or treated as an application default in the target task.",
                "- Do not suppress concrete hardcoded-secret evidence as merely contextual noise.",
                "",
            ]
        )
    if "auth_access_control" in families:
        sections.extend(
            [
                "### Auth Scope Matrix Completion",
                "",
                "- Emit `AUTH_SCOPE_MATRIX` when the exact target line shows only `is_authenticated` or login-state gating before a protected read or mutation.",
                "- Emit `AUTH_OBJECT_OWNERSHIP` when the same target line loads an object by id without tenant, owner, account, or relationship filtering.",
                "- Emit `AUTH_ERROR_ENVELOPE` when denial output reveals a stable object id, invoice id, or business identifier instead of a neutral request id.",
                "- If one exact target line supports all three auth defects, emit three separate findings with the same evidence span.",
                "",
            ]
        )
    if "upload_security" in families:
        sections.extend(
            [
                "### Upload Completion",
                "",
                "- Emit `UPLOAD_TYPE_MAGIC` when extension-only or Content-Type-only validation is used without file-signature or magic-byte checks.",
                "- Emit `UPLOAD_PATH_ISOLATION` when user-controlled names are written directly or uploads remain under a public/executable root.",
                "- Emit `UPLOAD_AUDIT_RETENTION` when upload events lack attributable retention/export evidence.",
                "",
            ]
        )
    return "\n".join(sections).strip()

def semantic_candidate_patch(
    *,
    base: SkillPackage,
    base_text: str,
    source_rows: list[dict[str, Any]],
    guard_rows: list[dict[str, Any]],
    base_url: str,
    api_key: str,
    model: str,
    timeout_seconds: float,
) -> dict[str, Any]:
    feedback_rows = summarized_failure_feedback(source_rows)
    negative_guard_rows = summarized_guard_feedback(guard_rows)
    capability_ids = relevant_capability_ids(feedback_rows)
    focused_skill_excerpt = skill_excerpt_for_capabilities(base_text, capability_ids)
    schema = {
        "candidate_id": "semantic_candidate_001",
        "capability_edits": [
            {
                "capability_id": base.capabilities[0] if base.capabilities else "CONFIG_ENV_GUARD",
                "replacement_review_rule": "Concrete replacement review_rule text for one existing capability section.",
                "replacement_evidence_pattern": "Concrete evidence pattern text grounded in the failure family.",
                "replacement_fix_shape": "Concrete fix shape text grounded in the failure family.",
                "additional_lessons": ["One short public-material lesson to insert under the same capability."],
            }
        ],
        "targeted_capabilities": [base.capabilities[0] if base.capabilities else "CONFIG_ENV_GUARD"],
        "why_this_should_help": "Short explanation of why the edit addresses the observed missing capability without expanding scope.",
        "risk_note": "Short note about false-positive or over-scope risk to watch.",
    }
    prompt = "\n\n".join(
        [
            "You are generating one conservative Skill patch from real open-world failure feedback.",
            "Only strengthen or clarify existing capabilities already present in the active Skill package.",
            "Do not add dependency/version-risk, regex DoS, server-side JS execution review, or any new task family.",
            "Use only the failure summaries below. Do not assume verifier-only oracle labels beyond the provided summaries.",
            "Every capability_edit must include a non-empty replacement_review_rule, replacement_evidence_pattern, and replacement_fix_shape.",
            "Produce capability_edits that replace existing review_rule, evidence_pattern, and fix_shape lines and optionally add short distilled_public_lesson lines inside existing capability sections.",
            "If a failure row already emitted one config capability but still missed another, explicitly allow two separate findings to share the same exact target span when both defects are grounded there.",
            "If a committed development or test configuration contains a hardcoded secret, do not suppress it merely because the file is labeled development; require explicit isolation in the rule and fix shape.",
            "Preserve the clean negative guard rows below: do not broaden the rule so far that an explicitly dev-only isolated profile becomes a false positive.",
            "Prefer concrete detection language over policy prose so the runtime is more likely to trigger the right capability on the next live run.",
            "Return exactly one JSON object.",
            f"Existing capabilities: {json.dumps(list(base.capabilities), ensure_ascii=False)}",
            f"Focused capability ids: {json.dumps(capability_ids, ensure_ascii=False)}",
            f"Failure summaries: {json.dumps(feedback_rows, ensure_ascii=False, indent=2)}",
            f"Clean negative guard rows: {json.dumps(negative_guard_rows, ensure_ascii=False, indent=2)}",
            "Focused skill excerpt:",
            focused_skill_excerpt[:6000],
            "JSON schema:",
            json.dumps(schema, ensure_ascii=False, indent=2),
        ]
    )
    last_error: Exception | None = None
    payload: dict[str, Any] | None = None
    meta: dict[str, Any] = {}
    for attempt_index in range(1, 4):
        attempt_messages = [
            {"role": "system", "content": "You are a strict defensive Skill evolution assistant. Return JSON only."},
            {"role": "user", "content": prompt},
        ]
        if attempt_index > 1:
            attempt_messages.insert(
                1,
                {
                    "role": "system",
                    "content": "The previous attempt was invalid because it did not return one parseable JSON object. Return exactly one JSON object and nothing else.",
                },
            )
        try:
            payload, meta = call_chat_completion_json(
                base_url=base_url,
                api_key=api_key,
                model=model,
                messages=attempt_messages,
                temperature=0.0,
                max_tokens=2800,
                timeout=timeout_seconds,
            )
            break
        except Exception as exc:
            last_error = exc
    if payload is None:
        raise RuntimeError(f"semantic candidate generation failed after retries: {last_error}") from last_error
    targeted = [str(item).strip() for item in payload.get("targeted_capabilities", []) if str(item).strip() in set(base.capabilities)]
    if not targeted:
        raise ValueError("semantic candidate did not target any existing capability")
    capability_edits = payload.get("capability_edits", [])
    if not isinstance(capability_edits, list) or not capability_edits:
        raise ValueError("semantic candidate did not return capability_edits")
    for edit in capability_edits:
        missing_fields = [
            field
            for field in ("capability_id", "replacement_review_rule", "replacement_evidence_pattern", "replacement_fix_shape")
            if not str(edit.get(field) or "").strip()
        ]
        if missing_fields:
            raise ValueError(f"semantic candidate returned incomplete capability_edit fields: {', '.join(missing_fields)}")
    capability_edits, refinement_notes = refine_capability_edits(
        capability_edits,
        feedback_rows=feedback_rows,
        guard_rows=negative_guard_rows,
    )
    candidate_id = str(payload.get("candidate_id") or "semantic_candidate_001").strip().replace(" ", "_")
    return {
        "candidate_id": candidate_id,
        "capability_edits": capability_edits,
        "targeted_capabilities": targeted,
        "why_this_should_help": str(payload.get("why_this_should_help") or "").strip(),
        "risk_note": str(payload.get("risk_note") or "").strip(),
        "generation_meta": {
            "model": meta.get("model") or model,
            "latency_ms": meta.get("latency_ms"),
            "usage": meta.get("usage"),
            "raw_content": meta.get("raw_content"),
            "feedback_rows": feedback_rows,
            "negative_guard_rows": negative_guard_rows,
            "focused_capability_ids": capability_ids,
            "focused_skill_excerpt": focused_skill_excerpt,
            "auto_refinement_notes": refinement_notes,
        },
    }


def write_candidate(
    base: SkillPackage,
    base_text: str,
    candidate_dir: Path,
    source_rows: list[dict[str, Any]],
    guard_rows: list[dict[str, Any]],
    *,
    candidate_mode: str,
    base_url: str,
    api_key: str,
    model: str,
    timeout_seconds: float,
) -> tuple[SkillPackage, str]:
    generation_details: dict[str, Any]
    if candidate_mode == "live_semantic":
        generation_details = semantic_candidate_patch(
            base=base,
            base_text=base_text,
            source_rows=source_rows,
            guard_rows=guard_rows,
            base_url=base_url,
            api_key=api_key,
            model=model,
            timeout_seconds=timeout_seconds,
        )
        package = clone_package(base, version=f"v3_{generation_details['candidate_id']}")
        candidate_text = apply_capability_edits(base_text, generation_details["capability_edits"])
    else:
        generation_details = {
            "candidate_id": "template_candidate_auth_scope",
            "patch_markdown": candidate_addition(source_rows),
            "targeted_capabilities": [],
            "why_this_should_help": "Template patch derived from remaining bounded failure families.",
            "risk_note": "May remain too broad or too generic if the failure pattern is narrower than the family-level lesson.",
            "generation_meta": {"feedback_rows": summarized_failure_feedback(source_rows)},
        }
        package = clone_package(base, version="v3_candidate_auth_scope")
        candidate_text = base_text.rstrip() + "\n\n" + candidate_addition(source_rows) + "\n"
    write_text(candidate_dir / "SKILL.md", candidate_text)
    write_json(candidate_dir / "manifest.json", package.to_dict())
    diff = "\n".join(
        difflib.unified_diff(
            base_text.splitlines(),
            candidate_text.splitlines(),
            fromfile="open_world_v2_SKILL.md",
            tofile="open_world_v3_candidate_auth_scope.md",
            lineterm="",
        )
    )
    write_text(candidate_dir / "skill_diff.md", diff + "\n")
    write_json(
        candidate_dir / "candidate_generation_inputs.json",
        {
            "allowed_sources": ["open-world failure feedback", "public-material distilled skill text", "verifier feedback", "evidence summary"],
            "forbidden_sources": ["verifier-only expected finding", "verifier-only expected evidence span", "verifier-only clean/negative answer label"],
            "verifier_only_oracle_fields_read": False,
            "source_summary": str(OPEN_WORLD_SUMMARY),
            "source_failure_rows": source_rows,
            "source_guard_rows": guard_rows,
            "candidate_mode": candidate_mode,
            "generation_details": generation_details,
        },
    )
    return package, candidate_text


def load_candidate_from_dir(candidate_dir: Path) -> tuple[SkillPackage, str]:
    manifest = read_json(candidate_dir / "manifest.json", {})
    if not manifest:
        raise FileNotFoundError(f"candidate manifest not found under {candidate_dir}")
    skill_text = read_text(candidate_dir / "SKILL.md")
    if not skill_text.strip():
        raise FileNotFoundError(f"candidate SKILL.md not found under {candidate_dir}")
    return SkillPackage.from_dict(manifest), skill_text


def run_variant(
    *,
    case_payload: dict[str, Any],
    spec: mini.VariantSpec,
    pointer: dict[str, Any],
    output_dir: Path,
    base_url: str,
    model: str,
    timeout_seconds: float,
) -> dict[str, Any]:
    out_dir = output_dir / str(case_payload["case_id"]) / spec.name
    try:
        summary = mini.run_variant(
            case_payload=case_payload,
            agent_case=mini.make_agent_visible_case(case_payload),
            verifier_only=case_payload["verifier_only"],
            spec=spec,
            backend="live_llm_text",
            output_dir=out_dir,
            active_pointer_snapshot=pointer,
            runner_metadata={
                "base_url": base_url,
                "model": model,
                "temperature": 0.0,
                "timeout": timeout_seconds,
                "task_label": f"{spec.name}:{case_payload['agent_visible']['task_family']}",
                "contract_mode": "strict",
                "enable_evidence_normalizer": True,
                "prompt_addendum": (
                    "Open-world closed-loop validation: quote exact target lines; emit no findings for unsupported or clean cases. "
                    "Defensive review only. Do not invent capabilities beyond the active Skill package."
                ),
            },
        )
        verifier = summary.get("post_normalization_verifier") or read_json(out_dir / "verifier_report.json", {})
        return {
            "case_id": case_payload["case_id"],
            "task_family": case_payload["agent_visible"]["task_family"],
            "variant": spec.name,
            "status": "completed",
            "verifier_result": "pass" if verifier.get("pass") else "fail",
            "feedback_type": verifier.get("feedback_type"),
            "score": score_from_verifier(verifier),
            "effective_pass": bool(verifier.get("pass")) and bool(summary.get("capability_group_correct")),
            "activated_capability_group": summary.get("activated_capability_group"),
            "expected_capability_group": summary.get("expected_capability_group"),
            "capability_group_correct": summary.get("capability_group_correct"),
            "false_positive_count": false_positive_count(verifier),
            "out_of_scope_correct": summary.get("out_of_scope_correct"),
            "clean_or_negative": bool(case_payload["verifier_only"].get("clean_or_negative")),
            "unsupported_limitation": bool(case_payload["verifier_only"].get("unsupported_limitation")),
            "artifact_dir": str(out_dir),
        }
    except Exception as exc:  # noqa: BLE001
        write_text(out_dir / "blocked_or_failed_trace.txt", traceback.format_exc())
        return {
            "case_id": case_payload["case_id"],
            "task_family": case_payload["agent_visible"]["task_family"],
            "variant": spec.name,
            "status": "failed",
            "failure_reason": str(exc),
            "artifact_dir": str(out_dir),
        }


def decide(base_rows: list[dict[str, Any]], candidate_rows: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any]]:
    base_by_case = {row["case_id"]: row for row in base_rows}
    candidate_by_case = {row["case_id"]: row for row in candidate_rows}
    shared_cases = [case_id for case_id in base_by_case if case_id in candidate_by_case]
    base_score = sum(float(base_by_case[case_id].get("score") or 0.0) for case_id in shared_cases) / len(shared_cases) if shared_cases else 0.0
    candidate_score = sum(float(candidate_by_case[case_id].get("score") or 0.0) for case_id in shared_cases) / len(shared_cases) if shared_cases else 0.0
    fp_delta = sum(int(candidate_by_case[case_id].get("false_positive_count") or 0) - int(base_by_case[case_id].get("false_positive_count") or 0) for case_id in shared_cases)
    positive_regressions = [
        case_id
        for case_id in shared_cases
        if base_by_case[case_id].get("effective_pass") and not candidate_by_case[case_id].get("effective_pass")
    ]
    clean_not_worse = all(
        int(candidate_by_case[case_id].get("false_positive_count") or 0) <= int(base_by_case[case_id].get("false_positive_count") or 0)
        for case_id in shared_cases
        if base_by_case[case_id].get("clean_or_negative")
    )
    unsupported_preserved = all(
        bool(candidate_by_case[case_id].get("out_of_scope_correct")) and int(candidate_by_case[case_id].get("false_positive_count") or 0) == 0
        for case_id in shared_cases
        if base_by_case[case_id].get("unsupported_limitation")
    )
    scope_violation = any(not bool(candidate_by_case[case_id].get("capability_group_correct")) for case_id in shared_cases)
    validation = {
        "base_score": round(base_score, 4),
        "candidate_score": round(candidate_score, 4),
        "score_delta": round(candidate_score - base_score, 4),
        "false_positive_delta": fp_delta,
        "positive_regression_count": len(positive_regressions),
        "positive_regression_cases": positive_regressions,
        "clean_negative_not_worse": clean_not_worse,
        "unsupported_limitation_preserved": unsupported_preserved,
        "scope_violation": scope_violation,
        "shared_case_count": len(shared_cases),
    }
    promoted = (
        validation["score_delta"] > 0
        and fp_delta <= 0
        and validation["positive_regression_count"] == 0
        and clean_not_worse
        and unsupported_preserved
        and not scope_violation
    )
    decision = {
        "decision": "staged_promotion_proposal" if promoted else "not_promoted",
        "reason": "strict_open_world_closed_loop_rule_satisfied" if promoted else "strict_open_world_closed_loop_rule_not_satisfied",
        "auto_installed": False,
        "promotion_rule": "candidate_score > base_score and false_positive_delta<=0 and positive_regression_count==0 and clean negative not worse and unsupported preserved and scope_violation=false",
    }
    return validation, decision


def render_report(payload: dict[str, Any]) -> str:
    command_tail = f"--candidate-mode {payload.get('candidate_mode', 'template')}"
    if payload.get("candidate_mode") == "reused_candidate" and payload.get("candidate_dir"):
        command_tail += f" --reuse-candidate-dir {payload['candidate_dir']}"
    lines = [
        "# Open-World Closed-Loop Status",
        "",
        f"Generated at: `{payload['generated_at']}`",
        "",
        "This run continues the bounded open-world story one step further: public-material distillation first, then a narrow structured repair candidate generated from the remaining live failure pattern.",
        "",
        "## Fresh Commands",
        "",
        "```powershell",
        f"skill-deploy open-world-distill-validation --skill-id {payload['installed_skill']} --version {payload['base_version']} --backend live_llm_text --base-url https://api.deepseek.com --model deepseek-v4-flash --projection-mode {payload.get('projection_mode', 'keyword')}",
        f"skill-deploy open-world-closed-loop --installed {payload['installed_skill']} --repeats {payload['repeat_count']} --base-url https://api.deepseek.com --model deepseek-v4-flash {command_tail}",
        "```",
        "",
        "## Summary",
        "",
        f"- Base installed skill: `{payload['installed_skill']}`",
        f"- Base version: `{payload['base_version']}`",
        f"- Repeat count: `{payload['repeat_count']}`",
        f"- Candidate mode: `{payload.get('candidate_mode', 'template')}`",
        f"- Candidate dir: `{payload.get('candidate_dir', '')}`",
        f"- Promotion count: `{payload['promotion_count']}` / `{payload['repeat_count']}`",
        f"- Stable improvement: `{payload['stable_open_world_evolution']}`",
        f"- Base mean score: `{payload.get('base_mean_score')}`",
        f"- Candidate mean score: `{payload.get('candidate_mean_score')}`",
        f"- Mean score delta: `{payload.get('mean_score_delta')}`",
        f"- Strict positive repeats: `{payload.get('strict_positive_repeats')}` / `{payload['repeat_count']}`",
        "",
        "## Repeat Decisions",
        "",
        "| Repeat | Decision | Base score | Candidate score | Delta | FP delta | Positive regressions |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for item in payload["repeats"]:
        validation = item["validation_result"]
        decision = item["promotion_decision"]
        lines.append(
            f"| {item['repeat_index']} | {decision['decision']} | {validation['base_score']} | {validation['candidate_score']} | "
            f"{validation['score_delta']} | {validation['false_positive_delta']} | {validation['positive_regression_count']} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- `staged_promotion_proposal` means the candidate beat the active installed skill on that repeat under the strict gate.",
            "- `reused_candidate` means the validation froze one previously generated candidate and reran it, instead of regenerating a new candidate each time.",
            "- Positive mean delta is supportive bounded evidence even when one repeat remains tied or negative; it is not the same as universal strict stability.",
            "",
            "## Boundary",
            "",
            "- This is bounded evidence for open-world distillation followed by one narrow evolution step.",
            "- It is not proof of unrestricted autonomous search over arbitrary public materials.",
            "- Unsupported dependency/version-risk remains unsupported.",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run one bounded closed-loop evolution step on top of the open-world distilled skill.")
    parser.add_argument("--installed", default="secure_code_review_open_world_distilled")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--base-url", default=os.environ.get("OPENAI_BASE_URL") or "https://api.deepseek.com")
    parser.add_argument("--model", default=os.environ.get("MODEL") or os.environ.get("OPENAI_MODEL") or "deepseek-v4-flash")
    parser.add_argument("--timeout-seconds", type=float, default=60.0)
    parser.add_argument("--candidate-mode", choices=["template", "live_semantic"], default="template")
    parser.add_argument("--reuse-candidate-dir", default="")
    args = parser.parse_args(argv)

    base_resolved = resolve_installed_skill(ROOT, args.installed)
    pointer = load_active_pointer(ROOT, args.installed)
    base_spec = mini.VariantSpec("open_world_v2", base_resolved["skill_package"], base_resolved["skill_text"], base_resolved["skill_dir"], "open_world_distilled_package")
    candidate_dir = OUTPUT_ROOT / "candidate_auth_scope"
    failures = source_failure_rows()
    guard_rows = source_guard_rows()
    api_key = os.environ.get("OPENAI_API_KEY") or ""
    if args.reuse_candidate_dir:
        candidate_dir = Path(args.reuse_candidate_dir).resolve()
        candidate_package, candidate_text = load_candidate_from_dir(candidate_dir)
        candidate_runtime_source = "open_world_closed_loop_reused_candidate"
        candidate_mode = "reused_candidate"
    else:
        if args.candidate_mode == "live_semantic" and not api_key:
            raise RuntimeError("OPENAI_API_KEY is required for live_semantic candidate generation")
        candidate_package, candidate_text = write_candidate(
            base_resolved["skill_package"],
            base_resolved["skill_text"],
            candidate_dir,
            failures,
            guard_rows,
            candidate_mode=args.candidate_mode,
            base_url=args.base_url,
            api_key=api_key,
            model=args.model,
            timeout_seconds=args.timeout_seconds,
        )
        candidate_runtime_source = "open_world_closed_loop_candidate"
        candidate_mode = args.candidate_mode
    candidate_spec = mini.VariantSpec("open_world_v3_candidate", candidate_package, candidate_text, candidate_dir, candidate_runtime_source)
    cases = load_cases()

    repeat_outputs: list[dict[str, Any]] = []
    promotion_count = 0
    for repeat_index in range(1, args.repeats + 1):
        repeat_root = OUTPUT_ROOT / f"repeat_{repeat_index:02d}"
        base_rows = [
            run_variant(
                case_payload=case_payload,
                spec=base_spec,
                pointer=pointer,
                output_dir=repeat_root / "base",
                base_url=args.base_url,
                model=args.model,
                timeout_seconds=args.timeout_seconds,
            )
            for case_payload in cases
        ]
        candidate_rows = [
            run_variant(
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
        validation, decision = decide(base_rows, candidate_rows)
        if decision["decision"] == "staged_promotion_proposal":
            promotion_count += 1
        repeat_outputs.append(
            {
                "repeat_index": repeat_index,
                "validation_result": validation,
                "promotion_decision": decision,
                "base_rows": base_rows,
                "candidate_rows": candidate_rows,
            }
        )

    stable = promotion_count == args.repeats and all(item["validation_result"]["score_delta"] > 0 for item in repeat_outputs)
    base_scores = [float(item["validation_result"]["base_score"]) for item in repeat_outputs]
    candidate_scores = [float(item["validation_result"]["candidate_score"]) for item in repeat_outputs]
    deltas = [float(item["validation_result"]["score_delta"]) for item in repeat_outputs]
    payload = {
        "generated_at": utc_now(),
        "installed_skill": args.installed,
        "base_version": base_resolved["skill_package"].version,
        "repeat_count": args.repeats,
        "api_key_present": api_key_present(),
        "candidate_dir": str(candidate_dir),
        "candidate_mode": candidate_mode,
        "projection_mode": read_json(OPEN_WORLD_SUMMARY, {}).get("projection_mode", "keyword"),
        "promotion_count": promotion_count,
        "stable_open_world_evolution": "pass" if stable else "partial",
        "base_mean_score": round(sum(base_scores) / len(base_scores), 4),
        "candidate_mean_score": round(sum(candidate_scores) / len(candidate_scores), 4),
        "mean_score_delta": round(sum(deltas) / len(deltas), 4),
        "strict_positive_repeats": sum(1 for value in deltas if value > 0),
        "repeats": repeat_outputs,
    }
    write_json(SUMMARY_PATH, payload)
    write_text(REPORT, render_report(payload))
    print(json.dumps({"status": payload["stable_open_world_evolution"], "promotion_count": promotion_count, "report": str(REPORT)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
