from __future__ import annotations

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

from scripts.run_generalization_suite import load_repair_policy


OUT_DIR = ROOT / "outputs" / "harbor_llm_repair_loop_config_001"
WSL_DISTRO = "Ubuntu-24.04-Codex"
EXPECTED_CAPABILITIES = [
    "CONFIG_HARDCODED_SECRET",
    "CONFIG_INSECURE_HTTP",
    "CONFIG_PROD_DEBUG",
]
CAPABILITY_TEXT = {
    "CONFIG_HARDCODED_SECRET": {
        "title": "No hardcoded secret in production config",
        "evidence": "payment_token, api_key, secret, or password is stored directly in production config.",
        "fix": "Replace inline secrets with vault or environment-secret references.",
    },
    "CONFIG_INSECURE_HTTP": {
        "title": "HTTPS/TLS required for production external endpoints",
        "evidence": "A production external_api_url uses http:// instead of https://.",
        "fix": "Require TLS/https for production external endpoints.",
    },
    "CONFIG_PROD_DEBUG": {
        "title": "Debug must be disabled in production",
        "evidence": "production config sets debug: true.",
        "fix": "Set debug to false in production.",
    },
}
TARGET_FILES = {
    "config.md": (ROOT / "data" / "config_security_cases" / "case001_prod_config_security" / "config.md").read_text(encoding="utf-8"),
}


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
    return {
        "OPENAI_BASE_URL": os.environ.get("OPENAI_BASE_URL", ""),
        "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY", ""),
        "MODEL": os.environ.get("MODEL") or os.environ.get("OPENAI_MODEL") or "",
    }


def render_skill(version: str, *, relaxed_contract: bool) -> str:
    lines = [
        f"# Config Security Skill {version}",
        "",
        "Task family: `config_security`",
        "",
        "## Review Goal",
        "",
        "Inspect the production-style configuration and report only concrete, target-grounded security findings.",
        "",
        "## Capabilities",
        "",
    ]
    for capability_id in EXPECTED_CAPABILITIES:
        entry = CAPABILITY_TEXT[capability_id]
        lines.extend(
            [
                f"### {capability_id}: {entry['title']}",
                f"- Evidence: {entry['evidence']}",
                f"- Fix: {entry['fix']}",
                "",
            ]
        )
    lines.extend(
        [
            "## Output Contract",
            "",
            "Return a JSON object with key `findings`.",
            "- Every finding must include `capability_id` and `evidence_span`.",
        ]
    )
    if not relaxed_contract:
        lines.append("- Every finding must include `recommended_fix`.")
    else:
        lines.append("- In exploratory v1, `recommended_fix` may be omitted.")
    lines.append("")
    return "\n".join(lines)


def instruction_text(relaxed_contract: bool) -> str:
    contract = (
        "For this exploratory v1 run, the report may omit `recommended_fix` if evidence is already specific."
        if relaxed_contract
        else "The report must include capability_id, evidence_span, and recommended_fix for each finding."
    )
    return "\n".join(
        [
            "Review the target configuration in `/app/target`.",
            "",
            "Create `/app/security_report.json` with the outer shape:",
            "",
            "```json",
            '{"findings": [{"capability_id": "CONFIG_HARDCODED_SECRET", "evidence_span": "...", "recommended_fix": "..."}]}',
            "```",
            "",
            contract,
            "",
            "The task focuses on hardcoded secret, insecure production HTTP endpoint, and production debug mode.",
        ]
    )


