from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
CASES_ROOT = ROOT / "data" / "task_cases"
SRC_ROOT = ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from skill_deployment import validate_controlled_task_case_dir


def main() -> int:
    if not CASES_ROOT.exists():
        payload = {"status": "failed", "case_count": 0, "results": [], "message": "data/task_cases does not exist"}
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 1
    results = []
    for case_dir in sorted(CASES_ROOT.iterdir()):
        if not case_dir.is_dir():
            continue
        row = validate_controlled_task_case_dir(case_dir)
        row["case_dir"] = str(case_dir.relative_to(ROOT))
        results.append(row)
    ok = bool(results) and all(row["status"] == "ok" for row in results)
    payload = {"status": "ok" if ok else "failed", "case_count": len(results), "results": results}
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
