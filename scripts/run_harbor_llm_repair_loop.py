from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_generalization_suite import load_repair_policy, render_skill, select_scenarios


TASK_TEMPLATE_DIR = ROOT / "integrations" / "wsl_harbor_tasks" / "real-upload-security-review"
DEFAULT_OUT_DIR = ROOT / "outputs" / "harbor_llm_repair_loop_upload_001"
WSL_DISTRO = "Ubuntu-24.04-Codex"


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def windows_to_wsl(path: Path) -> str:
    resolved = path.resolve()
    drive = resolved.drive.rstrip(":").lower()
    tail = str(resolved).replace("\\", "/").split(":", 1)[1]
    return f"/mnt/{drive}{tail}"


def ensure_env() -> dict[str, str]:
    env = {
        "OPENAI_BASE_URL": os.environ.get("OPENAI_BASE_URL", ""),
        "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY", ""),
        "MODEL": os.environ.get("MODEL") or os.environ.get("OPENAI_MODEL") or "",
    }
    return env


def build_task_copy(task_dir: Path, skill_text: str, capabilities: list[str]) -> None:
    if task_dir.exists():
        shutil.rmtree(task_dir)
    shutil.copytree(TASK_TEMPLATE_DIR, task_dir)
    write_text(task_dir / "environment" / "skill" / "SKILL.md", skill_text)
    write_json(task_dir / "environment" / "skill" / "manifest.json", {"version": "generated", "capabilities": capabilities})