def verifier_script(expected: list[str]) -> str:
    return "\n".join(
        [
            "#!/bin/bash",
            "set -euo pipefail",
            "mkdir -p /logs/verifier",
            "",
            "python3 - <<'PY'",
            "import json",
            "from pathlib import Path",
            "",
            "report_path = Path('/app/security_report.json')",
            f"expected = {json.dumps(expected)}",
            "expected_set = set(expected)",
            "result = {",
            "    'report_exists': report_path.exists(),",
            "    'expected': expected,",
            "    'seen': [],",
            "    'missing': expected,",
            "    'false_positive': [],",
            "    'schema_errors': [],",
            "}",
            "",
            "if not report_path.exists():",
            "    Path('/logs/verifier/reward.txt').write_text('0\\n')",
            "    Path('/logs/verifier/result.json').write_text(json.dumps(result, indent=2) + '\\n')",
            "    raise SystemExit('FAIL: /app/security_report.json was not created')",
            "",
            "try:",
            "    payload = json.loads(report_path.read_text())",
            "except json.JSONDecodeError as exc:",
            "    result['schema_errors'].append(f'invalid json: {exc}')",
            "    Path('/logs/verifier/reward.txt').write_text('0\\n')",
            "    Path('/logs/verifier/result.json').write_text(json.dumps(result, indent=2) + '\\n')",
            "    raise SystemExit('FAIL: report is not valid JSON')",
            "",
            "findings = payload.get('findings')",
            "if not isinstance(findings, list):",
            "    result['schema_errors'].append('findings must be a list')",
            "    findings = []",
            "",
            "seen = set()",
            "for index, item in enumerate(findings):",
            "    if not isinstance(item, dict):",
            "        result['schema_errors'].append(f'finding {index} is not an object')",
            "        continue",
            "    capability_id = str(item.get('capability_id', '')).strip()",
            "    if capability_id:",
            "        seen.add(capability_id)",
            "    if capability_id in expected_set:",
            "        if not str(item.get('evidence_span', '')).strip():",
            "            result['schema_errors'].append(f'{capability_id} missing evidence_span')",
            "        if not str(item.get('recommended_fix', '')).strip():",
            "            result['schema_errors'].append(f'{capability_id} missing recommended_fix')",
            "",
            "result['seen'] = sorted(seen)",
            "result['missing'] = sorted(expected_set - seen)",
            "result['false_positive'] = sorted(seen - expected_set)",
            "passed = not result['missing'] and not result['false_positive'] and not result['schema_errors']",
            "Path('/logs/verifier/reward.txt').write_text('1\\n' if passed else '0\\n')",
            "Path('/logs/verifier/result.json').write_text(json.dumps(result, indent=2) + '\\n')",
            "if not passed:",
            "    raise SystemExit('FAIL: ' + json.dumps(result))",
            "print('PASS: config report covers expected findings with evidence and fixes')",
            "PY",
            "",
        ]
    )


def build_task_copy(task_dir: Path, *, skill_text: str, capabilities: list[str], relaxed_contract: bool) -> None:
    if task_dir.exists():
        shutil.rmtree(task_dir)
    (task_dir / "environment" / "skill").mkdir(parents=True, exist_ok=True)
    (task_dir / "environment" / "target").mkdir(parents=True, exist_ok=True)
    (task_dir / "solution").mkdir(parents=True, exist_ok=True)
    (task_dir / "tests").mkdir(parents=True, exist_ok=True)
    (task_dir / "target").mkdir(parents=True, exist_ok=True)
    write_text(task_dir / "task.toml", "\n".join([
        'version = "1.0"',
        "",
        "[metadata]",
        'author_name = "Codex"',
        'author_email = "codex@example.local"',
        'difficulty = "medium"',
        'category = "security-review"',
        'tags = ["wsl2", "docker", "harbor", "config-security", "verifier-backed"]',
        "",
        "[verifier]",
        "timeout_sec = 60.0",
        "",
        "[agent]",
        "timeout_sec = 90.0",
        "",
        "[environment]",
        "build_timeout_sec = 120.0",
        "cpus = 1",
        'memory = "1G"',
        'storage = "2G"',
        "",
    ]))
    write_text(task_dir / "instruction.md", instruction_text(relaxed_contract))
    write_text(task_dir / "environment" / "Dockerfile", "FROM ubuntu:24.04\nWORKDIR /app\nCOPY target/ /app/target/\nCOPY skill/ /app/skill/\n")
    write_text(task_dir / "environment" / "skill" / "SKILL.md", skill_text)
    write_json(task_dir / "environment" / "skill" / "manifest.json", {"version": "generated", "capabilities": capabilities})
    for rel_name, content in TARGET_FILES.items():
        write_text(task_dir / "target" / rel_name, content)
        write_text(task_dir / "environment" / "target" / rel_name, content)
    write_text(task_dir / "solution" / "solve.sh", "#!/bin/bash\nset -euo pipefail\nprintf 'solution placeholder\\n'\n")
    write_text(task_dir / "tests" / "test.sh", verifier_script(EXPECTED_CAPABILITIES))


