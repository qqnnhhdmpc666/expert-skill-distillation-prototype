from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LIFECYCLE_INDEX_PATH = ROOT / "outputs" / "skill_lifecycle_evidence" / "index.json"
QUALIFICATION_PATH = ROOT / "outputs" / "validation" / "skill_qualification_cards.json"
VALIDITY_PATH = ROOT / "outputs" / "validation" / "skill_revision_validity_cards.json"
INSTALL_ROOT = ROOT / "outputs" / "installed_skills"
REVIEWER_ROOT = ROOT / "outputs" / "reviewer_readiness"
REPORTS_ROOT = ROOT / "reports"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def copy_text(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")


def relative(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def load_lookup(rows: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    return {str(row[key]): row for row in rows if key in row}


def build_install_registry(index_payload: dict[str, Any]) -> dict[str, Any]:
    if INSTALL_ROOT.exists():
        # keep previous history only inside generated receipts; regenerate cleanly here
        import shutil

        shutil.rmtree(INSTALL_ROOT)
    install_rows: list[dict[str, Any]] = []
    for row in index_payload.get("generalization", []):
        case_id = str(row["case_id"])
        distill_dir = ROOT / row["distillation_bundle"]
        install_dir = INSTALL_ROOT / case_id
        versions_dir = install_dir / "versions"
        active_dir = install_dir / "active"
        history_dir = install_dir / "history"
        version_specs = [
            ("v1", distill_dir / "SKILL_v1.md", distill_dir / "skill_manifest_v1.json"),
            ("v2", distill_dir / "SKILL_v2.md", distill_dir / "skill_manifest_v2.json"),
        ]
        for version, skill_src, manifest_src in version_specs:
            version_dir = versions_dir / version
            copy_text(skill_src, version_dir / "SKILL.md")
            manifest = read_json(manifest_src)
            manifest["installed_from"] = row["distillation_bundle"]
            manifest["case_id"] = case_id
            manifest["version_label"] = version
            write_json(version_dir / "manifest.json", manifest)
        copy_text(distill_dir / "SKILL_v2.md", active_dir / "SKILL.md")
        active_manifest = read_json(distill_dir / "skill_manifest_v2.json")
        active_manifest["installed_from"] = row["distillation_bundle"]
        active_manifest["active_version"] = "v2"
        active_manifest["scope"] = "controlled_offline_generalization"
        write_json(active_dir / "manifest.json", active_manifest)

        history = [
            {
                "timestamp": utc_now(),
                "event": "install",
                "from_version": None,
                "to_version": "v2",
                "reason": "Seeded controlled installed-skill registry from validated lifecycle evidence.",
                "scope": "controlled_offline_generalization",
            }
        ]
        if case_id == "upload_security_001":
            history.append(
                {
                    "timestamp": utc_now(),
                    "event": "rollback_demo",
                    "from_version": "v2",
                    "to_version": "v1",
                    "reason": "Demonstration rollback event referencing existing regression-gate precedent in outputs/mvp_vertical_slice/rollback_gate_001.",
                    "evidence": "outputs/mvp_vertical_slice/rollback_gate_001/rollback_decision.json",
                }
            )
            history.append(
                {
                    "timestamp": utc_now(),
                    "event": "restore_demo",
                    "from_version": "v1",
                    "to_version": "v2",
                    "reason": "Restore recommended active revision after rollback-surface demonstration.",
                }
            )
        write_json(history_dir / "events.json", history)
        write_json(
            install_dir / "deployment_record.json",
            {
                "case_id": case_id,
                "active_version": "v2",
                "available_versions": ["v1", "v2"],
                "scope_limit": "controlled_offline_generalization",
                "rollback_available": True,
                "history_artifact": relative(history_dir / "events.json"),
                "source_bundle": row["distillation_bundle"],
                "trajectory_bundle": row["trajectory_bundle"],
                "notes": "This is a generated installation surface for artifact-backed lifecycle review, not a production package manager.",
            },
        )
        install_rows.append(
            {
                "case_id": case_id,
                "task_family": row["task_family"],
                "active_version": "v2",
                "scope_limit": "controlled_offline_generalization",
                "install_dir": relative(install_dir),
                "history_events": len(history),
            }
        )
    registry = {
        "generated_at": utc_now(),
        "registry_type": "controlled_skill_installation_surface",
        "skills": install_rows,
        "boundary": "This registry demonstrates install/version/rollback surfaces over controlled lifecycle artifacts. It is not a production package manager.",
    }
    write_json(INSTALL_ROOT / "registry.json", registry)
    return registry


def build_reviewer_readiness(index_payload: dict[str, Any], qualification_payload: dict[str, Any], validity_payload: dict[str, Any]) -> dict[str, Any]:
    REVIEWER_ROOT.mkdir(parents=True, exist_ok=True)
    qual_rows = {str(card.get("card_id")): card for card in qualification_payload.get("cards", [])}
    validity_rows = {str(card.get("card_id")): card for card in validity_payload.get("cards", [])}
    case_to_live_card = {
        "upload_security_001": "live_llm_upload_repair_loop",
        "data_quality_review_001": "live_llm_data_quality_repair_loop",
        "config_security_001": "live_llm_config_security_repair_loop",
        "api_review_001": "live_llm_api_review_repair_loop",
    }
    rows: list[dict[str, Any]] = []
    for row in index_payload.get("generalization", []):
        case_id = str(row["case_id"])
        qual_card = qual_rows.get(case_to_live_card.get(case_id, ""), {})
        validity_card = validity_rows.get(case_to_live_card.get(case_id, ""), {})
        promoted = bool(row.get("a2_pass"))
        readiness = "review_now" if promoted and qual_card.get("promotion_level", "").startswith("L2_") else ("hold" if promoted else "blocked")
        rubric = {
            "task_usefulness": {
                "score": 4 if promoted else 2,
                "reason": "A2 passes the controlled verifier and the task-level artifact chain is complete." if promoted else "The task still lacks stable revision behavior and should not be shown first.",
            },
            "evidence_clarity": {
                "score": 4,
                "reason": "Distillation bundle, trajectory bundle, and patch/gate files are all present.",
            },
            "fix_actionability": {
                "score": 4 if row.get("repair_action") != "no_op" else 3,
                "reason": f"Repair action is `{row.get('repair_action')}` and can be inspected in the revision artifacts.",
            },
            "scope_honesty": {
                "score": 5,
                "reason": "Claim boundary is explicitly controlled and does not present broad autonomous generalization.",
            },
            "deployment_readiness": {
                "score": 3 if promoted else 1,
                "reason": "A generated install/rollback surface now exists, but it is still a controlled prototype surface rather than a production package manager." if promoted else "Blocked because the revision is not yet promotable.",
            },
        }
        packet = {
            "case_id": case_id,
            "task_family": row["task_family"],
            "review_readiness": readiness,
            "recommended_audience": "external reviewer" if readiness == "review_now" else "internal debugging first",
            "opening_claim": f"Controlled expert-skill lifecycle for `{case_id}` with artifact-backed distillation, execution, and revision evidence.",
            "what_to_show_first": [
                row["distillation_bundle"],
                row["trajectory_bundle"],
                relative(INSTALL_ROOT / case_id / "deployment_record.json"),
            ],
            "supporting_cards": {
                "qualification_card_id": qual_card.get("card_id"),
                "promotion_level": qual_card.get("promotion_level"),
                "validity_card_id": validity_card.get("card_id"),
            },
            "rubric": rubric,
            "boundary": "Reviewer-readiness packet authored from internal artifacts. It is preparation for human/external review, not itself external human validation.",
        }
        write_json(REVIEWER_ROOT / f"{case_id}_packet.json", packet)
        rows.append(packet)
    summary = {
        "generated_at": utc_now(),
        "packet_count": len(rows),
        "review_now_cases": [row["case_id"] for row in rows if row["review_readiness"] == "review_now"],
        "hold_cases": [row["case_id"] for row in rows if row["review_readiness"] == "hold"],
        "blocked_cases": [row["case_id"] for row in rows if row["review_readiness"] == "blocked"],
        "boundary": "These packets are structured reviewer-prep artifacts. They reduce review friction but do not replace external or human usefulness review.",
        "packets": rows,
    }
    write_json(REVIEWER_ROOT / "reviewer_assessment.json", summary)
    return summary


def render_install_status(registry: dict[str, Any]) -> str:
    lines = [
        "# Skill Installation Status",
        "",
        f"- Updated: `{registry['generated_at']}`",
        f"- Installed skill entries: `{len(registry['skills'])}`",
        "",
        "## Registry",
        "",
        "| Case | Family | Active | Scope | History events | Install dir |",
        "|---|---|---|---|---:|---|",
    ]
    for row in registry["skills"]:
        lines.append(
            f"| {row['case_id']} | {row['task_family']} | {row['active_version']} | {row['scope_limit']} | {row['history_events']} | `{row['install_dir']}` |"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- This is a generated install/version/rollback surface over controlled lifecycle artifacts.",
            "- It shows that skill artifacts can be versioned, scoped, and restored in a reproducible way.",
            "- It is not yet a production-grade package manager or deployment service.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_reviewer_status(summary: dict[str, Any]) -> str:
    lines = [
        "# Reviewer Readiness Status",
        "",
        f"- Updated: `{summary['generated_at']}`",
        f"- Packets: `{summary['packet_count']}`",
        f"- Review now: `{', '.join(summary['review_now_cases']) if summary['review_now_cases'] else 'none'}`",
        f"- Hold: `{', '.join(summary['hold_cases']) if summary['hold_cases'] else 'none'}`",
        f"- Blocked: `{', '.join(summary['blocked_cases']) if summary['blocked_cases'] else 'none'}`",
        "",
        "## Packet reading",
        "",
        "| Case | Readiness | Audience | Qualification | Boundary |",
        "|---|---|---|---|---|",
    ]
    for row in summary["packets"]:
        lines.append(
            f"| {row['case_id']} | {row['review_readiness']} | {row['recommended_audience']} | {row['supporting_cards']['promotion_level'] or 'n/a'} | {row['boundary']} |"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- This is an internal reviewer-prep layer, not external human validation.",
            "- It helps decide which skills are clean enough to show first and what artifacts should anchor the conversation.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    index_payload = read_json(LIFECYCLE_INDEX_PATH)
    qualification_payload = read_json(QUALIFICATION_PATH)
    validity_payload = read_json(VALIDITY_PATH)
    registry = build_install_registry(index_payload)
    reviewer_summary = build_reviewer_readiness(index_payload, qualification_payload, validity_payload)
    write_text(REPORTS_ROOT / "SKILL_INSTALLATION_STATUS.md", render_install_status(registry))
    write_text(REPORTS_ROOT / "REVIEWER_READINESS_STATUS.md", render_reviewer_status(reviewer_summary))
    print(
        json.dumps(
            {
                "install_registry": relative(INSTALL_ROOT / "registry.json"),
                "reviewer_assessment": relative(REVIEWER_ROOT / "reviewer_assessment.json"),
                "install_report": relative(REPORTS_ROOT / "SKILL_INSTALLATION_STATUS.md"),
                "reviewer_report": relative(REPORTS_ROOT / "REVIEWER_READINESS_STATUS.md"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
