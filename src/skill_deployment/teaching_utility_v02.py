from __future__ import annotations

import json
import random
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .task_cases import LegacyHoldoutTaskCase, load_legacy_holdout_task_cases


API_MATERIAL_FILES = (
    Path("data/api_review_expert_materials/api_design_guidelines.md"),
    Path("data/api_review_expert_materials/historical_review_comments.md"),
    Path("data/api_review_expert_materials/review_checklist.md"),
)
CONFIG_MATERIAL_FILES = (
    Path("data/config_security_expert_materials/config_security_guidelines.md"),
)

BASE_RULE_BUDGETS: dict[str, tuple[str, ...]] = {
    "api_review": ("R001", "R002", "R003", "R004"),
    "config_security": ("C001", "C002", "C003", "C004"),
}


RULE_SPECS: dict[str, dict[str, dict[str, Any]]] = {
    "api_review": {
        "R001": {
            "title": "Authentication and authorization boundary",
            "text": "Document authentication method, roles/scopes, and authorization failure behavior.",
            "keywords": ("authentication", "authorization", "role", "scope", "forbidden", "unauthorized", "login"),
        },
        "R002": {
            "title": "Request validation contract",
            "text": "Document required/optional status, type, range, length, and enum constraints for request fields.",
            "keywords": ("required", "type", "range", "length", "enum", "validation", "request"),
        },
        "R003": {
            "title": "Stable error code coverage",
            "text": "Cover success, validation, unauthorized, forbidden, not found, duplicate, and server failures with stable codes.",
            "keywords": ("error", "code", "400", "401", "403", "404", "409", "500", "duplicate"),
        },
        "R004": {
            "title": "Sensitive response data suppression",
            "text": "Do not expose tokens, stack traces, raw secrets, or unnecessary personal data in responses.",
            "keywords": ("token", "secret", "trace", "identity", "phone", "sensitive", "response"),
        },
        "R005": {
            "title": "Response envelope contract",
            "text": "Use a stable envelope with code, message, request_id, and data.",
            "keywords": ("response", "code", "message", "request_id", "data", "payload", "status"),
        },
        "R006": {
            "title": "Mutation idempotency behavior",
            "text": "POST/PUT/PATCH endpoints should explain idempotency keys or duplicate submission behavior.",
            "keywords": ("post", "put", "patch", "idempotency", "duplicate", "mutation"),
        },
    },
    "config_security": {
        "C001": {
            "title": "No hardcoded secrets",
            "text": "Do not hardcode tokens, passwords, API keys, or private credentials in configuration files.",
            "keywords": ("token", "api_key", "secret", "password", "sk_live", "credential"),
        },
        "C002": {
            "title": "Production TLS",
            "text": "Production external endpoints must use TLS rather than plaintext HTTP.",
            "keywords": ("http://", "tls", "https", "endpoint", "external_api_url"),
        },
        "C003": {
            "title": "Least-privilege service account",
            "text": "Avoid admin, wildcard, or broad write roles for service accounts unless justified.",
            "keywords": ("admin", "wildcard", "*", "role", "service_account", "least privilege"),
        },
        "C004": {
            "title": "Disable production debug",
            "text": "Production debug mode must be disabled.",
            "keywords": ("debug: true", "debug", "production"),
        },
        "C005": {
            "title": "Runtime resource limits",
            "text": "Deployed services should define CPU and memory requests or limits.",
            "keywords": ("resources", "limits", "requests", "cpu", "memory"),
        },
        "C006": {
            "title": "Audit logging and retention",
            "text": "Enable audit logging and define retention or export behavior.",
            "keywords": ("audit", "retention", "export", "enabled: false", "retention_days", "export_sink"),
        },
    },
}


@dataclass(frozen=True)
class PilotCase:
    case_id: str
    domain: str
    visible_files: tuple[tuple[str, str], ...]
    expected_rule_ids: tuple[str, ...]
    negative_rule_ids: tuple[str, ...]
    critical_rule_ids: tuple[str, ...]
    metadata: dict[str, Any]
    source_dir: str

    @property
    def joined_text(self) -> str:
        return "\n\n".join(text for _name, text in self.visible_files)

    @property
    def clean_control(self) -> bool:
        return not self.expected_rule_ids

    @property
    def all_rule_ids(self) -> tuple[str, ...]:
        return tuple(RULE_SPECS[self.domain].keys())


