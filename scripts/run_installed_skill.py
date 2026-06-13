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

from skill_deployment import (  # noqa: E402
    get_backend_runner,
    hash_file_sha256,
    hash_json_file_sha256,
    resolve_installed_skill,
    resolve_task_conditioned_activation,
    select_controlled_task_cases,
    verify_controlled_execution,
    write_evidence_bundle,
    RunnerContext,
)
from skill_deployment.evidence import write_json, write_text  # noqa: E402


DATA_ROOT = ROOT / "data" / "task_cases"
OUTPUT_ROOT = ROOT / "outputs" / "runtime_runs" / "installed_skills"


def run_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run one case through the installed Skill runtime path.")
    parser.add_argument("--installed", required=True)
    parser.add_argument("--case", required=True)
    parser.add_argument("--backend", default="offline_deterministic")
    parser.add_argument("--output-dir", default=str(OUTPUT_ROOT))
    args = parser.parse_args(argv)

    case = select_controlled_task_cases(DATA_ROOT, args.case)[0]
    resolved = resolve_installed_skill(ROOT, args.installed)
    skill_dir = resolved["skill_dir"]
    skill_package = resolved["skill_package"]
    skill_text = resolved["skill_text"]
    activation = resolve_task_conditioned_activation(skill_package, case)
    run_id = f"{run_stamp()}_{skill_package.version}"
    out_dir = Path(args.output_dir) / args.installed / case.case_id / run_id
    target_dir = out_dir / "target"
    write_text(target_dir / "target.md", case.target_asset)
    runner = get_backend_runner(args.backend, project_root=ROOT)
    context = RunnerContext(
        scenario_id=case.case_id,
        backend=args.backend,
        target_dir=target_dir,
        output_dir=out_dir / "agent",
        attempt_id=f"installed_{skill_package.version}",
        skill_package=skill_package,
        task_case=case,
        metadata={
            "skill_dir": skill_dir,
            "skill_package_path": str(skill_dir),
            "skill_version": skill_package.version,
            "manifest_hash": hash_json_file_sha256(skill_dir / "manifest.json"),
            "skill_hash": hash_file_sha256(skill_dir / "SKILL.md"),
            "task_family": case.task_family,
            "activated_capability_group": activation["activated_capability_group"],
            "supported_task_families": activation["supported_task_families"],
            "out_of_scope": activation["out_of_scope"],
            "unsupported_task_family": activation["unsupported_task_family"],
        },
    )
    result = runner.run(context)
    execution = result.report.to_dict()
    verifier = verify_controlled_execution(
        case.expected_capabilities,
        execution,
        feedback_overrides=case.verifier_contract.get("feedback_overrides", {}),
        target_text=case.target_asset,
    ).to_dict()
    write_json(out_dir / "verifier_report.json", verifier)
    provenance = {
        "runtime_source": "installed_skill_package",
        "skill_package_path": str(skill_dir),
        "skill_version": skill_package.version,
        "manifest_hash": hash_json_file_sha256(skill_dir / "manifest.json"),
        "skill_hash": hash_file_sha256(skill_dir / "SKILL.md"),
        "task_family": case.task_family,
        "activated_capability_group": activation["activated_capability_group"],
        "supported_task_families": activation["supported_task_families"],
        "out_of_scope": activation["out_of_scope"],
        "unsupported_task_family": activation["unsupported_task_family"],
    }
    write_evidence_bundle(
        out_dir / "evidence_bundle",
        case_id=case.case_id,
        backend=args.backend,
        variant="installed_runtime",
        target_text=case.target_asset,
        skill=skill_package,
        skill_text=skill_text,
        execution=execution,
        verifier=verifier,
        status="completed",
        provenance=provenance,
    )
    summary = {
        "run_id": run_id,
        "skill_id": args.installed,
        "case_id": case.case_id,
        "backend": args.backend,
        "runtime_source": "installed_skill_package",
        "skill_package_path": str(skill_dir),
        "skill_version": skill_package.version,
        "manifest_hash": provenance["manifest_hash"],
        "skill_hash": provenance["skill_hash"],
        "task_family": case.task_family,
        "activated_capability_group": activation["activated_capability_group"],
        "out_of_scope": activation["out_of_scope"],
        "unsupported_task_family": activation["unsupported_task_family"],
        "output_dir": str(out_dir),
        "pass": verifier["pass"],
    }
    write_json(out_dir / "run_summary.json", summary)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
