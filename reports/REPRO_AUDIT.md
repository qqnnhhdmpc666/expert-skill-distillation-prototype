# 复现审查记录

审查日期：2026-06-03

## 1. 审查目标

本报告记录 `SPARK-PDI` 和 `COLLEAGUE.SKILL` 两个开源工作的真实可用程度。

第一层任务的目标不是完整复现实验结果，而是判断：

- 仓库能不能获取；
- 环境依赖是否清楚；
- demo 或最小链路能不能跑；
- 核心 pipeline 在哪里；
- 输入输出格式是什么；
- 哪些模块可以用于两周 demo；
- 哪些模块需要简化或重写。

## 2. 本地获取情况

Git clone 直接拉取 GitHub 仓库时出现网络连接重置或超时。改用 GitHub zip 包下载成功。

本地缓存位置：

- `D:\solution\external_repos\spark-skills`
- `D:\solution\external_repos\colleague-skill`

结论：

- 两个仓库都已经成功获取到本地。
- 后续审查可基于本地文件继续推进。
- 不建议依赖 `git clone` 作为演示环境准备方式，zip 下载更稳。

## 3. COLLEAGUE.SKILL 审查

仓库：

- `https://github.com/titanwings/colleague-skill`

默认分支：

- `dot-skill`

本地路径：

- `D:\solution\external_repos\colleague-skill`

### 3.1 定位

当前仓库已经从 `colleague.skill` 扩展为 `dot-skill`。

它更像一个跨 host 的 agent skill 创建器，而不是一个传统 Python package。它的核心能力是把人物、同事、关系对象或公众人物材料组织成可安装、可调用、可版本管理的 skill artifact。

对我们项目最相关的是：

- skill artifact schema；
- work / persona 双层结构；
- `SKILL.md` 渲染方式；
- `manifest.json` 元数据；
- 版本更新和 rollback；
- correction log。

对我们项目不建议直接使用的是：

- Feishu / DingTalk / Slack 自动采集；
- 私人聊天记录导入；
- 关系对象 / 明星人格复刻场景；
- 任何涉及隐私或人格模拟的 demo 数据。

### 3.2 安装与环境

仓库要求：

- Python 3.9+
- `requests>=2.28.0`
- 可选：`pypinyin>=0.48.0`
- 可选：`playwright>=1.40.0`
- 可选：`slack-sdk>=3.27.0`
- 可选：`python-docx>=1.1.0`
- 可选：`openpyxl>=3.1.0`

本地环境：

- Python 3.13.1

结论：

- 核心 artifact writer 不需要重依赖。
- 自动数据采集能力依赖平台凭证和可选库，不适合作为两周 demo 的主链路。
- 对我们的 demo，可以只借鉴 artifact writer / schema / version manager 思路。

### 3.3 Demo 可运行性

已运行本地测试：

```powershell
python -m unittest tests.test_skill_writer tests.test_cli_lifecycle
```

运行结果：

```text
Ran 15 tests in 3.268s
OK
```

覆盖能力：

- 创建 skill；
- 生成 `SKILL.md`；
- 生成 `work.md`；
- 生成 `persona.md`；
- 生成 `work_skill.md`；
- 生成 `persona_skill.md`；
- 生成 `manifest.json`；
- 生成 `meta.json`；
- list 已有 skill；
- update skill；
- correction JSON 写入；
- version backup；
- rollback。

结论：

- COLLEAGUE.SKILL 的核心 artifact 生命周期可以本地跑通。
- 它适合作为我们 full skill package 和 version log 的参考。

### 3.4 核心 Pipeline

关键文件：

- `SKILL.md`
- `tools/skill_writer.py`
- `tools/skill_schema.py`
- `tools/skill_presets.py`
- `tools/version_manager.py`
- `tests/test_skill_writer.py`
- `tests/test_cli_lifecycle.py`

核心流程：

```text
输入 meta.json + work.md + persona.md
-> normalize metadata
-> render combined SKILL.md
-> render work-only skill
-> render persona-only skill
-> write manifest.json / meta.json
-> update 时备份旧版本
-> correction 写入 persona 或 patch 合并到 work/persona
-> rollback 恢复历史版本
```

artifact 结构：

- `SKILL.md`：组合 skill；
- `work.md`：工作能力内容；
- `persona.md`：表达风格或人物侧内容；
- `work_skill.md`：仅工作能力 skill；
- `persona_skill.md`：仅 persona skill；
- `manifest.json`：安装和元数据；
- `meta.json`：完整 schema 元数据；
- `versions/`：历史版本。