@dataclass(frozen=True)
class DomainSplit:
    generation: PilotCase
    query_pool: tuple[PilotCase, ...]
    validation: PilotCase
    hidden: PilotCase


@dataclass(frozen=True)
class RepeatPlan:
    repeat_index: int
    api_review: DomainSplit
    config_security: DomainSplit

    @property
    def generation_cases(self) -> tuple[PilotCase, ...]:
        return (self.api_review.generation, self.config_security.generation)

    @property
    def query_cases(self) -> tuple[PilotCase, ...]:
        return self.api_review.query_pool + self.config_security.query_pool

    @property
    def validation_cases(self) -> tuple[PilotCase, ...]:
        return (self.api_review.validation, self.config_security.validation)

    @property
    def hidden_cases(self) -> tuple[PilotCase, ...]:
        return (self.api_review.hidden, self.config_security.hidden)


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_api_pilot_cases(root: Path) -> list[PilotCase]:
    cases: list[PilotCase] = []
    case_root = root / "data" / "api_review_holdout_cases"
    for legacy in load_legacy_holdout_task_cases(case_root):
        expected_payload = _read_json(Path(str(legacy.source_dir or "")) / "expected.json")
        cases.append(
            PilotCase(
                case_id=legacy.case_id,
                domain="api_review",
                visible_files=(("case.md", legacy.input_text),),
                expected_rule_ids=legacy.expected_rule_ids,
                negative_rule_ids=legacy.negative_rule_ids,
                critical_rule_ids=tuple(str(item) for item in expected_payload.get("critical_rule_ids", [])),
                metadata=dict(legacy.metadata),
                source_dir=str(legacy.source_dir or ""),
            )
        )
    return sorted(cases, key=lambda item: item.case_id)


def load_config_pilot_cases(root: Path) -> list[PilotCase]:
    cases: list[PilotCase] = []
    case_root = root / "data" / "config_security_cases"
    for case_dir in sorted(path for path in case_root.iterdir() if path.is_dir()):
        expected = _read_json(case_dir / "expected.json")
        cases.append(
            PilotCase(
                case_id=str(expected["case_id"]),
                domain="config_security",
                visible_files=(("config.md", _read_text(case_dir / "config.md")),),
                expected_rule_ids=tuple(str(item) for item in expected.get("expected_rule_ids", [])),
                negative_rule_ids=tuple(str(item) for item in expected.get("negative_rule_ids", [])),
                critical_rule_ids=tuple(str(item) for item in expected.get("critical_rule_ids", [])),
                metadata=dict(expected.get("metadata") or {}),
                source_dir=str(case_dir),
            )
        )
    return sorted(cases, key=lambda item: item.case_id)


def build_repeat_plans(root: Path, repeats: int = 3) -> list[RepeatPlan]:
    api_cases = load_api_pilot_cases(root)
    config_cases = load_config_pilot_cases(root)
    if len(api_cases) < 5 or len(config_cases) < 5:
        raise ValueError("teaching-utility pilot requires at least 5 api and 5 config cases")

    def rotated_split(cases: list[PilotCase], offset: int) -> DomainSplit:
        hidden = cases[-1]
        teachable_cases = cases[:-1]
        ordered = [teachable_cases[(offset + index) % len(teachable_cases)] for index in range(len(teachable_cases))]
        return DomainSplit(
            generation=ordered[0],
            query_pool=(ordered[1], ordered[2]),
            validation=ordered[3],
            hidden=hidden,
        )

    plans: list[RepeatPlan] = []
    for repeat_index in range(1, repeats + 1):
        offset = repeat_index - 1
        plans.append(
            RepeatPlan(
                repeat_index=repeat_index,
                api_review=rotated_split(api_cases, offset),
                config_security=rotated_split(config_cases, offset),
            )
        )
    return plans


def material_paths_for_domain(root: Path, domain: str) -> tuple[Path, ...]:
    if domain == "api_review":
        return tuple(root / path for path in API_MATERIAL_FILES)
    if domain == "config_security":
        return tuple(root / path for path in CONFIG_MATERIAL_FILES)
    raise ValueError(f"unknown domain: {domain}")


def material_text_for_domain(root: Path, domain: str) -> str:
    parts = []
    for path in material_paths_for_domain(root, domain):
        parts.append(f"# Source: {path.name}\n\n{_read_text(path).strip()}")
    return "\n\n".join(parts).strip() + "\n"


