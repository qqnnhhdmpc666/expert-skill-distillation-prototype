from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from skill_deployment.schemas import TaskCase  # noqa: E402


CASES_ROOT = ROOT / "data/api_review_holdout_cases"


def main() -> int:
    results = []
    ok = True
    for case_dir in sorted(path for path in CASES_ROOT.iterdir() if path.is_dir()):
        try:
            case = TaskCase.from_directory(case_dir)
            results.append(
                {
                    "case_dir": str(case_dir.relative_to(ROOT)),
                    "case_id": case.case_id,
                    "status": "ok",
                    "expected_rule_ids": list(case.expected_rule_ids),
                    "negative_rule_ids": list(case.negative_rule_ids),
                    "false_positive_controls": list(case.false_positive_controls),
                    "metadata": case.metadata,
                }
            )
        except Exception as exc:  # noqa: BLE001 - CLI should report all case failures.
            ok = False
            results.append({"case_dir": str(case_dir.relative_to(ROOT)), "status": "error", "message": str(exc)})
    payload = {"status": "ok" if ok else "failed", "case_count": len(results), "results": results}
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