### 3.5 可复用部分

可直接借鉴：

- `Full Skill Package` 与调用 skill 分离的思想；
- `manifest.json` + `meta.json` 的 artifact 管理方式；
- `version_manager.py` 的版本备份和回滚方式；
- `skill_writer.py` 的 create / update / list CLI 结构；
- correction log 的增量更新方式；
- 多 host skill 安装元数据设计。

建议改造：

- 将 `work/persona` 改为 `capability/behavior/evidence` 或 `full/compact`；
- 将 correction 从 persona 修正改为 rule-level 修正；
- 将 manifest 增加 evidence coverage、verification status、compact skill 指标；
- 删除私人数据采集相关路径；
- 保留公开/合成材料输入。

### 3.6 需要简化或重写部分

不建议直接复用：

- Feishu / DingTalk / Slack 采集器；
- 关系对象或公众人物复刻 prompt；
- persona 模拟逻辑；
- host 安装器作为 demo 主路径。

需要我们自研：

- 专家规则抽取；
- evidence chunking；
- rule-to-evidence mapping；
- unsupported / weak / conflict 判定；
- repair loop；
- compact invocation skill 生成；
- cost summary。

### 3.7 对我们 Demo 的价值

COLLEAGUE.SKILL 对我们最有价值的是 artifact 工程形态：

- 它证明了 skill 可以被写成一组可安装、可版本管理的文件；
- 它的 `create/update/list/rollback` 生命周期可以作为我们 demo 的工程骨架；
- 它没有内置我们需要的证据覆盖验证，因此正好给我们留下整合 SPARK-PDI 的空间。

## 4. SPARK-PDI 审查

仓库：

- `https://github.com/EtaYang10th/spark-skills`

默认分支：

- `main`

本地路径：

- `D:\solution\external_repos\spark-skills`

### 4.1 定位

SPARK 是一个研究原型，用于把环境验证过的执行轨迹蒸馏成可复用 agent skills。

核心思想：

- 不只从 plan 蒸馏；
- 从 agent 实际执行、环境反馈和 verifier 结果中蒸馏；
- 用 PDI 检查 skill 是否真的吸收了 posterior execution evidence；
- PDI 既可以作为离线诊断，也可以作为在线 intervention 信号。

### 4.2 安装与环境

仓库要求：

- Python >= 3.12
- `uv`
- Docker
- Harbor
- OpenAI-compatible LLM endpoint
- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- 可选：`DASHSCOPE_API_KEY`

`pyproject.toml` 关键依赖：

- `harbor @ git+https://github.com/laude-institute/harbor.git`
- `litellm>=1.80.0`
- `fastapi>=0.115.0`
- `uvicorn[standard]>=0.32.0`
- `claude-agent-sdk==0.1.48`

本地环境检查：

- Python 可用，但版本是 3.13.1；
- `docker` 不存在；
- `uv` 不存在。

结论：

- SPARK 完整 pipeline 当前不能直接在本机运行。
- 阻塞点不是代码不存在，而是缺少 Docker、uv、Harbor 和 LLM endpoint 配置。
- 两周 demo 不应依赖完整 SPARK pipeline 实时执行。

### 4.3 官方 Demo 命令

任务生成：

```bash
uv run python run_tasks_gen.py \
  --prompt-file spark_tasks_gen/examples/3d_scan_calc_prompt.json \
  --model gpt-5.4
```

技能生成：

```bash
uv run python run_pipeline.py \
  --agent qwen-coder \
  --model qwen3-coder-next \
  --tasks-dir tasks-no-skills \
  --max-retries 3 \
  --parallelism 4
```

启用 PDI：

```bash
uv run python run_pipeline.py \
  --pdi-enabled \
  --pdi-method token_overlap
```

观察 PDI 但不干预：

```bash
uv run python run_pipeline.py \
  --pdi-observe-only \
  --pdi-method js_divergence
```

### 4.4 本地最小运行验证

完整 pipeline 因缺少 Docker 和 uv 未运行。

进一步检查无 Docker 可行性：

- `run_tasks_gen.py --help` 可在当前 Windows Python 环境下启动；
- `run_eval_skills.py --help` 可在当前 Windows Python 环境下启动；
- `run_pipeline.py --help` 当前先因缺少 `litellm` 失败；
- 但静态检查显示，真正运行 `run_pipeline.py` 时会调用 `cleanup_stale_docker_artifacts()`、`prefetch_base_images()` 和 Harbor；
- `spark_tasks_gen/validator.py` 会调用 `uv run harbor tasks check` 和 `uv run harbor run`；
- `spark_skills_gen/executor.py` 明确通过 `uv run harbor run` 在 Docker container 中执行任务。