def render_base_domain_skill(root: Path, domain: str, *, selected_rule_ids: tuple[str, ...] | None = None) -> str:
    specs = RULE_SPECS[domain]
    selected = selected_rule_ids or tuple(specs.keys())
    material_excerpt = material_text_for_domain(root, domain)
    lines = [
        f"# {domain} base skill",
        "",
        "## Objective",
        "",
        f"Review `{domain}` tasks conservatively from visible evidence only.",
        "",
        "## Domain Rules",
        "",
    ]
    for rule_id in selected:
        spec = specs[rule_id]
        lines.append(f"- [{rule_id}] {spec['title']}: {spec['text']}")
    lines.extend(
        [
            "",
            "## Evidence Protocol",
            "",
            "- Quote or tightly paraphrase visible case text only.",
            "- Do not invent findings outside the listed rules.",
            "- Clean controls should return no findings.",
            "",
            "## Source Materials",
            "",
            material_excerpt,
        ]
    )
    return "\n".join(lines).strip() + "\n"


def render_cross_domain_base_skill(root: Path) -> str:
    sections = [
        "# v0.2 Teaching Utility Pilot Base Skill",
        "",
        "This skill is distilled from domain materials before any trajectory lessons are added.",
        "",
    ]
    for domain in ("api_review", "config_security"):
        sections.append(render_base_domain_skill(root, domain, selected_rule_ids=BASE_RULE_BUDGETS[domain]).rstrip())
        sections.append("")
    return "\n".join(sections).rstrip() + "\n"


def extract_rule_ids(text: str) -> tuple[str, ...]:
    matches = re.findall(r"\b([RC]\d{3})\b", text)
    return tuple(sorted(dict.fromkeys(matches)))


def tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9_]+", text.lower()))


def jaccard_distance(a: str, b: str) -> float:
    left = tokenize(a)
    right = tokenize(b)
    if not left and not right:
        return 0.0
    return 1.0 - (len(left & right) / max(1, len(left | right)))


def predict_rules_from_visible_text(domain: str, visible_text: str, allowed_rule_ids: tuple[str, ...]) -> tuple[str, ...]:
    lowered = visible_text.lower()
    predicted: list[str] = []
    for rule_id in allowed_rule_ids:
        spec = RULE_SPECS[domain].get(rule_id)
        if not spec:
            continue
        if any(keyword.lower() in lowered for keyword in spec["keywords"]):
            predicted.append(rule_id)
    return tuple(predicted)


def evaluate_review(case: PilotCase, review: dict[str, Any]) -> dict[str, Any]:
    findings = review.get("findings")
    if not isinstance(findings, list):
        findings = []
    required_fields = ["rule_id", "issue", "severity", "evidence"]
    if case.domain == "config_security":
        required_fields.append("config_path")

    seen_rule_ids: set[str] = set()
    format_errors: list[str] = []
    for index, finding in enumerate(findings):
        if not isinstance(finding, dict):
            format_errors.append(f"finding[{index}] is not an object")
            continue
        rule_id = str(finding.get("rule_id") or "").strip()
        if rule_id:
            seen_rule_ids.add(rule_id)
        for field in required_fields:
            if not str(finding.get(field, "")).strip():
                format_errors.append(f"finding[{index}] missing {field}")
        if rule_id and rule_id not in case.all_rule_ids:
            format_errors.append(f"finding[{index}] unknown rule_id {rule_id}")

    expected = set(case.expected_rule_ids)
    negative = set(case.negative_rule_ids)
    critical = set(case.critical_rule_ids)
    missing = sorted(expected - seen_rule_ids)
    critical_missing = sorted(critical - seen_rule_ids)
    false_positives = sorted(seen_rule_ids & negative)
    if not expected:
        coverage = 1.0 if not seen_rule_ids else 0.0
    else:
        coverage = len(expected & seen_rule_ids) / len(expected)
    clean_control_pass = case.clean_control and not seen_rule_ids
    pass_at_1 = not missing and not false_positives and not format_errors
    score = max(
        0.0,
        round(
            coverage
            - (0.2 * len(false_positives))
            - (0.1 * len(format_errors))
            - (0.05 * len(critical_missing)),
            4,
        ),
    )
    return {
        "pass_at_1": pass_at_1,
        "coverage": round(coverage, 4),
        "score": score,
        "missing_rule_ids": missing,
        "critical_missed_rule_ids": critical_missing,
        "false_positive_rule_ids": false_positives,
        "format_errors": format_errors,
        "seen_rule_ids": sorted(seen_rule_ids),
        "clean_control_pass": clean_control_pass,
    }


