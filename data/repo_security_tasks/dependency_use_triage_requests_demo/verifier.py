from __future__ import annotations

import json
import sys
from pathlib import Path

from expert_skill_system.evaluation.repo_security_verifier import verify_prediction_file


def main(argv: list[str] | None = None) -> int:
    args = argv or sys.argv[1:]
    if len(args) not in {2, 3}:
        print("usage: verifier.py TASK_JSON PREDICTION_JSON [OUTPUT_JSON]")
        return 2
    output = Path(args[2]) if len(args) == 3 else None
    result = verify_prediction_file(Path(args[0]), Path(args[1]), output)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["verifier_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
