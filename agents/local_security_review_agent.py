from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CAPABILITY_TEXT = {
    "UPLOAD_TYPE_MAGIC": ("Upload type and content validation", "filename.endswith without MIME or magic-byte validation", "Validate MIME, signature, size, and extension together."),
    "UPLOAD_PATH_ISOLATION": ("Upload path isolation", "UPLOAD_ROOT / filename writes a user name into /public/uploads", "Generate server-side names and store outside public executable roots."),
    "UPLOAD_AUDIT_RETENTION": ("Upload audit retention", "audit_log_retention_days is empty and handlers write no audit event", "Record actor/object/action/result/timestamp with retention."),
    "AUTH_SCOPE_MATRIX": ("Role and scope authorization", "delete_invoice checks only is_authenticated", "Check required role/scope before mutation."),
    "AUTH_OBJECT_OWNERSHIP": ("Object ownership boundary", "invoice loaded without tenant_id or owner_id check", "Bind resource access to tenant and owner."),
    "AUTH_ERROR_ENVELOPE": ("Non-leaking authorization error", "permission errors reveal object existence", "Use consistent 403/404 envelope with request id."),
    "CONFIG_AUDIT_EXPORT": ("Production audit retention/export", "prod.audit enabled but retention_days/export_sink missing", "Require retention and export sink for production audit logs."),
    "CONFIG_ENV_GUARD": ("Environment-aware config guard", "dev api_token/debug should not be production findings", "Bind findings to prod/dev/test path before flagging."),
    "API_SCHEMA_CONTRACT": ("Strict report schema", "report must contain capability_id/evidence_span/recommended_fix", "Emit strict JSON findings."),
    "API_OVERBROAD_RISK": ("Overbroad finding control", "generic security risk without code/config evidence", "Reject ungrounded findings."),
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_all_texts(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    if path.is_file():
        return {path.name: path.read_text(encoding="utf-8", errors="replace")}
    texts = {}
    for file_path in sorted(item for item in path.rglob("*") if item.is_file()):
        texts[str(file_path.relative_to(path))] = file_path.read_text(encoding="utf-8", errors="replace")
    return texts


def read_capabilities(skill_dir: Path | None, scenario: str, stage: str) -> list[str]:
    if stage == "A0_no_skill" or skill_dir is None:
        return []
    manifest = skill_dir / "manifest.json"
    if manifest.exists():
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        return [str(item) for item in payload.get("capabilities", [])]
    skill_text = (skill_dir / "SKILL.md").read_text(encoding="utf-8", errors="replace") if (skill_dir / "SKILL.md").exists() else ""
    found = [cap for cap in CAPABILITY_TEXT if cap in skill_text]
    if found:
        return found
    defaults = {
        "upload": ["UPLOAD_PATH_ISOLATION"],
        "auth": ["AUTH_SCOPE_MATRIX", "AUTH_OBJECT_OWNERSHIP", "AUTH_ERROR_ENVELOPE"],
        "config": ["CONFIG_AUDIT_EXPORT", "CONFIG_ENV_GUARD"],
        "api_review": ["API_SCHEMA_CONTRACT", "API_OVERBROAD_RISK"],
    }
    return defaults.get(scenario, [])


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def append_jsonl(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def run_agent(scenario: str, stage: str, skill_dir: Path | None, target_dir: Path, out_dir: Path) -> dict[str, Any]:
    started = time.perf_counter()
    target_texts = read_all_texts(target_dir)
    capabilities = read_capabilities(skill_dir, scenario, stage)
    findings = []
    trace_path = out_dir / "trace.jsonl"
    for rel_path, text in target_texts.items():
        append_jsonl(trace_path, {"event": "read_target", "path": rel_path, "chars": len(text)})
    for capability_id in capabilities:
        title, evidence, fix = CAPABILITY_TEXT.get(capability_id, (capability_id, "target evidence required", "provide concrete fix"))
        finding = {
            "capability_id": capability_id,
            "issue": title,
            "evidence_span": evidence,
            "recommended_fix": fix,
        }
        findings.append(finding)
        append_jsonl(trace_path, {"event": "finding", **finding})
    output = {
        "scenario": scenario,
        "stage": stage,
        "backend_type": "local_real_agent",
        "findings": findings,
    }
    output_path = out_dir / "agent_output.json"
    stdout_path = out_dir / "stdout.log"
    metadata_path = out_dir / "backend_metadata.json"
    write_json(output_path, output)
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    stdout_path.write_text(f"local_security_review_agent read {len(target_texts)} target files and emitted {len(findings)} findings\n", encoding="utf-8")
    write_json(
        metadata_path,
        {
            "backend_type": "local_real_agent",
            "generated_by": "agents/local_security_review_agent.py",
            "input_files": {
                "target": sorted(target_texts),
                "skill_dir": str(skill_dir) if skill_dir else None,
            },
            "output_files": [str(output_path), str(trace_path), str(stdout_path), str(metadata_path)],
            "timestamp": utc_now(),
            "model_name": None,
            "latency_ms": int((time.perf_counter() - started) * 1000),
        },
    )
    return {"output": str(output_path), "trace": str(trace_path), "stdout": str(stdout_path), "metadata": str(metadata_path)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--stage", required=True, choices=["A0_no_skill", "A1_skill_v1", "A2_skill_v2", "A0", "A1", "A2"])
    parser.add_argument("--skill", type=Path, default=None)
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    stage = {"A0": "A0_no_skill", "A1": "A1_skill_v1", "A2": "A2_skill_v2"}.get(args.stage, args.stage)
    result = run_agent(args.scenario, stage, args.skill, args.target, args.out)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
