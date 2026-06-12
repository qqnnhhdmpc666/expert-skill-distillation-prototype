from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = ROOT / "outputs" / "release" / "clean_clone_smoke"
REPORT = ROOT / "reports" / "CLEAN_CLONE_SMOKE_STATUS.md"


EXCLUDE_DIRS = {
    ".git",
    ".venv",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "outputs",
    "swebench-venv",
    "external_repos",
    ".codex-downloads",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def ignore_names(_dir: str, names: list[str]) -> set[str]:
    ignored = {name for name in names if name in EXCLUDE_DIRS}
    ignored.update(name for name in names if name.endswith(".pyc"))
    return ignored


def run_command(command: list[str], *, cwd: Path, log_dir: Path, name: str) -> dict[str, Any]:
    completed = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
    write_text(log_dir / f"{name}.stdout.log", completed.stdout)
    write_text(log_dir / f"{name}.stderr.log", completed.stderr)
    return {
        "name": name,
        "command": command,
        "cwd": str(cwd),
        "return_code": completed.returncode,
        "stdout_log": str(log_dir / f"{name}.stdout.log"),
        "stderr_log": str(log_dir / f"{name}.stderr.log"),
        "status": "pass" if completed.returncode == 0 else "fail",
    }


def venv_python(venv_dir: Path) -> Path:
    if (venv_dir / "Scripts" / "python.exe").exists():
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def venv_skill_deploy(venv_dir: Path) -> Path:
    if (venv_dir / "Scripts" / "skill-deploy.exe").exists():
        return venv_dir / "Scripts" / "skill-deploy.exe"
    return venv_dir / "bin" / "skill-deploy"


def render_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Clean Clone Smoke Status",
        "",
        f"Generated at: `{payload['generated_at']}`",
        "",
        f"- Source: `{payload['source']}`",
        f"- Worktree: `{payload['worktree']}`",
        f"- Virtualenv: `{payload['venv']}`",
        f"- Overall status: `{payload['overall_status']}`",
        "",
        "## Commands",
        "",
        "| Step | Status | Return code | Command |",
        "|---|---|---:|---|",
    ]
    for item in payload["commands"]:
        lines.append(f"| {item['name']} | `{item['status']}` | {item['return_code']} | `{' '.join(item['command'])}` |")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This is a local clean-environment packaging smoke. It is not an external benchmark and does not validate real-world security effectiveness.",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a strict local clean-clone smoke for release readiness.")
    parser.add_argument("--source", default=str(ROOT))
    parser.add_argument("--output-dir", default=str(OUTPUT_ROOT))
    parser.add_argument("--keep-artifacts", action="store_true")
    args = parser.parse_args(argv)

    source = Path(args.source).resolve()
    output_root = Path(args.output_dir).resolve()
    temp_root = Path(tempfile.gettempdir()) / "p0m_clean_clone_smoke"
    worktree = temp_root / "worktree"
    venv_dir = temp_root / "venv"
    logs = output_root / "logs"
    if output_root.exists():
        shutil.rmtree(output_root)
    if temp_root.exists():
        shutil.rmtree(temp_root)
    output_root.mkdir(parents=True, exist_ok=True)

    commands: list[dict[str, Any]] = []
    try:
        shutil.copytree(source, worktree, ignore=ignore_names)
    except Exception as exc:  # noqa: BLE001 - release smoke failures must be reported, not crash-only.
        payload = {
            "generated_at": utc_now(),
            "source": str(source),
            "worktree": str(worktree),
            "venv": str(venv_dir),
            "overall_status": "fail",
            "failure_stage": "copy_source",
            "failure_reason": str(exc),
            "commands": commands,
            "keep_artifacts": bool(args.keep_artifacts),
        }
        write_json(output_root / "summary.json", payload)
        write_text(REPORT, render_report(payload))
        print(json.dumps({"summary": str(output_root / "summary.json"), "report": str(REPORT), "overall_status": "fail", "failure_stage": "copy_source"}, indent=2))
        return 1
    commands.append(run_command([sys.executable, "-m", "venv", str(venv_dir)], cwd=worktree, log_dir=logs, name="create_venv"))
    if commands[-1]["return_code"] == 0:
        py = venv_python(venv_dir)
        commands.append(run_command([str(py), "-m", "pip", "install", "--upgrade", "pip"], cwd=worktree, log_dir=logs, name="upgrade_pip"))
        commands.append(run_command([str(py), "-m", "pip", "install", "-e", ".[dev]"], cwd=worktree, log_dir=logs, name="editable_install"))
    if commands and commands[-1]["return_code"] == 0:
        skill = venv_skill_deploy(venv_dir)
        commands.append(run_command([str(skill), "build-codex-skill"], cwd=worktree, log_dir=logs, name="build_codex_skill"))
        commands.append(
            run_command(
                [str(skill), "install", "--skill", "outputs/deployable_codex_skill/secure_code_review", "--version", "v2"],
                cwd=worktree,
                log_dir=logs,
                name="install_skill",
            )
        )
        commands.append(
            run_command(
                [str(skill), "run-skill", "--installed", "secure_code_review", "--case", "upload_security_001", "--backend", "offline_deterministic"],
                cwd=worktree,
                log_dir=logs,
                name="run_installed_skill",
            )
        )
        commands.append(run_command([str(skill), "validate-review-package"], cwd=worktree, log_dir=logs, name="validate_review_package"))
    overall = "pass" if commands and all(item["return_code"] == 0 for item in commands) else "fail"
    payload = {
        "generated_at": utc_now(),
        "source": str(source),
        "worktree": str(worktree),
        "venv": str(venv_dir),
        "overall_status": overall,
        "commands": commands,
        "keep_artifacts": bool(args.keep_artifacts),
    }
    write_json(output_root / "summary.json", payload)
    write_text(REPORT, render_report(payload))
    print(json.dumps({"summary": str(output_root / "summary.json"), "report": str(REPORT), "overall_status": overall}, indent=2))
    if not args.keep_artifacts and overall == "pass":
        shutil.rmtree(output_root, ignore_errors=True)
    return 0 if overall == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
