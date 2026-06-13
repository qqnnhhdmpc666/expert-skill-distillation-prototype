from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence

from .capability_registry import CAPABILITY_SPECS
from .evidence import write_json, write_text
from .schemas import SkillPackage
from .task_cases import ControlledTaskCase


DISTILLATION_HINTS: dict[str, tuple[str, ...]] = {
    "UPLOAD_TYPE_MAGIC": ("content validation", "mime", "magic", "extension"),
    "UPLOAD_PATH_ISOLATION": ("path isolation", "non-public storage", "storage"),
    "UPLOAD_AUDIT_RETENTION": ("audit retention", "audit", "retention"),
    "AUTH_SCOPE_MATRIX": ("role/scope authorization", "role", "scope", "authorization"),
    "AUTH_OBJECT_OWNERSHIP": ("object ownership", "ownership", "tenant boundary", "tenant"),
    "AUTH_ERROR_ENVELOPE": ("error envelope", "error", "envelope"),
    "CONFIG_AUDIT_EXPORT": ("audit retention", "export sinks", "export sink", "audit"),
    "CONFIG_ENV_GUARD": ("separate prod from dev/test", "prod", "dev/test", "debug state"),
    "API_SCHEMA_CONTRACT": ("strict json report contract", "json report contract", "evidence spans", "fix specificity"),
    "API_OVERBROAD_RISK": ("overbroad generic findings", "overbroad", "generic findings"),
    "DATA_REQUIRED_FIELD_COVERAGE": ("missing-column issues", "required field", "row sample"),
    "DATA_TEMPORAL_SPLIT_GUARD": ("temporal split hygiene", "cutoff rule", "offending row id"),
    "DATA_LABEL_ENUM_ALIGNMENT": ("label values", "declared contract", "unexpected label token"),
    "PATCH_TEST_FAILURE_REPRO": ("failing test", "test failure", "regression assertion"),
    "PATCH_MINIMAL_CODE_CHANGE": ("minimal patch", "small source change", "behavior-preserving"),
    "PATCH_REGRESSION_VALIDATION": ("targeted test", "regression validation", "validation command"),
}


@dataclass(frozen=True)
class CapabilityProjection:
    capability_id: str
    title: str
    source_span: str
    matched_keywords: tuple[str, ...]
    score: int
    selected: bool
    source_case_id: str
    task_family: str


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def split_clauses(text: str) -> list[str]:
    normalized = " ".join(text.split())
    if not normalized:
        return []
    clauses: list[str] = []
    for chunk in normalized.replace(";", ".").split("."):
        chunk = chunk.strip()
        if not chunk:
            continue
        parts = [part.strip(" -") for part in chunk.split(",")]
        clauses.extend(part for part in parts if part)
    return clauses or [normalized]


def hint_keywords(capability_id: str) -> tuple[str, ...]:
    spec = CAPABILITY_SPECS[capability_id]
    merged = list(DISTILLATION_HINTS.get(capability_id, ()))
    merged.extend(needle for needle in spec.detector_needles if needle not in merged)
    return tuple(merged)


def project_capability(expert_material: str, capability_id: str, *, case_id: str, task_family: str) -> CapabilityProjection:
    hints = [item.lower() for item in hint_keywords(capability_id)]
    best_clause = expert_material.strip()
    best_hits: list[str] = []
    best_score = 0
    for clause in split_clauses(expert_material):
        lowered = clause.lower()
        hits = [hint for hint in hints if hint in lowered]
        if len(hits) > best_score:
            best_score = len(hits)
            best_hits = hits
            best_clause = clause
    spec = CAPABILITY_SPECS[capability_id]
    return CapabilityProjection(
        capability_id=capability_id,
        title=spec.title,
        source_span=best_clause,
        matched_keywords=tuple(best_hits),
        score=best_score,
        selected=best_score > 0,
        source_case_id=case_id,
        task_family=task_family,
    )


def project_case_capabilities(case: ControlledTaskCase, allowed_capabilities: Sequence[str] | None = None) -> list[CapabilityProjection]:
    universe = tuple(allowed_capabilities or case.expected_capabilities)
    projections = [project_capability(case.expert_material, capability_id, case_id=case.case_id, task_family=case.task_family) for capability_id in universe]
    selected = [item for item in projections if item.selected]
    if selected:
        return selected
    raise ValueError(f"no capabilities were distilled from expert material for case `{case.case_id}`")


def normalize_group_payload(name: str, task_family: str, capabilities: Iterable[str], source_cases: Iterable[str]) -> dict[str, Any]:
    return {
        "name": name,
        "task_families": [task_family] if task_family else [],
        "capabilities": list(dict.fromkeys(str(item) for item in capabilities if str(item).strip())),
        "source_cases": list(dict.fromkeys(str(item) for item in source_cases if str(item).strip())),
    }