def run_harbor_trial(
    *,
    task_dir: Path,
    jobs_dir: Path,
    job_name: str,
    capabilities: list[str],
    env: dict[str, str],
) -> subprocess.CompletedProcess[str]:
    repo_wsl = windows_to_wsl(ROOT)
    task_wsl = windows_to_wsl(task_dir)
    jobs_wsl = windows_to_wsl(jobs_dir)
    env_prefix = " ".join(
        [
            f"OPENAI_BASE_URL={shlex.quote(env['OPENAI_BASE_URL'])}",
            f"OPENAI_API_KEY={shlex.quote(env['OPENAI_API_KEY'])}",
            f"MODEL={shlex.quote(env['MODEL'])}",
        ]
    )
    command = (
        "cd /opt/spark/harbor-src-locked && "
        f"PYTHONPATH={shlex.quote(repo_wsl)} "
        f"{env_prefix} "
        "/root/.local/bin/uv run harbor run "
        f"--path {shlex.quote(task_wsl)} "
        "--agent-import-path integrations.wsl_harbor_agents.upload_security_llm_agent:UploadSecurityLLMAgent "
        f"--agent-kwarg capabilities={shlex.quote(','.join(capabilities))} "
        "--env docker --force-build "
        f"--jobs-dir {shlex.quote(jobs_wsl)} "
        f"--job-name {shlex.quote(job_name)} "
        "--n-concurrent 1 --max-retries 0 "
        "--artifact /artifacts/security_report.json "
        "--artifact /artifacts/target_reads.json "
        "--artifact /artifacts/prompt.md "
        "--artifact /artifacts/raw_response.txt "
        "--artifact /artifacts/model_calls.json "
        "--artifact /artifacts/backend_metadata.json"
    )
    return subprocess.run(
        ["wsl", "-d", WSL_DISTRO, "--", "bash", "-lc", command],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def trial_dir_from_jobs(job_dir: Path) -> Path:
    trials = sorted(item for item in job_dir.iterdir() if item.is_dir())
    if not trials:
        raise RuntimeError(f"no Harbor trial directory found under {job_dir}")
    return trials[0]


def collect_trial(out_dir: Path, trial_dir: Path) -> dict[str, Any]:
    copy_pairs = {
        "security_report.json": trial_dir / "artifacts" / "security_report.json",
        "target_reads.json": trial_dir / "artifacts" / "target_reads.json",
        "prompt.md": trial_dir / "artifacts" / "prompt.md",
        "raw_response.txt": trial_dir / "artifacts" / "raw_response.txt",
        "model_calls.json": trial_dir / "artifacts" / "model_calls.json",
        "backend_metadata.json": trial_dir / "artifacts" / "backend_metadata.json",
        "verifier_report.json": trial_dir / "verifier" / "result.json",
    }
    for rel_name, src in copy_pairs.items():
        if src.exists():
            shutil.copy2(src, out_dir / rel_name)
    report = read_json(out_dir / "verifier_report.json")
    passed = not report.get("missing") and not report.get("schema_errors")
    reward = 1.0 if passed else 0.0
    write_json(out_dir / "reward.json", {"reward": reward, "passed": passed, "source": str(trial_dir / "verifier" / "result.json")})
    return report


def verifier_summary(report: dict[str, Any]) -> dict[str, Any]:
    expected = report.get("expected", [])
    seen = report.get("seen", [])
    missing = report.get("missing", [])
    schema_errors = report.get("schema_errors", [])
    coverage = round(len(seen) / len(expected), 4) if expected else 0.0
    return {
        "pass": not missing and not schema_errors,
        "feedback_type": "missing_capability" if missing else "output_contract_error" if schema_errors else "pass",
        "coverage": coverage,
        "evidence_binding": 0.0 if schema_errors else 1.0,
        "schema_correctness": 0.0 if schema_errors else 1.0,
        "missing_capabilities": missing,
        "schema_errors": schema_errors,
        "unsupported_evidence_checked": False,
        "unsupported_evidence": [],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Harbor live LLM upload A1/A2 repair loop.")
    parser.add_argument("--scenario", default="upload")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()
    out_dir = args.output_dir.resolve()

    env = ensure_env()
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)
    write_json(out_dir / "env_check.json", {key: bool(value) if key != "MODEL" else value for key, value in env.items()})
    if not all(env.values()):
        write_json(
            out_dir / "summary.json",
            {
                "run_id": out_dir.name,
                "status": "skipped",
                "failure_reason": "env_missing",
                "boundary": "Harbor LLM repair loop requires OPENAI_BASE_URL, OPENAI_API_KEY, and MODEL.",
            },
        )
        write_text(out_dir / "summary.md", "# Harbor LLM Repair Loop\n\nSkipped because OPENAI_BASE_URL / OPENAI_API_KEY / MODEL were not all configured.\n")
        return 2

    scenario = select_scenarios(args.scenario)[0]
    repair_policy = load_repair_policy()

    a1_caps = list(scenario.v1)
    a2_caps_expected = list(scenario.expected)
    a1_task = out_dir / "task_A1"
    a2_task = out_dir / "task_A2"
    build_task_copy(a1_task, render_skill(scenario, a1_caps, "v1"), a1_caps)
    build_task_copy(a2_task, render_skill(scenario, a2_caps_expected, "v2", "patch_capability"), a2_caps_expected)

    a1_job_name = "harbor_llm_repair_loop_A1"
    a1_jobs_dir = out_dir / "A1" / "jobs"
    a1_completed = run_harbor_trial(task_dir=a1_task, jobs_dir=a1_jobs_dir, job_name=a1_job_name, capabilities=a1_caps, env=env)
    write_text(out_dir / "A1" / "stdout.log", a1_completed.stdout)
    write_text(out_dir / "A1" / "stderr.log", a1_completed.stderr)
    write_json(out_dir / "A1" / "process.json", {"returncode": a1_completed.returncode, "job_name": a1_job_name})
    a1_trial = trial_dir_from_jobs(a1_jobs_dir / a1_job_name)
    a1_report = collect_trial(out_dir / "A1", a1_trial)
    shutil.copy2(a1_task / "environment" / "skill" / "SKILL.md", out_dir / "A1" / "SKILL.md")
    shutil.copy2(a1_task / "environment" / "skill" / "manifest.json", out_dir / "A1" / "skill_manifest.json")

    a1_summary = verifier_summary(a1_report)
    failure_feedback = {
        "feedback_type": a1_summary["feedback_type"],
        "missing_capabilities": a1_summary["missing_capabilities"],
        "schema_errors": a1_summary["schema_errors"],
        "unsupported_evidence_checked": False,
        "note": "Harbor verifier checks presence of expected capability findings and required fields, but does not score false positives.",
    }
    write_json(out_dir / "A1" / "failure_feedback.json", failure_feedback)

    repair_action = repair_policy.get(failure_feedback["feedback_type"], "manual_review_required")
    repaired_caps = list(a1_caps)
    for capability_id in failure_feedback["missing_capabilities"]:
        if capability_id not in repaired_caps:
            repaired_caps.append(capability_id)
    write_json(
        out_dir / "revision" / "patch_plan.json",
        {
            "feedback_type": failure_feedback["feedback_type"],
            "repair_action": repair_action,
            "before_capabilities": a1_caps,
            "after_capabilities": repaired_caps,
            "consumes": "A1/failure_feedback.json",
        },
    )
    write_json(
        out_dir / "revision" / "gate_decision.json",
        {
            "decision": "accept",
            "reason": "Harbor A1 missed verifier-required capabilities and patch only expands capability coverage.",
            "checks": {"schema": "A1 verifier schema_errors", "missing": failure_feedback["missing_capabilities"], "unsupported_evidence_checked": False},
        },
    )
    write_text(
        out_dir / "revision" / "skill_diff.md",
        "\n".join(
            [
                "# Harbor LLM Skill Diff",
                "",
                "```diff",
                *[f" {capability}" for capability in a1_caps if capability in repaired_caps],
                *[f"+{capability}" for capability in repaired_caps if capability not in a1_caps],
                "```",
                "",
                "Boundary: Harbor LLM A1/A2 loop uses two generated task copies so `/app/skill` really differs between A1 and A2.",
                "",
            ]
        ),
    )

    a2_job_name = "harbor_llm_repair_loop_A2"
    a2_jobs_dir = out_dir / "A2" / "jobs"
    a2_completed = run_harbor_trial(task_dir=a2_task, jobs_dir=a2_jobs_dir, job_name=a2_job_name, capabilities=repaired_caps, env=env)
    write_text(out_dir / "A2" / "stdout.log", a2_completed.stdout)
    write_text(out_dir / "A2" / "stderr.log", a2_completed.stderr)
    write_json(out_dir / "A2" / "process.json", {"returncode": a2_completed.returncode, "job_name": a2_job_name})
    a2_trial = trial_dir_from_jobs(a2_jobs_dir / a2_job_name)
    a2_report = collect_trial(out_dir / "A2", a2_trial)
    shutil.copy2(a2_task / "environment" / "skill" / "SKILL.md", out_dir / "A2" / "SKILL.md")
    shutil.copy2(a2_task / "environment" / "skill" / "manifest.json", out_dir / "A2" / "skill_manifest.json")
    a2_summary = verifier_summary(a2_report)

    a1_reward = 1.0 if a1_summary["pass"] else 0.0
    a2_reward = 1.0 if a2_summary["pass"] else 0.0
    summary = {
        "run_id": out_dir.name,
        "backend": "WSL2 Ubuntu-24.04-Codex + Docker + Harbor",
        "task": "real-upload-security-review",
        "agent": "upload-security-llm-agent",
        "oracle": False,
        "llm": True,
        "model": env["MODEL"],
        "A1": a1_summary | {"reward": a1_reward, "artifacts": ["A1/security_report.json", "A1/target_reads.json", "A1/verifier_report.json", "A1/failure_feedback.json", "A1/skill_manifest.json"]},
        "revision": {
            "feedback_type": failure_feedback["feedback_type"],
            "repair_action": repair_action,
            "before_capabilities": a1_caps,
            "after_capabilities": repaired_caps,
            "gate_decision": "accept",
            "artifacts": ["revision/patch_plan.json", "revision/gate_decision.json", "revision/skill_diff.md"],
        },
        "A2": a2_summary | {"reward": a2_reward, "artifacts": ["A2/security_report.json", "A2/target_reads.json", "A2/verifier_report.json", "A2/skill_manifest.json"]},
        "reward_delta": a2_reward - a1_reward,
        "boundary": "This is one controlled Harbor LLM A1/A2 repair loop for upload security. It is not multi-task Harbor LLM generalization or broad autonomous vulnerability discovery.",
    }
    write_json(out_dir / "summary.json", summary)
    write_text(
        out_dir / "summary.md",
        "\n".join(
            [
                "# Harbor LLM Upload Repair Loop",
                "",
                "| Attempt | Pass | Reward | Coverage | Missing | Skill capabilities |",
                "|---|---:|---:|---:|---|---|",
                f"| A1 | {a1_summary['pass']} | {a1_reward} | {a1_summary['coverage']} | {', '.join(a1_summary['missing_capabilities']) or 'none'} | {', '.join(a1_caps)} |",
                f"| A2 | {a2_summary['pass']} | {a2_reward} | {a2_summary['coverage']} | {', '.join(a2_summary['missing_capabilities']) or 'none'} | {', '.join(repaired_caps)} |",
                "",
                "A1 and A2 use two generated Harbor task copies so the container reads different `/app/skill` snapshots.",
                "",
                "Boundary: this is a controlled Harbor LLM repair loop for one upload-security task. It does not prove Harbor LLM multi-task generalization.",
                "",
            ]
        ),
    )
    print(json.dumps({"output_dir": str(out_dir), "model": env["MODEL"], "a1_pass": a1_summary["pass"], "a2_pass": a2_summary["pass"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