def trajectory_lesson_from_run(case: PilotCase, review_eval: dict[str, Any], review: dict[str, Any]) -> dict[str, Any]:
    seen = tuple(str(item) for item in review_eval.get("seen_rule_ids", []))
    missing = tuple(str(item) for item in review_eval.get("missing_rule_ids", []))
    false_positive = tuple(str(item) for item in review_eval.get("false_positive_rule_ids", []))
    if review_eval.get("pass_at_1"):
        focus_rules = seen or case.expected_rule_ids
        lesson = (
            f"{case.case_id}: when visible evidence matches {', '.join(focus_rules) or 'no rule'}, "
            "emit grounded findings only and preserve the output contract."
        )
    elif missing:
        lesson = (
            f"{case.case_id}: do not miss {', '.join(missing)} when the visible case text exposes those triggers; "
            "repair the review checklist before adding broader findings."
        )
        focus_rules = missing
    elif false_positive:
        lesson = (
            f"{case.case_id}: suppress false positives for {', '.join(false_positive)} when the visible case text is clean or out of scope."
        )
        focus_rules = false_positive
    else:
        lesson = (
            f"{case.case_id}: preserve JSON contract fields and keep findings grounded to visible evidence."
        )
        focus_rules = seen or case.expected_rule_ids
    return {
        "case_id": case.case_id,
        "domain": case.domain,
        "pass_at_1": bool(review_eval.get("pass_at_1")),
        "score": float(review_eval.get("score") or 0.0),
        "focus_rules": list(focus_rules),
        "lesson": lesson,
        "review_summary": {
            "seen_rule_ids": list(seen),
            "missing_rule_ids": list(missing),
            "false_positive_rule_ids": list(false_positive),
            "format_errors": list(review_eval.get("format_errors", [])),
        },
        "review": review,
    }


