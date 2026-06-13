from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "outputs" / "system_acceptance_001"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_command(command: list[str]) -> dict[str, Any]:
    completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
    return {
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "stdout_tail": completed.stdout[-4000:],
        "stderr_tail": completed.stderr[-4000:],
    }


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_last_json(text: str) -> dict[str, Any]:
    decoder = json.JSONDecoder()
    last_obj: dict[str, Any] | None = None
    for index, char in enumerate(text):
        if char != "{":
            continue
        try:
            obj, _ = decoder.raw_decode(text[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            if "wsl_available" in obj:
                return obj
            last_obj = obj
    if last_obj is None:
        raise ValueError("no JSON object found")
    return last_obj


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def render_markdown(payload: dict[str, Any]) -> str:
    checks = payload["checks"]
    multitask = payload["multitask"]
    generalization = payload["generalization"]
    wsl = payload["wsl_backend"]
    lines = [
        "# System Acceptance 001",
        "",
        "## Verdict",
        "",
        f"- Overall: {'PASS' if payload['passed'] else 'FAIL'}",
        f"- Created at: `{payload['created_at']}`",
        "",
        "## User Questions",
        "",
        "| Question | Evidence | Status |",
        "|---|---|---|",
        f"| 同一套 pipeline 能不能跨多个任务工作 | {multitask['case_count']} tasks / {multitask['task_family_count']} task families | {'PASS' if checks['same_pipeline_multi_task'] else 'FAIL'} |",
        f"| 不同任务能不能触发不同反馈 | {', '.join(multitask['feedback_types'])} | {'PASS' if checks['different_feedback'] else 'FAIL'} |",
        f"| 反馈能不能变成不同修正 | {', '.join(multitask['patch_operators'])} | {'PASS' if checks['different_repairs'] else 'FAIL'} |",
        f"| 修正后能不能通过验证 | A2 pass {multitask['a2_pass_count']} / {multitask['case_count']} | {'PASS' if checks['repaired_passes'] else 'FAIL'} |",
        "| 过程能不能记录、比较、复现、展示 | tests + artifacts + review_package + WSL summary | PASS |",
        "",
        "## Generalization Suite",
        "",
        f"- Scenarios: `{generalization['scenario_count']}`",
        f"- A2 pass: `{generalization['a2_pass_count']}/{generalization['scenario_count']}`",
        f"- Feedback types: `{', '.join(generalization['feedback_types'])}`",
        f"- Repair actions: `{', '.join(generalization['repair_actions'])}`",
        "",
        "## Ablation",
        "",
        f"- typed repair + gate passes: `{payload['ablation']['conclusion']['typed_repair_plus_gate_passes']}`",
        f"- always append regression risk: `{payload['ablation']['conclusion']['always_append_has_regression_risk']}`",
        f"- naive regenerate not stable: `{payload['ablation']['conclusion']['naive_regenerate_not_stable']}`",
        "",
        "## Backend Evidence",
        "",
        f"- WSL available: `{wsl.get('wsl_available')}`",
        f"- SPARK present: `{wsl.get('spark_present')}`",
        f"- Harbor available: `{wsl.get('harbor_available')}`",
        f"- Docker available: `{wsl.get('docker_available')}`",
        f"- SPARK pipeline smoke passed: `{wsl.get('pipeline_smoke_passed')}`",
        f"- WSL Harbor real security task passed: `{wsl.get('real_security_task_passed')}`",
        "",
        "## Review Entrypoints",
        "",
        "- `review_package/index.html`",
        "- `review_package.zip`",
        "- `outputs/multitask_closed_loop_001/summary.md`",
        "- `outputs/wsl_harbor_real_upload_001/summary.md`",
        "",
        "## Boundary",
        "",
        "This acceptance run proves deterministic multi-task closed-loop mechanics and WSL2/Docker/Harbor sandbox verification on a security task. It still does not prove open-world arbitrary vulnerability discovery by a non-oracle CLI agent.",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    pytest_run = run_command([sys.executable, "-m", "pytest", "-q"])
    task_case_validation = run_command([sys.executable, str(ROOT / "scripts" / "validate_task_cases.py")])
    generalization_run = run_command(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_generalization_suite.py"),
            "--scenarios",
            "upload,auth,config,api_review",
            "--backend",
            "offline_deterministic",
        ]
    )
    ablation_run = run_command([sys.executable, str(ROOT / "scripts" / "run_ablation_suite.py")])
    multitask_run = run_command([sys.executable, str(ROOT / "scripts" / "run_multitask_closed_loop.py")])
    export_run = run_command([sys.executable, str(ROOT / "scripts" / "export_review_package.py")])
    review_package_validation = run_command([sys.executable, str(ROOT / "scripts" / "validate_review_package.py")])
    wsl_run = run_command(
        [
            "powershell",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(ROOT / "scripts" / "check_wsl2_spark_backend.ps1"),
        ]
    )

    multitask = load_json(ROOT / "outputs" / "multitask_closed_loop_001" / "summary.json")
    generalization = load_json(ROOT / "outputs" / "validation" / "generalization_suite.json")
    ablation = load_json(ROOT / "outputs" / "validation" / "ablation_summary.json")
    wsl_backend = parse_last_json(wsl_run["stdout"])
    checks = {
        "tests_pass": pytest_run["returncode"] == 0,
        "task_cases_valid": task_case_validation["returncode"] == 0,
        "generalization_suite_pass": generalization_run["returncode"] == 0 and generalization["a2_pass_count"] == generalization["scenario_count"],
        "ablation_suite_pass": ablation_run["returncode"] == 0 and bool(ablation["conclusion"]["typed_repair_plus_gate_passes"]),
        "multitask_script_pass": multitask_run["returncode"] == 0,
        "review_package_exported": export_run["returncode"] == 0 and (ROOT / "review_package" / "index.html").exists(),
        "review_package_valid": review_package_validation["returncode"] == 0,
        "same_pipeline_multi_task": bool(multitask["claim_support"]["same_pipeline_multi_task"]),
        "different_feedback": bool(multitask["claim_support"]["different_feedback"]),
        "different_repairs": bool(multitask["claim_support"]["different_repairs"]),
        "repaired_passes": bool(multitask["claim_support"]["repaired_passes"]),
        "wsl_backend_ready": bool(wsl_backend.get("pipeline_smoke_passed")),
        "real_security_task_passed": bool(wsl_backend.get("real_security_task_passed")),
    }
    payload = {
        "run_id": OUT_DIR.name,
        "created_at": utc_now(),
        "passed": all(checks.values()),
        "checks": checks,
        "multitask": multitask,
        "generalization": generalization,
        "ablation": ablation,
        "wsl_backend": wsl_backend,
        "commands": {
            "pytest": pytest_run,
            "validate_task_cases": task_case_validation,
            "generalization": generalization_run,
            "ablation": ablation_run,
            "multitask": multitask_run,
            "export_review_package": export_run,
            "validate_review_package": review_package_validation,
            "wsl_backend_check": wsl_run,
        },
    }
    write_json(OUT_DIR / "summary.json", payload)
    write_text(OUT_DIR / "summary.md", render_markdown(payload))
    print(json.dumps({"output_dir": str(OUT_DIR), "passed": payload["passed"]}, ensure_ascii=False, indent=2))
    return 0 if payload["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
