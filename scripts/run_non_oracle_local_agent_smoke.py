from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_generalization_suite import select_scenarios, verify


OUT_DIR = ROOT / "outputs" / "non_oracle_local_agent_upload_001"


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_md(path: Path, payload: dict[str, object]) -> None:
    lines = [
        "# Non-Oracle Local Agent Upload Smoke",
        "",
        f"- Pass: `{payload['pass']}`",
        f"- Findings: `{payload['finding_count']}`",
        f"- Feedback: `{payload['verifier_report']['feedback_type']}`",
        "",
        "## Boundary",
        "",
        "This is a deterministic non-oracle local semantic smoke. It reads target text and skill manifest, extracts evidence spans with simple detectors, and is not an LLM or Harbor agent.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    scenario = select_scenarios("upload")[0]
    skill_dir = ROOT / "runs" / "generalization" / scenario.key / "skills" / "skill_v2"
    target_dir = ROOT / "runs" / "generalization" / scenario.key / "target_asset"
    if not skill_dir.exists() or not target_dir.exists():
        subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "run_generalization_suite.py"),
                "--scenarios",
                "upload",
                "--backend",
                "offline_deterministic",
            ],
            cwd=ROOT,
            check=True,
        )
    agent_out_dir = OUT_DIR / "agent"
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "agents" / "non_oracle_local_security_agent.py"),
            "--skill",
            str(skill_dir),
            "--target",
            str(target_dir),
            "--out",
            str(agent_out_dir),
        ],
        cwd=ROOT,
        check=True,
    )
    output = json.loads((agent_out_dir / "agent_output.json").read_text(encoding="utf-8"))
    report = verify(scenario, output)
    payload = {
        "run_id": "non_oracle_local_agent_upload_001",
        "backend": "non_oracle_local_semantic_agent",
        "oracle": False,
        "llm": False,
        "pass": report["pass"],
        "finding_count": len(output.get("findings", [])),
        "agent_output": str(agent_out_dir / "agent_output.json"),
        "trace": str(agent_out_dir / "trace.jsonl"),
        "stdout": str(agent_out_dir / "stdout.log"),
        "metadata": str(agent_out_dir / "backend_metadata.json"),
        "verifier_report": report,
        "boundary": "Deterministic non-oracle local semantic smoke; not Harbor and not LLM autonomy.",
    }
    write_json(OUT_DIR / "summary.json", payload)
    write_md(OUT_DIR / "summary.md", payload)
    print(json.dumps({"summary": str(OUT_DIR / "summary.json"), "pass": report["pass"]}, ensure_ascii=False, indent=2))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
