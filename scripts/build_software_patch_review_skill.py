from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from skill_deployment.evidence import write_json, write_text  # noqa: E402
from skill_deployment.schemas import SkillPackage  # noqa: E402


OUTPUT_ROOT = ROOT / "outputs" / "deployable_codex_skill" / "software_patch_review"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def root_skill_markdown() -> str:
    return """# Software Patch Review Skill Package

Installable prototype package for bounded software patch review and SWE-bench smoke adapters.

## Boundary

- Allowed: issue understanding, minimal patch proposal, regression-test validation planning.
- Forbidden: security exploit generation, unrelated repository rewrites, hidden benchmark result claims.

## Runtime Versions

- `v1`: minimal patch-review capability group for local smoke and external adapter provenance.
"""


def version_skill_markdown() -> str:
    return """# Software Patch Review Installed Runtime v1

This installed runtime is bounded to software patch review and external SWE-bench smoke plumbing.

## Capability Groups

### software_patch_review
- task_families: `software_patch_review`
- capabilities:
  - `PATCH_TEST_FAILURE_REPRO`
  - `PATCH_MINIMAL_CODE_CHANGE`
  - `PATCH_REGRESSION_VALIDATION`

### out_of_scope_guard
- task_families: `none`
- capabilities:
  - none

## Output Contract

- `capability_id`
- `evidence_span`
- `recommended_fix`
"""


def runtime_manifest() -> dict[str, Any]:
    package = SkillPackage(
        skill_id="software_patch_review",
        version="v1",
        task_family="software_patch_review",
        capabilities=("PATCH_TEST_FAILURE_REPRO", "PATCH_MINIMAL_CODE_CHANGE", "PATCH_REGRESSION_VALIDATION"),
        output_contract=("capability_id", "evidence_span", "recommended_fix"),
        trace_contract=("trajectory.jsonl", "target_reads.json", "skill_reads.json"),
        metadata={
            "runtime_case_id": "software_patch_review_001",
            "package_role": "installed_runtime",
            "package_family_scope": "software_patch_review_and_swebench_smoke",
            "supported_task_families": ["software_patch_review"],
            "out_of_scope_group": "out_of_scope_guard",
            "external_adapters": ["swebench_lite_smoke"],
            "capability_groups": [
                {
                    "name": "software_patch_review",
                    "task_families": ["software_patch_review"],
                    "capabilities": ["PATCH_TEST_FAILURE_REPRO", "PATCH_MINIMAL_CODE_CHANGE", "PATCH_REGRESSION_VALIDATION"],
                },
                {
                    "name": "out_of_scope_guard",
                    "task_families": [],
                    "capabilities": [],
                },
            ],
        },
    )
    return package.to_dict()


def root_manifest() -> dict[str, Any]:
    return {
        "skill_id": "software_patch_review",
        "package_type": "codex_skill_runtime_bundle",
        "created_at": utc_now(),
        "name": "Software Patch Review Skill Package",
        "deployment_shape": "codex_skill_plus_cli",
        "available_versions": ["v1"],
        "default_version": "v1",
        "runtime_case_scope": ["software_patch_review_001"],
        "external_smoke_scope": ["SWE-bench/SWE-bench_Lite"],
        "entrypoints": {
            "install_v1": "skill-deploy install --skill outputs/deployable_codex_skill/software_patch_review --version v1",
            "run_installed": "skill-deploy run-skill --installed software_patch_review --case software_patch_review_001 --backend offline_deterministic",
        },
        "claim_boundary": "Patch-review package used for local controlled smoke and external adapter provenance, not a SWE-bench effectiveness claim by itself.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the deployable Software Patch Review Skill package.")
    parser.add_argument("--output-dir", default=str(OUTPUT_ROOT))
    args = parser.parse_args(argv)
    out_dir = Path(args.output_dir)
    write_text(out_dir / "SKILL.md", root_skill_markdown())
    write_json(out_dir / "manifest.json", root_manifest())
    write_text(out_dir / "versions" / "v1" / "SKILL.md", version_skill_markdown())
    write_json(out_dir / "versions" / "v1" / "manifest.json", runtime_manifest())
    write_json(
        out_dir / "examples" / "patch_review_positive.json",
        {
            "case_id": "software_patch_review_001",
            "findings": [
                {
                    "capability_id": "PATCH_MINIMAL_CODE_CHANGE",
                    "evidence_span": "target.md: replace int(amount * rate) with round(amount * rate, 2)",
                    "recommended_fix": "Apply the minimal expression replacement and rerun the targeted test.",
                }
            ],
        },
    )
    write_json(
        out_dir / "eval" / "smoke_cases.json",
        {
            "cases": [
                {
                    "case_id": "software_patch_review_001",
                    "command": "skill-deploy run-skill --installed software_patch_review --case software_patch_review_001 --backend offline_deterministic",
                }
            ]
        },
    )
    print(json.dumps({"output": str(out_dir), "manifest": str(out_dir / "manifest.json"), "versions": ["v1"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