结论：

- 无 Docker 可以做离线分析、读取已有轨迹、运行 PDI tracker、研究 evidence block；
- 无 Docker 不适合跑通 SPARK 的真实 skill generation / evaluation pipeline；
- 如果目标是“完整复现第一篇的执行-验证-蒸馏流程”，需要接受安装 Docker / uv / Harbor；
- 如果目标是“两周 demo”，可以先走 offline fallback，不把 Docker 作为主路径依赖。

已运行轻量 PDI tracker smoke test：

```powershell
python - <<'PY'
from spark_skills_gen.context import PDITracker
tracker = PDITracker(enabled=True, method="token_overlap")
...
PY
```

运行结果：

- `PDITracker` 可以本地导入；
- `compute()` 可以输出 `proxy_exec`、`proxy_plan`、`proxy_oss`、`raw_pdi`、`weighted_pdi`、`triggered`、`level`；
- 该模块不依赖 Docker 或 Harbor；
- 适合作为我们 offline verifier 的参考实现。

### 4.5 核心 Pipeline

关键文件：

- `run_pipeline.py`
- `run_tasks_gen.py`
- `run_eval_skills.py`
- `spark_skills_gen/pipeline.py`
- `spark_skills_gen/context.py`
- `spark_skills_gen/trajectory.py`
- `spark_skills_gen/skill_evidence.py`
- `spark_skills_gen/summarizer.py`
- `spark_skills_gen/executor.py`
- `spark_skills_gen/judge.py`

技能生成流程：

```text
execute
-> judge
-> reflect
-> retry
-> collect successful trajectory
-> build six evidence blocks
-> generate SKILL.md
```

六类 evidence block：

- Task Pattern；
- Success Execution Chain；
- Success Verification Signals；
- Lessons From All Attempts；
- Environment Affordances；
- Raw Support Tail。

PDI tracker 逻辑：

```text
current memo + previous memo + agent commands + test summary
-> proxy_exec：执行证据被 memo 吸收的程度
-> proxy_plan：策略是否停滞
-> proxy_oss：memo 是否固化
-> raw_pdi = exec - plan - oss
-> warmup weighting
-> low PDI triggers soft / strong intervention
```

支持的 PDI 方法：

- `token_overlap`
- `js_divergence`

### 4.6 仓库自带可用材料

本地 zip 包中包含公开示例结果：

- `spark_skills_gen/skills_gen_result/all_model_pdi/*/SKILL.md`
- `spark_skills_gen/skills_gen_result/all_model_pdi/*/attempts.json`
- `spark_skills_gen/skills_gen_result/all_model_pdi/*/trajectory.jsonl`

这些材料可用于：

- 学习 SPARK 的 skill 输出风格；
- 学习 successful trajectory 如何组织；
- 学习 verifier/test summary 如何成为 evidence；
- 设计我们的 offline evidence coverage report。

注意：

- 原始 trajectory 中可能包含历史运行环境字段和 redacted API 字段；
- 不应直接把原始轨迹全文放进我们的 demo；
- 只应抽取公开结构和非敏感的证据组织方式。

### 4.7 可复用部分

可直接借鉴：

- `trajectory.jsonl` 的事件记录方式；
- `attempts.json` 的 attempt / reward / test summary 结构；
- `SkillEvidence` 六块证据结构；
- PDI tracker 中 `proxy_exec / proxy_plan / proxy_oss` 的思想；
- online intervention 的 soft / strong 分级；
- dashboard 展示 PDI history 的思路。

建议改造：

- 将 `agent commands + test summary` 替换为 `expert material chunks + rule evidence`；
- 将 `proxy_exec` 改为 rule 是否有明确 evidence；
- 将 `proxy_plan` 改为生成规则是否过度沿用模板或泛化；
- 将 `proxy_oss` 改为 unsupported 规则在修正轮次中是否反复出现；
- 将 PDI intervention 改为 repair suggestion。

### 4.8 需要简化或重写部分

不适合作为两周 demo 主路径：

- Dockerized task execution；
- Harbor agent execution；
- task construction pipeline；
- full cross-model evaluation；
- Hugging Face 全量数据下载；
- 实时 dashboard。

需要我们自研或简化：

