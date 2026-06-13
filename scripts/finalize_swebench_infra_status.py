from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RUN_ROOT = ROOT / "outputs" / "external_swebench" / "swebench_gold_patch_smoke_requests_20260612"
REPORT = ROOT / "reports" / "SWEBENCH_INFRA_FINAL_STATUS.md"
JSON_REPORT = ROOT / "reports" / "swebench_infra_final_status.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def normalize_status(summary: dict[str, Any]) -> tuple[str, str]:
    status = (summary.get("infra_unblock") or {}).get("final_status") or summary.get("official_harness_gold_patch_smoke")
    blocked_reason = (summary.get("gold_patch") or {}).get("blocked_reason") or (summary.get("infra_unblock") or {}).get("blocked_reason")
    if status == "pass" or status == "official_harness_gold_patch_smoke=pass":
        return "official_harness_gold_patch_smoke=pass", str(blocked_reason or "")
    if status == "evaluation_failed":
        return "evaluation_failed", str(blocked_reason or "")
    return "infra_blocked", str(blocked_reason or "official harness did not complete successfully")


def render_report(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# SWE-bench Infra Final Status",
            "",
            f"Generated at: `{payload['generated_at']}`",
            "",
            "## Status",
            "",
            f"- `external_harness`: `{payload['external_harness']}`",
            f"- `blocked_reason`: `{payload['blocked_reason']}`",
            f"- `source_summary`: `{payload['source_summary']}`",
            "",
            "## Boundary",
            "",
            "- No official evaluator logic was changed.",
            "- No gold patch or test patch was changed.",
            "- No custom evaluator replaced the official harness.",
            "- No `skill_llm_patch` was run without model configuration.",
            "- `infra_blocked` is not benchmark success and not a Skill/model failure.",
        ]
    ) + "\n"


def main() -> int:
    summary_path = RUN_ROOT / "summary.json"
    summary = read_json(summary_path, {})
    status, reason = normalize_status(summary)
    payload = {
        "generated_at": utc_now(),
        "external_harness": status,
        "blocked_reason": reason,
        "source_summary": str(summary_path),
        "allowed_status_values": ["official_harness_gold_patch_smoke=pass", "infra_blocked", "evaluation_failed"],
        "claim_boundary": "SWE-bench supports only software_patch_review harness readiness, not secure_code_review claims.",
    }
    write_json(JSON_REPORT, payload)
    write_text(REPORT, render_report(payload))
    print(json.dumps({"status": status, "report": str(REPORT)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
