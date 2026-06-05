from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


OUT_DIR = Path("outputs/mvp_vertical_slice/compressed_candidate_execution_001")
SEMANTIC_VERIFIER_DIR = Path("outputs/mvp_vertical_slice/semantic_verifier_001")
CANDIDATE_SKILL = Path("outputs/mvp_vertical_slice/validation_aware_compiler_001/candidate_skills/candidate_C_compressed_required_rules.md")
CASES = {
    "case001": Path("data/harbor_api_review_tasks/api-review-001-compact-v1/case_001_openapi.md"),
    "case002": Path("data/harbor_api_review_tasks/api-review-002-compact-v1/case_002_openapi.md"),
}


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, text=True, capture_output=True, check=False)


def extract_rule_ids(review_path: Path) -> list[str]:
    if not review_path.exists():
        return []
    payload = read_json(review_path)
    findings = payload.get("findings") if isinstance(payload, dict) else []
    if not isinstance(findings, list):
        return []
    return sorted({str(finding.get("rule_id")) for finding in findings if isinstance(finding, dict) and finding.get("rule_id")})


def verify_outputs(review_path: Path, case_path: Path, run_dir: Path) -> dict[str, Any]:
    local_verify_path = run_dir / "verification_result.json"
    semantic_verify_path = run_dir / "semantic_verification_result.json"
    if review_path.exists():
        run_command([sys.executable, "scripts/verify_api_review_json.py", "--review", str(review_path), "--output", str(local_verify_path)])
        run_command(
            [
                sys.executable,
                "scripts/verify_api_review_semantic_json.py",
                "--review",
                str(review_path),
                "--case",
                str(case_path),
                "--output",
                str(semantic_verify_path),
            ]
        )
    local = read_json(local_verify_path) if local_verify_path.exists() else None
    semantic = read_json(semantic_verify_path) if semantic_verify_path.exists() else None
    return {
        "local_verification": str(local_verify_path) if local else None,
        "semantic_verification": str(semantic_verify_path) if semantic else None,
        "local_passed": local.get("passed") if local else None,
        "semantic_passed": semantic.get("passed") if semantic else None,
        "missing_rule_ids": semantic.get("missing_rule_ids") if semantic else (local.get("missing_rule_ids") if local else []),
        "semantic_errors": semantic.get("semantic_errors") if semantic else [],
    }


def run_mock_case(case_id: str, case_path: Path) -> dict[str, Any]:
    run_dir = OUT_DIR / f"{case_id}_mock_candidate_C"
    review_path = run_dir / "review.json"
    cmd = [
        sys.executable,
        "agents/api_review_mock_agent.py",
        "--compact-skill",
        str(CANDIDATE_SKILL),
        "--case",
        str(case_path),
        "--output",
        str(review_path),
    ]
    result = run_command(cmd)
    verification = verify_outputs(review_path, case_path, run_dir)
    return {
        "case": case_id,
        "agent": "mock",
        "candidate": "candidate_C_compressed_required_rules",
        "review": str(review_path) if review_path.exists() else None,
        "agent_exit_code": result.returncode,
        "agent_status": "ok" if result.returncode == 0 else "failed",
        "generated_review_rule_ids": extract_rule_ids(review_path),
        "verifier_passed": verification["local_passed"],
        "semantic_verifier_passed": verification["semantic_passed"],
        "missing_rule_ids": verification["missing_rule_ids"],
        "notes": "mock agent uses rule IDs from skill and deterministic findings; semantic verifier checks field and trigger content.",
        **verification,
    }


def run_llm_case(case_id: str, case_path: Path) -> dict[str, Any]:
    run_dir = OUT_DIR / f"{case_id}_rightcode_gpt_candidate_C"
    review_path = run_dir / "review.json"
    diagnostic_path = run_dir / "llm_agent_diagnostic.json"
    env_ready = all(os.environ.get(name) for name in ("OPENAI_BASE_URL", "OPENAI_API_KEY", "MODEL"))
    if not env_ready:
        diagnostic = {
            "status": "skipped",
            "reason": "OPENAI_BASE_URL, OPENAI_API_KEY, and MODEL must be set for external LLM execution.",
        }
        write_json(diagnostic_path, diagnostic)
        return {
            "case": case_id,
            "agent": "rightcode_gpt",
            "candidate": "candidate_C_compressed_required_rules",
            "review": None,
            "agent_exit_code": None,
            "agent_status": "skipped",
            "generated_review_rule_ids": [],
            "verifier_passed": None,
            "semantic_verifier_passed": None,
            "missing_rule_ids": [],
            "notes": diagnostic["reason"],
            "diagnostic": str(diagnostic_path),
        }
    cmd = [
        sys.executable,
        "agents/api_review_llm_agent.py",
        "--skill",
        str(CANDIDATE_SKILL),
        "--case",
        str(case_path),
        "--output",
        str(review_path),
        "--diagnostic",
        str(diagnostic_path),
    ]
    result = run_command(cmd)
    verification = verify_outputs(review_path, case_path, run_dir)
    diagnostic = read_json(diagnostic_path) if diagnostic_path.exists() else {"status": "missing_diagnostic"}
    return {
        "case": case_id,
        "agent": "rightcode_gpt",
        "candidate": "candidate_C_compressed_required_rules",
        "review": str(review_path) if review_path.exists() else None,
        "agent_exit_code": result.returncode,
        "agent_status": diagnostic.get("status"),
        "generated_review_rule_ids": extract_rule_ids(review_path),
        "verifier_passed": verification["local_passed"],
        "semantic_verifier_passed": verification["semantic_passed"],
        "missing_rule_ids": verification["missing_rule_ids"],
        "notes": "External LLM run; skipped if endpoint credentials are unavailable.",
        "diagnostic": str(diagnostic_path),
        **verification,
    }