def render_root_skill_markdown(skill_id: str, versions: Sequence[str], supported_families: Sequence[str]) -> str:
    return "\n".join(
        [
            f"# {skill_id}",
            "",
            "This is an installable Codex Skill bundle generated through expert-material distillation.",
            "",
            "## Closed Loop",
            "",
            "expert materials -> distilled Skill package -> installed runtime execution -> verifier/evidence feedback -> candidate evolution",
            "",
            f"- available_versions: {', '.join(f'`{item}`' for item in versions)}",
            f"- supported_task_families: {', '.join(f'`{item}`' for item in supported_families)}",
            "",
            "## Safety Boundary",
            "",
            "- Defensive review only.",
            "- No exploit generation, no attack-chain execution, no unauthorized target testing.",
            "",
        ]
    ) + "\n"


def render_version_skill_markdown(
    *,
    skill_id: str,
    version: str,
    task_family: str,
    capability_groups: Sequence[dict[str, Any]],
    source_cases: Sequence[str],
    distillation_method: str,
) -> str:
    lines = [
        f"# {skill_id} Installed Runtime {version}",
        "",
        "This installed runtime was distilled from expert materials, not manually written as a one-off prompt.",
        "",
        "## Distillation Metadata",
        "",
        f"- distillation_method: `{distillation_method}`",
        f"- runtime_task_family: `{task_family}`",
        f"- source_cases: {', '.join(f'`{item}`' for item in source_cases)}",
        "",
        "## Capability Groups",
        "",
    ]
    for group in capability_groups:
        lines.append(f"### {group['name']}")
        lines.append(f"- task_families: {', '.join(f'`{item}`' for item in group.get('task_families', [])) or '`none`'}")
        if group.get("source_cases"):
            lines.append(f"- distilled_from: {', '.join(f'`{item}`' for item in group['source_cases'])}")
        lines.append("- capabilities:")
        if group.get("capabilities"):
            for capability_id in group["capabilities"]:
                lines.append(f"  - `{capability_id}`: {CAPABILITY_SPECS[capability_id].title}")
        else:
            lines.append("  - none")
        lines.append("")
    lines.extend(
        [
            "## Output Contract",
            "",
            "- `capability_id`",
            "- `evidence_span`",
            "- `recommended_fix`",
            "",
            "## Safety Boundary",
            "",
            "- Defensive review only.",
            "- Unsupported task families must activate `out_of_scope_guard` and avoid unrelated findings.",
            "",
        ]
    )
    return "\n".join(lines)


def build_root_manifest(skill_id: str, version: str, versions: Sequence[str], supported_families: Sequence[str], title: str) -> dict[str, Any]:
    return {
        "skill_id": skill_id,
        "package_type": "distilled_codex_skill_bundle",
        "created_at": utc_now(),
        "name": title,
        "default_version": version,
        "available_versions": list(versions),
        "supported_task_families": list(supported_families),
        "distillation_method": "keyword_projection_from_expert_materials",
        "deployment_shape": "codex_skill_plus_cli",
        "safety_boundary": {
            "allowed": ["defensive_detection", "explanation", "fix_recommendation", "patch_validation"],
            "forbidden": ["exploit_generation", "attack_chain_execution", "unauthorized_target_testing"],
        },
    }


def build_version_manifest(
    *,
    skill_id: str,
    version: str,
    task_family: str,
    capability_groups: Sequence[dict[str, Any]],
    source_cases: Sequence[str],
) -> dict[str, Any]:
    capabilities: list[str] = []
    supported_families: list[str] = []
    for group in capability_groups:
        for capability_id in group.get("capabilities", []):
            if capability_id not in capabilities:
                capabilities.append(capability_id)
        for family in group.get("task_families", []):
            if family not in supported_families:
                supported_families.append(family)
    package = SkillPackage(
        skill_id=skill_id,
        version=version,
        task_family=task_family,
        capabilities=tuple(capabilities),
        output_contract=("capability_id", "evidence_span", "recommended_fix"),
        trace_contract=("trajectory.jsonl", "target_reads.json", "skill_reads.json"),
        metadata={
            "package_role": "expert_distilled_runtime",
            "distillation_method": "keyword_projection_from_expert_materials",
            "supported_task_families": supported_families,
            "capability_groups": list(capability_groups),
            "source_cases": list(source_cases),
            "out_of_scope_group": "out_of_scope_guard",
            "distillation_provenance_dir": "provenance",
        },
    )
    return package.to_dict()


