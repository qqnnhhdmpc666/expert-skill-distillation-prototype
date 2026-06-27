# 项目说明书（30 分钟接手版）

如果你刚打开这个仓库，不要先被目录数量吓到。它的主线其实很简单，但不是“只做 Skill”：

> 把材料拆成知识库 / RAG、可固化 Skill 和执行轨迹三层，再让它们在 evidence 和 verifier 约束下互相更新。

## 1. 先看什么

按这个顺序就够：

1. `README.md`
2. `docs/USER_MANUAL_ZH.md`
3. `docs/CLAIM_BOUNDARY.md`
4. `docs/HYBRID_KNOWLEDGE_SKILL_TRAJECTORY_ARCHITECTURE.md`
5. `reports/OPEN_WORLD_DISTILLATION_VALIDATION_STATUS.md`
6. `reports/OPEN_WORLD_CLOSED_LOOP_STATUS.md`
7. `reports/TEACHING_UTILITY_V02_STATUS.md`
8. `reports/TEACHER_PROGRESS_BRIEF_20260616.md`

## 2. 这个仓库真正的三个核心

### 核心 A：Knowledge Base / RAG

知识库保存不适合固化为 Skill 的内容：

- 会变化的事实，例如版本、依赖、API 行为、漏洞公告；
- 大量案例，例如历史漏洞、失败日志、真实修复记录；
- 背景材料，例如论文、标准、设计文档、团队经验；
- 具体异常处理经验。

它不是 Skill 的竞争方案，而是 Skill 执行时的动态上下文来源。

### 核心 B：材料蒸馏为 Skill

输入可以是：

- 专家知识
- 用户规则
- 公开材料

输出是：

- 可安装的 Skill package
- 可追溯的 distillation provenance

Skill 只固化稳定、可迁移、可复用的 how-to 流程，不把所有案例都塞进去。

### 核心 C：轨迹驱动的 Skill / RAG 更新

Skill 安装进 runtime 后：

- 在任务里执行
- 留下 evidence bundle
- verifier 给出 pass / fail / missing capability / false positive / scope violation
- 系统再生成 candidate Skill
- 通过 promote / reject / rollback gate 决定是否晋升
- 轨迹也可以进入知识库，成为后续 RAG 检索的案例

## 3. 当前最重要的结论

### 已经成立的

- Skill 作为 installable runtime object 这条机制链已经成立
- 项目方向已经明确为 Knowledge Base + Skill + Trajectory 的混合结构
- bounded open-world 自动蒸馏已经有支持性 fresh evidence
- bounded evolution improvement 已经有更真实的 fresh evidence
- teaching-utility 这条线保留了真实负结果

### 新的研究判断

- 固定流程适合蒸馏为 Skill；
- 动态事实、具体案例和异常处理仍需要 RAG / 知识库；
- 轨迹不是简单的“成功样本”，而是同时用于验证 Skill、更新 Skill、补充知识库的经验数据；
- benchmark 需要同时比较 RAG-only、Skill-only、RAG+Skill、trajectory feedback 的贡献。

### 目前最强的 open-world 证据

#### 自动蒸馏

- 最新 fresh rerun：bounded public-material distillation `8 / 10`
- 当前 baseline：`8 / 10`
- 更早一次 fresh run：distilled `8 / 10`，baseline `7 / 10`

这说明当前有界公开材料蒸馏已经能达到安装版基线水平，并且出现过严格超过基线的 fresh run。

#### Skill 进化

- 一次 fresh generated-candidate run：`3 / 3` strict promotion proposals
- 一次 frozen-candidate repeatability run：`4 / 5` strict promotion proposals
- frozen candidate 平均分差：`+0.0333`
- 但不是每一轮都严格更优，所以仍然保留 repeatability caveat

这说明：

> 在当前有界 open-world 线上，系统已经不只是“偶尔改对一次”，而是拿到了更接近 repeatable improvement 的证据。

## 4. 这个仓库最重要的目录

```text
src/skill_deployment/   runtime、distillation、install state、verifier、CLI
agents/                 live / local agent 执行器
scripts/                入口脚本、实验脚本、导出脚本
data/                   task cases、holdout、公开材料验证样本
demo/                   最小材料示例
outputs/                distilled skills、installed skills、runtime evidence、pilot 结果
reports/                阶段报告、claim 校准、实验结论
docs/                   用户说明、项目说明、边界说明
review_package/         对外评审材料
```

## 5. 如果你只想先跑一次

### 跑内置 Skill

```powershell
python -m pip install -e .[dev]
skill-deploy build-codex-skill
skill-deploy install --skill outputs/deployable_codex_skill/secure_code_review --version v2
skill-deploy run-skill --installed secure_code_review --case upload_security_001 --backend offline_deterministic
```

### 跑 bounded open-world 自动蒸馏

```powershell
$env:OPENAI_API_KEY = "<your key>"
skill-deploy open-world-distill-validation --skill-id secure_code_review_open_world_hybrid_distilled --version v1 --backend live_llm_text --base-url https://api.deepseek.com --model deepseek-v4-flash --projection-mode hybrid_semantic
```

### 跑 bounded open-world 演化

```powershell
$env:OPENAI_API_KEY = "<your key>"
skill-deploy open-world-closed-loop --installed secure_code_review_open_world_hybrid_distilled --repeats 5 --base-url https://api.deepseek.com --model deepseek-v4-flash --candidate-mode live_semantic --reuse-candidate-dir outputs/open_world_closed_loop/frozen_candidate_config_guard_v1
```

### 跑 teaching-utility v0.2

```powershell
$env:OPENAI_API_KEY = "<your key>"
skill-deploy teaching-utility-v02 --repeats 3 --base-url https://api.deepseek.com --model deepseek-v4-flash --query-budget 2
```

## 6. 现在还不能说什么

当前还不能说：

- 任意 open-world 材料上都能稳定自动蒸馏
- evolution 已经在广泛任务上稳定产出更优 Skill
- 已经拿到官方外部 benchmark 成绩
- 系统已经是可直接部署的通用安全产品

最稳妥的定位仍然是：

> 一个带有 bounded open-world distillation 与 bounded evolution evidence 的研究级 Skill Runtime 原型。
