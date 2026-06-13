# 项目说明书（给第一次打开仓库的人）

如果你刚进这个仓库，不需要先理解所有目录。先记住一句话：

> 这个项目做的是“把材料蒸馏成 Skill，再让 Skill 在证据约束下进化”。

## 1. 先看什么

建议按这个顺序看：

1. `README.md`
2. `docs/USER_MANUAL_ZH.md`
3. `docs/CLAIM_BOUNDARY.md`
4. `reports/OPEN_WORLD_DISTILLATION_VALIDATION_STATUS.md`
5. `reports/OPEN_WORLD_CLOSED_LOOP_STATUS.md`
6. `reports/TEACHING_UTILITY_V02_STATUS.md`
7. `reports/TEACHER_PROGRESS_BRIEF_20260613.md`

## 2. 这个仓库最重要的目录

```text
src/skill_deployment/   核心 runtime、install state、distillation、verifier、CLI
agents/                 本地或 live agent 执行器
scripts/                实验、验证、构建、导出脚本
data/                   task cases、专家材料、公开材料示例
outputs/                fresh 运行产物、distilled skills、evidence、pilot 结果
reports/                阶段性报告、claim 校准、实验结论
docs/                   用户说明、边界说明、复现和对外说明
review_package/         对外评审或打包导出的材料
```

## 3. 如果你只想先跑一次

### 跑内置 Skill

```powershell
python -m pip install -e .[dev]
skill-deploy build-codex-skill
skill-deploy install --skill outputs/deployable_codex_skill/secure_code_review --version v2
skill-deploy run-skill --installed secure_code_review --case upload_security_001 --backend offline_deterministic
```

### 跑公开材料蒸馏验证

```powershell
$env:OPENAI_API_KEY = "<your key>"
skill-deploy open-world-distill-validation --backend live_llm_text --base-url https://api.deepseek.com --model deepseek-v4-flash
```

### 跑 teaching-utility v0.2 pilot

```powershell
$env:OPENAI_API_KEY = "<your key>"
skill-deploy teaching-utility-v02 --repeats 3 --base-url https://api.deepseek.com --model deepseek-v4-flash
```

## 4. 当前最重要的结论

当前项目已经支持：

- 把专家/用户/公开材料自动蒸馏成 Skill
- 把 Skill 安装到 runtime 中执行
- 留下 evidence bundle
- 基于 verifier 反馈生成 candidate Skill
- 用 gate 决定 promote / reject / rollback

同时，最新的 v0.2 pilot 也明确说明了一件重要的事：

> “对当前任务有用的轨迹”不一定“最适合教出下一个 Skill”。

而且当前 active 轨迹选择策略还没有赢过更朴素的基线。这不是坏事，反而是仓库现在最真实、最值得继续做的研究问题。