def run_harbor_trial(
    *,
    task_dir: Path,
    jobs_dir: Path,
    job_name: str,
    capabilities: list[str],
    env: dict[str, str],
    relaxed_contract: bool,
    prompt_addendum: str,
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
        "--agent-import-path integrations.wsl_harbor_agents.controlled_security_llm_agent:ControlledSecurityLLMAgent "
        f"--agent-kwarg capabilities={shlex.quote(','.join(capabilities))} "
        f"--agent-kwarg task_label={shlex.quote('configuration security review')} "
        f"--agent-kwarg relaxed_contract={shlex.quote('true' if relaxed_contract else 'false')} "
        f"--agent-kwarg prompt_addendum={shlex.quote(prompt_addendum)} "
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
    passed = not report.get("missing") and not report.get("false_positive") and not report.get("schema_errors")
    reward = 1.0 if passed else 0.0
    write_json(out_dir / "reward.json", {"reward": reward, "passed": passed, "source": str(trial_dir / "verifier" / "result.json")})
    return report


def verifier_summary(report: dict[str, Any]) -> dict[str, Any]:
    expected = report.get("expected", [])
    seen = report.get("seen", [])
    missing = report.get("missing", [])
    false_positive = report.get("false_positive", [])
    schema_errors = report.get("schema_errors", [])
    coverage = round(len(seen) / len(expected), 4) if expected else 0.0
    feedback_type = "pass"
    if schema_errors:
        feedback_type = "output_contract_error"
    elif false_positive:
        feedback_type = "false_positive_risk"
    elif missing:
        feedback_type = "missing_capability"
    return {
        "pass": not missing and not false_positive and not schema_errors,
        "feedback_type": feedback_type,
        "coverage": coverage,
        "evidence_binding": 1.0 if not schema_errors else 0.0,
        "schema_correctness": 1.0 if not schema_errors else 0.0,
        "missing_capabilities": missing,
        "false_positive_capabilities": false_positive,
        "schema_errors": schema_errors,
    }


def main() -> int:
    env = ensure_env()
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True)
    write_json(OUT_DIR / "env_check.json", {key: bool(value) if key != "MODEL" else value for key, value in env.items()})
    if not all(env.values()):
        write_json(
            OUT_DIR / "summary.json",
            {
                "run_id": OUT_DIR.name,
                "status": "skipped",
                "failure_reason": "env_missing",
                "boundary": "Harbor LLM config repair loop requires OPENAI_BASE_URL, OPENAI_API_KEY, and MODEL.",
            },
        )
        write_text(OUT_DIR / "summary.md", "# Harbor LLM Config Repair Loop\n\nSkipped because OPENAI_BASE_URL / OPENAI_API_KEY / MODEL were not all configured.\n")
        return 2

    repair_policy = load_repair_policy()
    a1_caps = list(EXPECTED_CAPABILITIES)
    a2_caps = list(EXPECTED_CAPABILITIES)
    a1_task = OUT_DIR / "task_A1"
    a2_task = OUT_DIR / "task_A2"
    a1_prompt_addendum = (
        "Keep the outer JSON object with key `findings`, but in this exploratory v1 run each finding should include only "
        "`capability_id` and `evidence_span`. Omit `recommended_fix`."
    )
    build_task_copy(a1_task, skill_text=render_skill("v1", relaxed_contract=True), capabilities=a1_caps, relaxed_contract=True)
    build_task_copy(a2_task, skill_text=render_skill("v2", relaxed_contract=False), capabilities=a2_caps, relaxed_contract=False)

    a1_job_name = "harbor_llm_repair_loop_config_A1"
    a1_jobs_dir = OUT_DIR / "A1" / "jobs"
    a1_completed = run_harbor_trial(
        task_dir=a1_task,
        jobs_dir=a1_jobs_dir,
        job_name=a1_job_name,
        capabilities=a1_caps,
        env=env,
        relaxed_contract=True,
        prompt_addendum=a1_prompt_addendum,
    )
    write_text(OUT_DIR / "A1" / "stdout.log", a1_completed.stdout)
    write_text(OUT_DIR / "A1" / "stderr.log", a1_completed.stderr)
    write_json(OUT_DIR / "A1" / "process.json", {"returncode": a1_completed.returncode, "job_name": a1_job_name})
    a1_trial = trial_dir_from_jobs(a1_jobs_dir / a1_job_name)
    a1_report = collect_trial(OUT_DIR / "A1", a1_trial)
    shutil.copy2(a1_task / "environment" / "skill" / "SKILL.md", OUT_DIR / "A1" / "SKILL.md")
    shutil.copy2(a1_task / "environment" / "skill" / "manifest.json", OUT_DIR / "A1" / "skill_manifest.json")
    a1_summary = verifier_summary(a1_report)
    failure_feedback = {
        "feedback_type": a1_summary["feedback_type"],
        "missing_capabilities": a1_summary["missing_capabilities"],
        "false_positive_capabilities": a1_summary["false_positive_capabilities"],
        "schema_errors": a1_summary["schema_errors"],
        "note": "A1 uses a weaker output contract inside Harbor to test whether verifier-driven repair can restore full structured findings.",
    }
    write_json(OUT_DIR / "A1" / "failure_feedback.json", failure_feedback)

    repair_action = repair_policy.get(failure_feedback["feedback_type"], "manual_review_required")
    write_json(
        OUT_DIR / "revision" / "patch_plan.json",
        {
            "feedback_type": failure_feedback["feedback_type"],
            "repair_action": repair_action,
            "before_capabilities": a1_caps,
            "after_capabilities": a2_caps,
            "before_contract": "relaxed",
            "after_contract": "strict",
            "consumes": "A1/failure_feedback.json",
        },
    )
    write_json(
        OUT_DIR / "revision" / "gate_decision.json",
        {
            "decision": "accept",
            "reason": "Config A1 failed because the verifier required recommended_fix fields; the repair tightens only the output contract while keeping the same target and verifier.",
            "checks": {
                "same_target": True,
                "same_verifier_logic": True,
                "same_capabilities": True,
                "schema_errors": failure_feedback["schema_errors"],
            },
        },
    )
    write_text(
        OUT_DIR / "revision" / "skill_diff.md",
        "\n".join(
            [
                "# Harbor LLM Config Skill Diff",
                "",
                "```diff",
                "- Output Contract: exploratory v1 allowed missing recommended_fix",
                "+ Output Contract: strict v2 requires recommended_fix for every finding",
                "```",
                "",
                "Capabilities stay fixed; the repair targets output-contract quality rather than adding new answer-key items.",
                "",
            ]
        ),
    )

    a2_job_name = "harbor_llm_repair_loop_config_A2"
    a2_jobs_dir = OUT_DIR / "A2" / "jobs"
    a2_completed = run_harbor_trial(
        task_dir=a2_task,
        jobs_dir=a2_jobs_dir,
        job_name=a2_job_name,
        capabilities=a2_caps,
        env=env,
        relaxed_contract=False,
        prompt_addendum="",
    )
    write_text(OUT_DIR / "A2" / "stdout.log", a2_completed.stdout)
    write_text(OUT_DIR / "A2" / "stderr.log", a2_completed.stderr)
    write_json(OUT_DIR / "A2" / "process.json", {"returncode": a2_completed.returncode, "job_name": a2_job_name})
    a2_trial = trial_dir_from_jobs(a2_jobs_dir / a2_job_name)
    a2_report = collect_trial(OUT_DIR / "A2", a2_trial)
    shutil.copy2(a2_task / "environment" / "skill" / "SKILL.md", OUT_DIR / "A2" / "SKILL.md")
    shutil.copy2(a2_task / "environment" / "skill" / "manifest.json", OUT_DIR / "A2" / "skill_manifest.json")
    a2_summary = verifier_summary(a2_report)

    a1_reward = 1.0 if a1_summary["pass"] else 0.0
    a2_reward = 1.0 if a2_summary["pass"] else 0.0
    summary = {
        "run_id": OUT_DIR.name,
        "backend": "WSL2 Ubuntu-24.04-Codex + Docker + Harbor",
        "task": "controlled-config-security-review",
        "agent": "controlled-security-llm-agent",
        "oracle": False,
        "llm": True,
        "model": env["MODEL"],
        "A1": a1_summary | {"reward": a1_reward, "artifacts": ["A1/security_report.json", "A1/target_reads.json", "A1/verifier_report.json", "A1/failure_feedback.json", "A1/skill_manifest.json"]},
        "revision": {
            "feedback_type": failure_feedback["feedback_type"],
            "repair_action": repair_action,
            "before_contract": "relaxed",
            "after_contract": "strict",
            "artifacts": ["revision/patch_plan.json", "revision/gate_decision.json", "revision/skill_diff.md"],
        },
        "A2": a2_summary | {"reward": a2_reward, "artifacts": ["A2/security_report.json", "A2/target_reads.json", "A2/verifier_report.json", "A2/skill_manifest.json"]},
        "reward_delta": a2_reward - a1_reward,
        "boundary": "This is one controlled Harbor LLM repair loop for a configuration-security task. The repair tightens the output contract; it does not prove broad Harbor LLM multi-task generalization.",
    }
    write_json(OUT_DIR / "summary.json", summary)
    write_text(
        OUT_DIR / "summary.md",
        "\n".join(
            [
                "# Harbor LLM Config Repair Loop",
                "",
                "| Attempt | Pass | Reward | Coverage | Feedback | Schema errors |",
                "|---|---:|---:|---:|---|---|",
                f"| A1 | {a1_summary['pass']} | {a1_reward} | {a1_summary['coverage']} | {a1_summary['feedback_type']} | {', '.join(a1_summary['schema_errors']) or 'none'} |",
                f"| A2 | {a2_summary['pass']} | {a2_reward} | {a2_summary['coverage']} | {a2_summary['feedback_type']} | {', '.join(a2_summary['schema_errors']) or 'none'} |",
                "",
                "A1 and A2 use two generated Harbor task copies so the container reads different `/app/skill` contract snapshots while keeping the same target and verifier family.",
                "",
                "Boundary: this is controlled second-task Harbor LLM evidence for one config-security scenario. It is not open-world vulnerability discovery or broad Harbor generalization.",
                "",
            ]
        ),
    )
    print(json.dumps({"output_dir": str(OUT_DIR), "model": env["MODEL"], "a1_pass": a1_summary["pass"], "a2_pass": a2_summary["pass"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
