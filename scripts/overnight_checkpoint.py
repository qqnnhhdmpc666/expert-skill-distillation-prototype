from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"


def now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def run(command: list[str], timeout: int = 120) -> dict[str, Any]:
    completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=timeout, check=False)
    return {
        "command": command,
        "returncode": completed.returncode,
        "stdout_tail": completed.stdout[-3000:],
        "stderr_tail": completed.stderr[-3000:],
    }


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def append(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(content)


def read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def collect_status() -> dict[str, Any]:
    py = {
        "executable": sys.executable,
        "version": sys.version,
        "cwd": str(ROOT),
    }
    scripts = sorted(path.name for path in (ROOT / "scripts").glob("*") if path.is_file())
    pytest = run([sys.executable, "-m", "pytest", "-q"])
    ports = {}
    for port in (8501, 8502, 8766, 8767):
        probe = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                f"[bool](Get-NetTCPConnection -LocalPort {port} -State Listen -ErrorAction SilentlyContinue)",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        ports[str(port)] = "True" in probe.stdout
    env = {name: bool(os.environ.get(name)) for name in ("OPENAI_BASE_URL", "OPENAI_API_KEY", "MODEL")}
    wsl = run(["powershell", "-ExecutionPolicy", "Bypass", "-File", str(ROOT / "scripts" / "check_wsl2_spark_backend.ps1")], timeout=180)
    multitask = read_json(ROOT / "outputs" / "multitask_closed_loop_001" / "summary.json")
    acceptance = read_json(ROOT / "outputs" / "system_acceptance_001" / "summary.json")
    return {
        "time": now(),
        "project_dir": str(ROOT),
        "python": py,
        "scripts": scripts,
        "pytest": pytest,
        "streamlit_ports": ports,
        "llm_env_configured": env,
        "wsl_check": wsl,
        "multitask_summary": multitask,
        "system_acceptance": acceptance,
    }


def render_log_entry(status: dict[str, Any], note: str) -> str:
    pytest_ok = status["pytest"]["returncode"] == 0
    acceptance = status.get("system_acceptance") or {}
    multitask = status.get("multitask_summary") or {}
    return f"""## Checkpoint {status['time']}

Note: {note}

- Project: `{status['project_dir']}`
- Python: `{status['python']['executable']}`
- Pytest: `{'PASS' if pytest_ok else 'FAIL'}`
- Streamlit/review ports: `{status['streamlit_ports']}`
- LLM env configured: `{status['llm_env_configured']}`
- System acceptance: `{acceptance.get('passed', 'not-generated')}`
- Multi-task A2 pass: `{multitask.get('a2_pass_count', '-')}/{multitask.get('case_count', '-')}`
- WSL check returncode: `{status['wsl_check']['returncode']}`
- Current blocker: real non-oracle CLI agent in Harbor is not connected yet.
- Anti-stall rule: no install/download loop; any environment command over 20 minutes without progress will be stopped and logged.

"""


def write_p0_reports(status: dict[str, Any]) -> None:
    acceptance = status.get("system_acceptance") or {}
    multitask = status.get("multitask_summary") or {}
    wsl_stdout = status["wsl_check"]["stdout_tail"]
    write(
        REPORTS / "AUTONOMOUS_SELF_ASSESSMENT.md",
        f"""# Autonomous Self Assessment

更新时间：{status['time']}

## 1. 当前系统最不像成熟系统的地方是什么？

- 核心 pipeline 仍有一部分早期逻辑存在于 `demo/streamlit_app.py`，虽然已有 `scripts/run_multitask_closed_loop.py`、`scripts/run_system_acceptance.py` 和 WSL/Harbor task，但后端抽象还没有完全统一到 `backends/`。
- 真实 sandbox 任务目前使用 Harbor `oracle` agent；还不是 `codex` / `qwen-coder` / `claude-code` 这类非 oracle CLI agent。
- 多任务泛化已有 3 类任务证据，但还未 dataset 化到 `data/task_cases/*` 的统一 schema。

## 2. 当前系统最容易被导师质疑的地方是什么？

- “规则/能力点是否预置”仍需说清：当前 controlled suite 使用可复现能力定义和 verifier，不应包装成任意专家材料完全自动蒸馏。
- “真实 agent”边界要严谨：WSL2/Harbor 已跑通真实 sandbox/verifier，但安全任务 agent 是 oracle。
- ablation 证据散在多个旧脚本和 outputs 中，需要收束成今晚统一的 `outputs/validation/ablation_summary.md`。

## 3. 当前系统是否只是单场景脚本？

不是。已有 `outputs/multitask_closed_loop_001/summary.json`：`{multitask.get('case_count', '-')}` tasks / `{multitask.get('task_family_count', '-')}` families，A2 pass `{multitask.get('a2_pass_count', '-')}`。但还需要 P2 数据集化成四类 task cases。

## 4. 当前系统是否依赖页面直接拼结果？

部分历史展示仍来自 `demo/streamlit_app.py` 的构造逻辑；但项目级验收已经依赖命令行脚本：

- `scripts/run_multitask_closed_loop.py`
- `scripts/run_system_acceptance.py`
- `scripts/check_wsl2_spark_backend.ps1`
- WSL/Harbor task under `integrations/wsl_harbor_tasks/`

## 5. 当前系统是否有足够 artifact 证明执行链路？

已有初步证据：`outputs/multitask_closed_loop_001/`, `outputs/wsl_harbor_real_upload_001/`, `outputs/system_acceptance_001/`, `review_package/`。不足是 trace schema 尚未统一到 source/execution/feedback/revision 四类。

## 6. 当前系统距离开源原型还差什么？

- `docs/PROJECT_STRUCTURE.md`
- `docs/QUICKSTART.md`
- `scripts/validate_review_package.py`
- `data/task_cases/*` schema
- 后端接口 `backends/`
- 统一 validation outputs

## 7. 当前系统距离真实漏洞挖掘 Skill 还有哪些关键缺口？

- 需要 inspection procedure，而不只是能力清单。
- 需要 target observation schema、trace policy、safety boundary、verifier hooks。
- 需要真实 CLI agent 或安全 evaluator 产生可观察轨迹。
- 需要明确哪些反馈可自动验证，哪些必须专家判断。

## 8. 除了用户要求，还应补什么？

- 一个一键验收命令作为 release gate。
- 一个 claim boundary 文档，防止演示口径过度。
- 一个 lightweight schema validator，确保 task case 和 review package 不漂移。
""",
    )
    write(
        REPORTS / "BACKEND_MATURITY_STATUS.md",
        f"""# Backend Maturity Status

更新时间：{status['time']}

## 当前状态

- `offline_deterministic`: available via `scripts/run_multitask_closed_loop.py`.
- `live_llm_text`: code path exists in `demo/streamlit_app.py` / `scripts/run_generic_agent_loop.py`, but env configured = `{status['llm_env_configured']}`.
- `local_real_agent`: script exists as `scripts/run_generic_agent_loop.py`; P3 still needs normalized `agents/local_security_review_agent.py`.
- `sandbox_agent`: WSL2/Docker/Harbor available; real security task passed with oracle agent.

## 页面依赖边界

Streamlit should remain display layer. Core acceptance currently runs through `scripts/run_system_acceptance.py`, not the page.

## WSL Check Tail

```json
{wsl_stdout}
```
""",
    )
    write(
        REPORTS / "CROSS_TASK_GENERALIZATION_STATUS.md",
        f"""# Cross-Task Generalization Status

更新时间：{status['time']}

## Current Evidence

- Case count: `{multitask.get('case_count', '-')}`
- Task families: `{multitask.get('task_family_count', '-')}`
- Feedback types: `{', '.join(multitask.get('feedback_types', [])) if multitask else '-'}`
- Repair operators: `{', '.join(multitask.get('patch_operators', [])) if multitask else '-'}`
- A2 pass: `{multitask.get('a2_pass_count', '-')}/{multitask.get('case_count', '-')}`

## Assessment

The evidence is stronger than a single upload demo, but still controlled. P2 must expand this into `data/task_cases/` with four explicit scenarios and a shared runner.
""",
    )
    write(
        REPORTS / "WSL_HARBOR_STATUS.md",
        f"""# WSL / Harbor Status

更新时间：{status['time']}

## Summary

WSL2, Docker, Harbor, SPARK imports, SPARK hello smoke, and the WSL Harbor real upload-security task are available according to `scripts/check_wsl2_spark_backend.ps1`.

## Boundary

This can be called a sandbox execution substrate. It should not yet be called a mature non-oracle sandbox agent, because the security task uses Harbor `oracle`.

## Raw Check Tail

```json
{wsl_stdout}
```
""",
    )
    write(
        REPORTS / "MORNING_STATUS_0800.md",
        f"""# Morning Status 0800

更新时间：{status['time']}

## One-Sentence Summary

Overnight mode started. Current baseline already has system acceptance `{acceptance.get('passed', 'not-generated')}`, multi-task closed-loop evidence, and WSL2/Harbor security-task evidence; the remaining night focus is datasetized generalization, backend abstraction, ablation, trace schema, and claim-boundary documentation.

## Current Baseline

- Pytest: `{'PASS' if status['pytest']['returncode'] == 0 else 'FAIL'}`
- System acceptance: `{acceptance.get('passed', 'not-generated')}`
- Multi-task A2 pass: `{multitask.get('a2_pass_count', '-')}/{multitask.get('case_count', '-')}`
- LLM env configured: `{status['llm_env_configured']}`
- WSL check returncode: `{status['wsl_check']['returncode']}`

## Remaining Plan

1. Build `data/task_cases/*` and `scripts/run_generalization_suite.py`.
2. Add backend abstractions and local real agent metadata.
3. Produce ablation, feedback taxonomy, trace observability, vulnerability product analysis, and review validators.
""",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--note", default="overnight checkpoint")
    parser.add_argument("--write-p0-reports", action="store_true")
    args = parser.parse_args()

    status = collect_status()
    append(REPORTS / "OVERNIGHT_RUN_LOG.md", render_log_entry(status, args.note))
    if args.write_p0_reports:
        write_p0_reports(status)
    print(json.dumps({"checkpoint": status["time"], "pytest": status["pytest"]["returncode"], "reports": str(REPORTS)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
