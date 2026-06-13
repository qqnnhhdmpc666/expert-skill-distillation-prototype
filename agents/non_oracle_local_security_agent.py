from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from skill_deployment import CAPABILITY_SPECS


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def append_jsonl(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def read_all_texts(path: Path) -> dict[str, str]:
    if path.is_file():
        return {path.name: path.read_text(encoding="utf-8", errors="replace")}
    return {
        str(file_path.relative_to(path)): file_path.read_text(encoding="utf-8", errors="replace")
        for file_path in sorted(item for item in path.rglob("*") if item.is_file())
    }


def read_capabilities(skill_dir: Path) -> list[str]:
    manifest = skill_dir / "manifest.json"
    if manifest.exists():
        payload = read_json(manifest)
        return [str(item) for item in payload.get("capabilities", [])]
    skill_text = (skill_dir / "SKILL.md").read_text(encoding="utf-8", errors="replace") if (skill_dir / "SKILL.md").exists() else ""
    return [capability_id for capability_id in CAPABILITY_SPECS if capability_id in skill_text]


def parse_active_capabilities(raw_value: str | None, available: list[str]) -> list[str]:
    if raw_value is None:
        return available
    requested = [item.strip() for item in raw_value.split(",") if item.strip()]
    requested_set = set(requested)
    return [capability_id for capability_id in available if capability_id in requested_set]


def find_span(target_texts: dict[str, str], needles: list[str]) -> str:
    for rel_path, text in target_texts.items():
        lower_text = text.lower()
        for needle in needles:
            idx = lower_text.find(needle.lower())
            if idx >= 0:
                line_start = text.rfind("\n", 0, idx) + 1
                line_end = text.find("\n", idx)
                if line_end < 0:
                    line_end = len(text)
                snippet = " ".join(text[line_start:line_end].split())
                return snippet
    return ""


def run_agent(skill_dir: Path, target_dir: Path, out_dir: Path, active_capabilities: str | None = None) -> dict[str, Any]:
    start = time.perf_counter()
    trace_path = out_dir / "trace.jsonl"
    target_texts = read_all_texts(target_dir)
    available_capabilities = read_capabilities(skill_dir)
    capabilities = parse_active_capabilities(active_capabilities, available_capabilities)
    findings: list[dict[str, Any]] = []
    for rel_path, text in target_texts.items():
        append_jsonl(trace_path, {"event": "read_target", "path": rel_path, "chars": len(text)})
    append_jsonl(
        trace_path,
        {
            "event": "read_skill",
            "skill_dir": str(skill_dir),
            "available_capabilities": available_capabilities,
            "active_capabilities": capabilities,
        },
    )
    for capability_id in capabilities:
        detector = CAPABILITY_SPECS.get(capability_id)
        if not detector:
            append_jsonl(trace_path, {"event": "skip_unsupported_capability", "capability_id": capability_id})
            continue
        evidence = find_span(target_texts, list(detector.detector_needles))
        if not evidence:
            append_jsonl(trace_path, {"event": "no_evidence", "capability_id": capability_id})
            continue
        finding = {
            "capability_id": capability_id,
            "issue": detector.title,
            "evidence_span": evidence,
            "recommended_fix": detector.fix_hint,
        }
        findings.append(finding)
        append_jsonl(trace_path, {"event": "finding", **finding})
    output = {
        "backend_type": "non_oracle_local_semantic_agent",
        "findings": findings,
        "notes": [
            "task_conditioned_active_capabilities_applied",
            f"active_capabilities:{','.join(capabilities) if capabilities else 'none'}",
        ],
    }
    write_json(out_dir / "agent_output.json", output)
    (out_dir / "stdout.log").write_text(
        f"non_oracle_local_security_agent read {len(target_texts)} target files and emitted {len(findings)} findings\n",
        encoding="utf-8",
    )
    write_json(
        out_dir / "backend_metadata.json",
        {
            "backend_type": "non_oracle_local_semantic_agent",
            "oracle": False,
            "llm": False,
            "generated_by": "agents/non_oracle_local_security_agent.py",
            "skill_dir": str(skill_dir),
            "target_dir": str(target_dir),
            "available_capabilities": available_capabilities,
            "active_capabilities": capabilities,
            "timestamp": utc_now(),
            "latency_ms": int((time.perf_counter() - start) * 1000),
        },
    )
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skill", type=Path, required=True)
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--active-capabilities", default=None)
    args = parser.parse_args()
    result = run_agent(args.skill, args.target, args.out, args.active_capabilities)
    print(json.dumps({"out": str(args.out), "findings": len(result["findings"])}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
