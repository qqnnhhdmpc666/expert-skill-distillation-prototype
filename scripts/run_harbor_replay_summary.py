from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from skill_deployment import RunnerContext, get_backend_runner


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Read an existing Harbor repair-loop artifact through the shared replay runner adapter.")
    parser.add_argument("--backend", required=True, choices=["harbor_llm_repair_upload_replay", "harbor_llm_repair_config_replay"])
    parser.add_argument("--attempt", default="A1", choices=["A1", "A2"])
    args = parser.parse_args()

    runner = get_backend_runner(args.backend, project_root=ROOT)
    result = runner.run(
        RunnerContext(
            scenario_id=args.backend,
            backend=args.backend,
            target_dir=ROOT,
            output_dir=ROOT,
            attempt_id=args.attempt,
            skill_package=None,
            task_case=None,
            metadata={},
        )
    )
    payload = {
        "backend": args.backend,
        "attempt": args.attempt,
        "finding_count": len(result.report.findings),
        "output_path": str(result.output_path) if result.output_path else None,
        "artifact_paths": {key: str(value) for key, value in result.artifact_paths.items()},
        "verifier_report": read_json(result.artifact_paths["verifier_report"]) if "verifier_report" in result.artifact_paths else None,
        "reward": read_json(result.artifact_paths["reward"]) if "reward" in result.artifact_paths else None,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