def distill_skill_bundle(
    *,
    skill_id: str,
    version: str,
    cases: Sequence[ControlledTaskCase],
    output_dir: Path,
    title: str | None = None,
) -> dict[str, Any]:
    if not cases:
        raise ValueError("at least one controlled task case is required for distillation")
    title = title or f"{skill_id} Expert-Distilled Skill"
    output_dir.mkdir(parents=True, exist_ok=True)
    version_dir = output_dir / "versions" / version
    provenance_dir = version_dir / "provenance"

    projections: list[CapabilityProjection] = []
    capability_groups: list[dict[str, Any]] = []
    source_manifest: list[dict[str, Any]] = []
    supported_families: list[str] = []
    for case in cases:
        case_projections = project_case_capabilities(case)
        projections.extend(case_projections)
        selected_capabilities = [item.capability_id for item in case_projections]
        capability_groups.append(normalize_group_payload(case.task_family, case.task_family, selected_capabilities, [case.case_id]))
        source_manifest.append(
            {
                "case_id": case.case_id,
                "title": case.title,
                "task_family": case.task_family,
                "source_dir": case.source_dir,
                "selected_capabilities": selected_capabilities,
                "expert_material_preview": case.expert_material[:240],
            }
        )
        if case.task_family not in supported_families:
            supported_families.append(case.task_family)
    capability_groups.append({"name": "out_of_scope_guard", "task_families": [], "capabilities": [], "source_cases": []})

    task_family = supported_families[0] if len(supported_families) == 1 else "multi_task_expert_distilled"
    manifest = build_version_manifest(
        skill_id=skill_id,
        version=version,
        task_family=task_family,
        capability_groups=capability_groups,
        source_cases=[case.case_id for case in cases],
    )
    version_skill = render_version_skill_markdown(
        skill_id=skill_id,
        version=version,
        task_family=task_family,
        capability_groups=capability_groups,
        source_cases=[case.case_id for case in cases],
        distillation_method="keyword_projection_from_expert_materials",
    )

    existing_root = {}
    root_manifest_path = output_dir / "manifest.json"
    if root_manifest_path.exists():
        import json

        existing_root = json.loads(root_manifest_path.read_text(encoding="utf-8-sig"))
    versions = sorted({*(existing_root.get("available_versions", []) or []), version})
    root_manifest = build_root_manifest(skill_id, version, versions, supported_families, title)

    extracted_candidates = [
        {
            "case_id": item.source_case_id,
            "task_family": item.task_family,
            "capability_id": item.capability_id,
            "title": item.title,
            "source_span": item.source_span,
            "matched_keywords": list(item.matched_keywords),
            "score": item.score,
            "selected": item.selected,
        }
        for item in projections
    ]
    capability_provenance = [
        {
            "capability_id": item.capability_id,
            "title": item.title,
            "task_family": item.task_family,
            "source_case_id": item.source_case_id,
            "source_span": item.source_span,
            "matched_keywords": list(item.matched_keywords),
            "projection_score": item.score,
            "selection_rule": "selected_when_keyword_projection_score_gt_zero",
        }
        for item in projections
    ]
    distillation_trace = {
        "generated_at": utc_now(),
        "skill_id": skill_id,
        "version": version,
        "method": "keyword_projection_from_expert_materials",
        "boundary": "This is a real distillation path for controlled expert materials. It is not an open-world semantic induction claim.",
        "steps": [
            {"stage": "load_source_materials", "artifact": "provenance/source_materials_manifest.json"},
            {"stage": "project_capabilities", "artifact": "provenance/extracted_candidates.json"},
            {"stage": "compile_runtime_manifest", "artifact": "manifest.json"},
            {"stage": "render_skill_text", "artifact": "SKILL.md"},
        ],
    }

    write_text(output_dir / "SKILL.md", render_root_skill_markdown(skill_id, versions, supported_families))
    write_json(output_dir / "manifest.json", root_manifest)
    write_text(
        output_dir / "README.md",
        "\n".join(
            [
                f"# {skill_id}",
                "",
                "This bundle was generated from expert materials through `skill-deploy distill-skill`.",
                "",
                "```powershell",
                f"skill-deploy install --skill {output_dir.as_posix()} --version {version}",
                "```",
                "",
            ]
        )
        + "\n",
    )
    write_text(version_dir / "SKILL.md", version_skill)
    write_json(version_dir / "manifest.json", manifest)
    write_json(
        provenance_dir / "source_materials_manifest.json",
        {
            "sources": source_manifest,
            "source_case_count": len(source_manifest),
            "supported_task_families": supported_families,
        },
    )
    for case in cases:
        write_text(provenance_dir / "source_materials" / f"{case.case_id}.md", case.expert_material + "\n")
    write_json(provenance_dir / "extracted_candidates.json", extracted_candidates)
    write_json(provenance_dir / "capability_provenance.json", capability_provenance)
    write_json(provenance_dir / "distillation_trace.json", distillation_trace)
    write_json(
        output_dir / "eval" / "smoke_cases.json",
        {
            "distilled_skill_id": skill_id,
            "version": version,
            "cases": [
                {
                    "case_id": case.case_id,
                    "command": f"skill-deploy run-skill --installed {skill_id} --case {case.case_id} --backend offline_deterministic",
                }
                for case in cases
            ],
        },
    )
    write_json(
        output_dir / "examples" / "distillation_summary.json",
        {
            "skill_id": skill_id,
            "version": version,
            "source_cases": [case.case_id for case in cases],
            "selected_capability_count": len({item.capability_id for item in projections}),
            "supported_task_families": supported_families,
        },
    )
    return {
        "skill_id": skill_id,
        "version": version,
        "output_dir": str(output_dir),
        "version_dir": str(version_dir),
        "supported_task_families": supported_families,
        "selected_capabilities": sorted({item.capability_id for item in projections}),
        "source_cases": [case.case_id for case in cases],
        "distillation_method": "keyword_projection_from_expert_materials",
    }
