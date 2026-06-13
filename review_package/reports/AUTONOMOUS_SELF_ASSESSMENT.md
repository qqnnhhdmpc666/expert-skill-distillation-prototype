# Autonomous Self Assessment

更新时间：2026-06-08T06:24:53+08:00

## 1. 当前系统最不像成熟系统的地方是什么？

- 核心 pipeline 仍有一部分早期逻辑存在于 `demo/streamlit_app.py`，虽然已有 `scripts/run_multitask_closed_loop.py`、`scripts/run_system_acceptance.py` 和 WSL/Harbor task，但后端抽象还没有完全统一到 `backends/`。
- 真实 sandbox 任务目前使用 Harbor `oracle` agent；还不是 `codex` / `qwen-coder` / `claude-code` 这类非 oracle CLI agent。
- 多任务泛化已有 3 类任务证据，但还未 dataset 化到 `data/task_cases/*` 的统一 schema。

## 2. 当前系统最容易被导师质疑的地方是什么？

- “规则/能力点是否预置”仍需说清：当前 controlled suite 使用可复现能力定义和 verifier，不应包装成任意专家材料完全自动蒸馏。
- “真实 agent”边界要严谨：WSL2/Harbor 已跑通真实 sandbox/verifier，但安全任务 agent 是 oracle。
- ablation 证据散在多个旧脚本和 outputs 中，需要收束成今晚统一的 `outputs/validation/ablation_summary.md`。

## 3. 当前系统是否只是单场景脚本？

不是。已有 `outputs/multitask_closed_loop_001/summary.json`：`3` tasks / `3` families，A2 pass `3`。但还需要 P2 数据集化成四类 task cases。

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
