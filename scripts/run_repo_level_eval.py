from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from expert_skill_system.evaluation.repo_eval_harness import run_repo_level_eval  # noqa: E402
from expert_skill_system.runtime.release_bundle_resolver import BundleResolutionError  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the reproducible repo-level evaluation harness.")
    parser.add_argument("--task-registry", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--state-dir", required=True)
    parser.add_argument("--bundle-digest")
    parser.add_argument("--use-active-binding", action="store_true")
    parser.add_argument("--task-id")
    parser.add_argument("--condition", default="C5_active_runtime")
    parser.add_argument("--allow-local-manifest-only", action="store_true")
    parser.add_argument("--fail-on-partial-bundle", action="store_true")
    args = parser.parse_args(argv)
    try:
        summary = run_repo_level_eval(
            task_registry=Path(args.task_registry),
            output_dir=Path(args.output),
            state_dir=Path(args.state_dir),
            bundle_digest=args.bundle_digest,
            use_active_binding=args.use_active_binding,
            task_id=args.task_id,
            condition=args.condition,
            allow_local_manifest_only=args.allow_local_manifest_only,
            fail_on_partial_bundle=args.fail_on_partial_bundle,
        )
    except BundleResolutionError as exc:
        payload = {
            "schema_version": "repo_level_eval_error.v1",
            "status": "failed_bundle_resolution",
            "error": str(exc),
        }
        output = Path(args.output)
        output.mkdir(parents=True, exist_ok=True)
        (output / "bundle_resolution.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        return 2
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if summary["fail_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