- Markdown / JSON 专家材料 ingestion；
- evidence chunker；
- skill package schema；
- offline evidence verifier；
- repair loop；
- compact invocation skill builder；
- cost summary。

### 4.9 对我们 Demo 的价值

SPARK-PDI 对我们最有价值的是验证思想，而不是完整执行环境。

我们可以把它转化为：

```text
SPARK: execution trajectory -> evidence-backed skill
我们: expert material chunks -> evidence-backed expert skill
```

最现实的复用路径：

- 不跑完整 Harbor；
- 复用 PDI 的“证据优先”原则；
- 复用 evidence block 组织方式；
- 复用 trajectory / attempt / verifier report 的记录思想；
- 实现一个 offline evidence coverage verifier。

### 4.10 Windows 可运行性判断

当前机器是 Windows / PowerShell 环境。

可在 Windows 原生环境完成：

- 查看和审查源码；
- 运行 COLLEAGUE.SKILL 的 artifact writer 测试；
- 读取 SPARK 已发布的 `SKILL.md`、`attempts.json`、`trajectory.jsonl`；
- 运行 SPARK 的 `PDITracker` 等纯 Python 离线模块；
- 实现我们自己的 demo pipeline。

不建议在 Windows 原生环境直接跑：

- SPARK 的完整 Harbor execution；
- Dockerized task execution；
- cross-model evaluation；
- 大规模 SkillsBench 任务复现。

推荐环境：

- Windows + Docker Desktop + WSL2 Ubuntu；
- 在 WSL2 内安装 Python 3.12、uv、Harbor；
- 通过 Docker Desktop WSL integration 执行 Linux container 任务。

原因：

- SPARK 的任务环境是 Docker / Linux container；
- Harbor 和任务脚本更接近 Linux 工作流；
- Windows 路径、权限、换行、容器挂载容易引入额外问题；
- WSL2 更接近论文作者预期的运行环境。

## 5. 两周 Demo 决策

### 5.1 直接复用模块

- COLLEAGUE.SKILL 的 artifact 生命周期设计；
- COLLEAGUE.SKILL 的 `create/update/list/rollback` CLI 思路；
- COLLEAGUE.SKILL 的 `manifest.json` / `meta.json` 思路；
- SPARK 的 six evidence blocks 思路；
- SPARK 的 `trajectory.jsonl` / `attempts.json` 记录思路；
- SPARK 的 PDI proxy 指标思想。

### 5.2 思想复现模块

- SPARK 的 online trajectory verification；
- SPARK 的 PDI intervention；
- COLLEAGUE.SKILL 的 work/persona 双层结构。

在我们的 demo 中对应为：

```text
专家材料 -> full skill package
full skill package -> evidence coverage report
unsupported / weak / conflict -> repair suggestion
verified full skill -> compact invocation skill
```

### 5.3 需要自研模块

- 专家材料 ingestion；
- rule extraction；
- evidence chunking；
- rule-to-evidence mapping；
- evidence coverage verifier；
- repair loop；
- compact skill builder；
- cost metrics。

### 5.4 风险最高模块

- 完整运行 SPARK 的 Docker / Harbor pipeline；
- 使用真实专家材料导致隐私风险；
- 直接套用 COLLEAGUE.SKILL 的 persona 场景导致任务偏题；
- 过度宣称“自动正确”。

### 5.5 最小可交付版本

建议最小可交付版本为：

```text
输入：合成 API / 代码评审专家材料
输出 1：Full Skill Package
输出 2：Evidence Coverage Report
输出 3：Repair Log
输出 4：Compact Invocation Skill
输出 5：Cost Summary
```

### 5.6 当前结论

第一层任务结论：

- 两篇工作都已开源；
- COLLEAGUE.SKILL 的核心 artifact 生命周期可本地跑通；
- SPARK-PDI 的完整 pipeline 当前受 Docker / uv / Harbor 阻塞，不适合作为 demo 实时依赖；
- SPARK-PDI 的 PDI tracker、evidence block 和公开示例轨迹可用于 offline 简化复现；
- 我们应优先实现自己的轻量闭环，而不是试图把两个仓库完整拼接起来。

推荐下一步：

- 产出 `D:\solution\docs\SKILL_PACKAGE_SCHEMA.md`；
- 选择 API / 代码评审作为安全 demo 场景；
- 准备 `D:\solution\data\README_DATA.md` 和合成专家材料；
- 开始实现 `Material Ingestion -> Skill Distiller -> Evidence Verifier` 的最小 pipeline。