def render_summary(summary: dict[str, Any]) -> str:
    lines = [
        "# Compressed Candidate Execution 001",
        "",
        "## Positioning",
        "",
        "This slice checks whether candidate_C can drive agent output beyond rule-id coverage, using both the existing local verifier and a stricter semantic verifier.",
        "",
        "| Case | Agent | Rule IDs | Local Pass | Semantic Pass | Missing | Notes |",
        "|---|---|---|---|---|---|---|",
    ]
    for run in summary["runs"]:
        lines.append(
            f"| {run['case']} | {run['agent']} | {', '.join(run['generated_review_rule_ids']) or 'none'} | "
            f"{run['verifier_passed']} | {run['semantic_verifier_passed']} | "
            f"{', '.join(run['missing_rule_ids']) if run['missing_rule_ids'] else 'none'} | {run['notes']} |"
        )
    lines.extend(
        [
            "",
            "## Conclusion",
            "",
            f"- Status: {summary['conclusion_status']}",
            f"- Finding: {summary['finding']}",
            f"- Boundary: {summary['boundary']}",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    SEMANTIC_VERIFIER_DIR.mkdir(parents=True, exist_ok=True)
    runs = []
    for case_id, case_path in CASES.items():
        runs.append(run_mock_case(case_id, case_path))
    for case_id, case_path in CASES.items():
        runs.append(run_llm_case(case_id, case_path))
    mock_runs = [run for run in runs if run["agent"] == "mock"]
    llm_runs = [run for run in runs if run["agent"] == "rightcode_gpt"]
    mock_semantic_pass = all(run["semantic_verifier_passed"] is True for run in mock_runs)
    llm_attempted = any(run["agent_status"] != "skipped" for run in llm_runs)
    llm_semantic_pass = all(run["semantic_verifier_passed"] is True for run in llm_runs if run["agent_status"] != "skipped")
    if mock_semantic_pass and (not llm_attempted or llm_semantic_pass):
        conclusion_status = "partially_supported"
        finding = "Candidate_C passes semantic execution validation for available agents in this toy slice."
    elif mock_semantic_pass and llm_attempted:
        conclusion_status = "partially_supported_for_artifact_compilation_not_yet_llm_execution"
        finding = "Candidate_C passes mock/semantic execution but not all LLM semantic checks."
    else:
        conclusion_status = "inconclusive"
        finding = "Candidate_C did not pass semantic execution validation."
    created_at = datetime.now(timezone.utc).isoformat()
    summary = {
        "run_id": OUT_DIR.name,
        "created_at": created_at,
        "candidate": str(CANDIDATE_SKILL),
        "layer": "compressed_candidate_execution",
        "env_ready": all(os.environ.get(name) for name in ("OPENAI_BASE_URL", "OPENAI_API_KEY", "MODEL")),
        "model": os.environ.get("MODEL"),
        "runs": runs,
        "conclusion_status": conclusion_status,
        "finding": finding,
        "boundary": "Toy execution validation only. Passing this slice does not prove a general fixed-budget compiler.",
    }
    write_json(OUT_DIR / "summary.json", summary)
    write_json(OUT_DIR / "execution_results.json", runs)
    write_json(
        SEMANTIC_VERIFIER_DIR / "summary.json",
        {
            "run_id": SEMANTIC_VERIFIER_DIR.name,
            "created_at": created_at,
            "source_run": str(OUT_DIR),
            "semantic_verifier": "scripts/verify_api_review_semantic_json.py",
            "runs": [
                {
                    "case": run["case"],
                    "agent": run["agent"],
                    "semantic_verifier_passed": run["semantic_verifier_passed"],
                    "semantic_verification": run.get("semantic_verification"),
                    "semantic_errors": run.get("semantic_errors"),
                }
                for run in runs
            ],
            "boundary": "Lightweight keyword/field semantic verifier; not complex NLP.",
        },
    )
    write_json(
        OUT_DIR / "manifest.json",
        {
            "run_id": OUT_DIR.name,
            "created_at": created_at,
            "artifacts": ["summary.json", "execution_results.json", "summary.md"],
            "boundary": summary["boundary"],
        },
    )
    write_json(
        SEMANTIC_VERIFIER_DIR / "manifest.json",
        {
            "run_id": SEMANTIC_VERIFIER_DIR.name,
            "created_at": created_at,
            "artifacts": ["summary.json"],
            "boundary": "Semantic verifier output for compressed candidate execution.",
        },
    )
    write_json(OUT_DIR / "llm_diagnostic_summary.json", {"env_ready": summary["env_ready"], "model": summary["model"]})
    (OUT_DIR / "summary.md").write_text(render_summary(summary), encoding="utf-8", newline="\n")
    print(json.dumps({"output_dir": str(OUT_DIR), "conclusion_status": conclusion_status, "env_ready": summary["env_ready"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