def render_distilled_skill(
    root: Path,
    *,
    method_name: str,
    repeat_index: int,
    source_lessons: list[dict[str, Any]],
    selected_query_lessons: list[dict[str, Any]],
) -> str:
    selected_rules_by_domain = {domain: set(BASE_RULE_BUDGETS[domain]) for domain in ("api_review", "config_security")}
    for lesson in source_lessons:
        selected_rules_by_domain[lesson["domain"]].update(str(item) for item in lesson["focus_rules"])
    for lesson in selected_query_lessons:
        selected_rules_by_domain[lesson["domain"]].update(str(item) for item in lesson["focus_rules"])
    lines = [
        "# v0.2 Distilled Skill",
        "",
        "This skill is distilled from domain materials plus trajectory lessons chosen under a matched budget.",
        "",
    ]
    for domain in ("api_review", "config_security"):
        lines.append(
            render_base_domain_skill(
                root,
                domain,
                selected_rule_ids=tuple(sorted(selected_rules_by_domain[domain])),
            ).rstrip()
        )
        lines.append("")
    lines.extend(
        [
            "## Trajectory Lessons",
            "",
            "Only trajectory-derived lessons selected within the matched budget are added below.",
            "",
        ]
    )
    for lesson in source_lessons:
        lines.append(f"- seed::{lesson['case_id']}: {lesson['lesson']}")
    for lesson in selected_query_lessons:
        lines.append(f"- query::{lesson['case_id']}: {lesson['lesson']}")
    lines.extend(
        [
            "",
            "## Boundaries",
            "",
            "- Do not use rules that are absent from the domain rule sections.",
            "- Clean controls should return no findings.",
            "- Unsupported families should not be invented from these two domains.",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def select_random_query(query_cases: tuple[PilotCase, ...], *, seed: int) -> dict[str, Any]:
    rng = random.Random(seed)
    selected = rng.choice(list(query_cases))
    return {
        "method": "random",
        "selected_case_id": selected.case_id,
        "selection_reason": f"seeded_random_choice:{seed}",
    }


def select_top_reward_success_only(
    query_cases: tuple[PilotCase, ...],
    source_lessons: list[dict[str, Any]],
) -> dict[str, Any]:
    by_domain = {lesson["domain"]: lesson for lesson in source_lessons}
    best_domain = max(
        by_domain.values(),
        key=lambda item: (
            int(bool(item["pass_at_1"])),
            float(item["score"]),
        ),
    )["domain"]
    selected = next(case for case in query_cases if case.domain == best_domain)
    return {
        "method": "top_reward_success_only",
        "selected_case_id": selected.case_id,
        "selection_reason": f"follow_highest_seed_reward_domain:{best_domain}",
    }


def select_success_failure_contrast(
    query_cases: tuple[PilotCase, ...],
    source_lessons: list[dict[str, Any]],
) -> dict[str, Any]:
    by_domain = {lesson["domain"]: lesson for lesson in source_lessons}
    target_domain = min(
        by_domain.values(),
        key=lambda item: (
            int(bool(item["pass_at_1"])),
            float(item["score"]),
        ),
    )["domain"]
    selected = next(case for case in query_cases if case.domain == target_domain)
    return {
        "method": "success_failure_contrast",
        "selected_case_id": selected.case_id,
        "selection_reason": f"follow_lower_seed_reward_domain_for_contrast:{target_domain}",
    }


def select_diversity(query_cases: tuple[PilotCase, ...], observed_cases: tuple[PilotCase, ...]) -> dict[str, Any]:
    generation_text = "\n\n".join(case.joined_text for case in observed_cases)
    scored = [
        (jaccard_distance(generation_text, case.joined_text), case)
        for case in query_cases
    ]
    scored.sort(key=lambda item: (-item[0], item[1].case_id))
    selected = scored[0][1]
    return {
        "method": "diversity",
        "selected_case_id": selected.case_id,
        "selection_reason": f"max_lexical_distance_from_seed:{round(scored[0][0], 4)}",
        "distance_scores": [{"case_id": case.case_id, "distance": round(distance, 4)} for distance, case in scored],
    }


def _mean_domain_score(lessons: list[dict[str, Any]], domain: str) -> float:
    domain_lessons = [float(item["score"]) for item in lessons if item["domain"] == domain]
    if not domain_lessons:
        return 0.0
    return sum(domain_lessons) / len(domain_lessons)


def _observed_lessons(
    source_lessons: list[dict[str, Any]],
    selected_query_lessons: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [*source_lessons, *selected_query_lessons]


def _residual_rules_by_domain(observed_lessons: list[dict[str, Any]]) -> dict[str, set[str]]:
    residual: dict[str, set[str]] = {"api_review": set(), "config_security": set()}
    for lesson in observed_lessons:
        focus = {str(item) for item in lesson.get("focus_rules", [])}
        if not lesson.get("pass_at_1"):
            residual[lesson["domain"]].update(focus)
            continue
        if lesson.get("review_summary", {}).get("false_positive_rule_ids"):
            residual[lesson["domain"]].update(str(item) for item in lesson["review_summary"]["false_positive_rule_ids"])
        if lesson.get("review_summary", {}).get("missing_rule_ids"):
            residual[lesson["domain"]].update(str(item) for item in lesson["review_summary"]["missing_rule_ids"])
    return residual


def _candidate_hypotheses(
    observed_lessons: list[dict[str, Any]],
    query_cases: tuple[PilotCase, ...],
    *,
    prior_candidates: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    if prior_candidates:
        return [dict(candidate) for candidate in prior_candidates]

    domain_scores = {
        domain: _mean_domain_score(observed_lessons, domain)
        for domain in ("api_review", "config_security")
    }
    low_domain = min(domain_scores.items(), key=lambda item: item[1])[0]
    high_domain = max(domain_scores.items(), key=lambda item: item[1])[0]
    broad_rules = sorted({str(rule) for lesson in observed_lessons for rule in lesson.get("focus_rules", [])})
    high_domain_rules = sorted(
        {
            str(rule)
            for lesson in observed_lessons
            if lesson["domain"] == high_domain
            for rule in lesson.get("focus_rules", [])
        }
        | set(BASE_RULE_BUDGETS[high_domain])
    )
    low_domain_rules = sorted(
        {
            str(rule)
            for lesson in observed_lessons
            if lesson["domain"] == low_domain
            for rule in lesson.get("focus_rules", [])
        }
        | set(BASE_RULE_BUDGETS[low_domain])
        | {str(rule) for case in query_cases if case.domain == low_domain for rule in case.all_rule_ids}
    )
    precision_guard_rules = sorted(
        {
            str(rule)
            for lesson in observed_lessons
            if lesson.get("pass_at_1")
            for rule in lesson.get("focus_rules", [])
        }
    ) or sorted({rule for domain_rules in BASE_RULE_BUDGETS.values() for rule in domain_rules})
    candidates = [
        {
            "candidate_id": "h0_base_conservative",
            "focus_domain": high_domain,
            "allowed_rules": high_domain_rules,
            "assumption": "Preserve currently successful domain behavior and avoid speculative expansion.",
            "status": "active",
            "weight": 1.0,
            "update_notes": [],
        },
        {
            "candidate_id": "h1_low_score_repair",
            "focus_domain": low_domain,
            "allowed_rules": low_domain_rules,
            "assumption": "Repair the weakest current domain by adding missing rule reminders.",
            "status": "active",
            "weight": 1.0,
            "update_notes": [],
        },
        {
            "candidate_id": "h2_precision_guard",
            "focus_domain": "cross_domain",
            "allowed_rules": precision_guard_rules,
            "assumption": "Prefer rules that previously stayed precise, even if that sacrifices broader coverage.",
            "status": "active",
            "weight": 1.0,
            "update_notes": [],
        },
        {
            "candidate_id": "h3_broad_union",
            "focus_domain": "cross_domain",
            "allowed_rules": sorted({rule for case in query_cases for rule in case.all_rule_ids}),
            "assumption": "Prefer wider teaching coverage even if immediate seed reward was lower.",
            "status": "active",
            "weight": 1.0,
            "update_notes": [],
        },
    ]
    return candidates


def _predict_candidate_rules(candidate: dict[str, Any], case: PilotCase) -> tuple[str, ...]:
    if candidate.get("status") == "eliminated":
        return ()
    focus_domain = candidate.get("focus_domain")
    if focus_domain not in (case.domain, "cross_domain"):
        return ()
    return predict_rules_from_visible_text(case.domain, case.joined_text, tuple(candidate.get("allowed_rules", ())))


def select_active_discriminative(
    query_cases: tuple[PilotCase, ...],
    source_lessons: list[dict[str, Any]],
    selected_query_lessons: list[dict[str, Any]],
    prior_candidates: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    observed_lessons = _observed_lessons(source_lessons, selected_query_lessons)
    candidates = _candidate_hypotheses(observed_lessons, query_cases, prior_candidates=prior_candidates)
    residual_rules_by_domain = _residual_rules_by_domain(observed_lessons)
    disagreement_rows: list[dict[str, Any]] = []
    scored: list[tuple[int, float, PilotCase]] = []
    for case in query_cases:
        predictions = []
        rule_sets = []
        union_predicted: set[str] = set()
        for candidate in candidates:
            predicted = _predict_candidate_rules(candidate, case)
            rule_sets.append(set(predicted))
            union_predicted.update(predicted)
            predictions.append(
                {
                    "candidate_id": candidate["candidate_id"],
                    "predicted_rule_ids": list(predicted),
                    "focus_domain": candidate["focus_domain"],
                    "status": candidate.get("status", "active"),
                    "weight": round(float(candidate.get("weight", 1.0)), 4),
                }
            )
        disagreement = 0.0
        comparisons = 0
        for left_index in range(len(rule_sets)):
            for right_index in range(left_index + 1, len(rule_sets)):
                left = rule_sets[left_index]
                right = rule_sets[right_index]
                union = left | right
                if union:
                    disagreement += 1.0 - (len(left & right) / len(union))
                comparisons += 1
        mean_disagreement = disagreement / comparisons if comparisons else 0.0
        repair_overlap = len(union_predicted & residual_rules_by_domain.get(case.domain, set()))
        disagreement_rows.append(
            {
                "case_id": case.case_id,
                "domain": case.domain,
                "predictions": predictions,
                "mean_pairwise_disagreement": round(mean_disagreement, 4),
                "repair_overlap": repair_overlap,
            }
        )
        scored.append((repair_overlap, mean_disagreement, case))
    scored.sort(key=lambda item: (-item[0], -item[1], item[2].case_id))
    selected = scored[0][2]
    return {
        "method": "active_discriminative_evidence",
        "selected_case_id": selected.case_id,
        "selection_reason": f"max_residual_repair_overlap_then_disagreement:overlap={scored[0][0]},disagreement={round(scored[0][1], 4)}",
        "candidates": candidates,
        "disagreement_matrix": disagreement_rows,
    }


def update_active_candidates(
    *,
    candidates: list[dict[str, Any]],
    case: PilotCase,
    query_run: dict[str, Any],
) -> list[dict[str, Any]]:
    actual_rule_ids = set(str(item) for item in query_run["evaluation"].get("seen_rule_ids", []))
    updated: list[dict[str, Any]] = []
    for candidate in candidates:
        next_candidate = dict(candidate)
        notes = list(candidate.get("update_notes", []))
        predicted_rule_ids = set(_predict_candidate_rules(candidate, case))
        focus_domain = str(candidate.get("focus_domain", "cross_domain"))
        out_of_scope = focus_domain not in (case.domain, "cross_domain")
        if out_of_scope or candidate.get("status") == "eliminated":
            notes.append(f"{case.case_id}: no update (candidate out of scope or already eliminated).")
            next_candidate["update_notes"] = notes
            updated.append(next_candidate)
            continue

        false_positive_rules = sorted(predicted_rule_ids - actual_rule_ids)
        missed_rules = sorted(actual_rule_ids - predicted_rule_ids)
        union = predicted_rule_ids | actual_rule_ids
        agreement = len(predicted_rule_ids & actual_rule_ids) / len(union) if union else 1.0
        revised_rules = set(str(item) for item in candidate.get("allowed_rules", []))
        revised_rules.update(actual_rule_ids)
        if case.clean_control:
            revised_rules.difference_update(predicted_rule_ids)
        else:
            revised_rules.difference_update(false_positive_rules)

        next_weight = float(candidate.get("weight", 1.0))
        if agreement < 0.25 and (false_positive_rules or missed_rules):
            next_candidate["status"] = "eliminated"
            next_weight *= 0.2
            notes.append(
                f"{case.case_id}: eliminated after low agreement={round(agreement, 4)}; missed={missed_rules}, false_positive={false_positive_rules}."
            )
        elif agreement < 0.6 or false_positive_rules or missed_rules:
            next_candidate["status"] = "downweighted"
            next_weight *= 0.6
            notes.append(
                f"{case.case_id}: downweighted after agreement={round(agreement, 4)}; missed={missed_rules}, false_positive={false_positive_rules}."
            )
        else:
            next_candidate["status"] = "active"
            next_weight *= 1.05
            notes.append(f"{case.case_id}: reinforced after agreement={round(agreement, 4)}.")

        next_candidate["weight"] = round(next_weight, 4)
        next_candidate["allowed_rules"] = sorted(revised_rules)
        next_candidate["last_observation"] = {
            "case_id": case.case_id,
            "predicted_rule_ids": sorted(predicted_rule_ids),
            "actual_rule_ids": sorted(actual_rule_ids),
            "agreement": round(agreement, 4),
            "missed_rule_ids": missed_rules,
            "false_positive_rule_ids": false_positive_rules,
        }
        next_candidate["update_notes"] = notes
        updated.append(next_candidate)
    return updated


def select_query_case(
    method_name: str,
    *,
    query_cases: tuple[PilotCase, ...],
    generation_cases: tuple[PilotCase, ...],
    source_lessons: list[dict[str, Any]],
    selected_query_lessons: list[dict[str, Any]],
    seed: int,
    prior_candidates: list[dict[str, Any]] | None = None,
    observed_cases: tuple[PilotCase, ...] | None = None,
) -> dict[str, Any]:
    if method_name == "random":
        return select_random_query(query_cases, seed=seed)
    if method_name == "top_reward_success_only":
        return select_top_reward_success_only(query_cases, _observed_lessons(source_lessons, selected_query_lessons))
    if method_name == "success_failure_contrast":
        return select_success_failure_contrast(query_cases, _observed_lessons(source_lessons, selected_query_lessons))
    if method_name == "diversity":
        return select_diversity(query_cases, observed_cases or generation_cases)
    if method_name == "active_discriminative_evidence":
        return select_active_discriminative(query_cases, source_lessons, selected_query_lessons, prior_candidates=prior_candidates)
    raise ValueError(f"unknown method: {method_name}")
