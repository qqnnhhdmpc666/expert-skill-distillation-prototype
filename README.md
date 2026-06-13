# Expert Skill Distillation Prototype

一个面向 Agent 的 **Skill 蒸馏与 Skill 进化闭环原型**。

这个项目想解决的，不是“某个 prompt 能不能多过几个 case”，而是更底层的问题：

> 能不能把专家知识变成一个可安装、可执行、可验证、可升级、可回滚的 Skill 对象？

## 我们真正要做什么

这个仓库的核心不是单个安全 Skill，也不是一份任务报告，而是一条闭环：

```text
专家知识 / 用户材料
-> 蒸馏成可安装 Skill
-> 在任务中执行
-> 收集轨迹、证据、verifier 反馈
-> 生成候选修订
-> 通过门控决定晋升 / 拒绝 / 回滚
-> 进入下一轮 Skill 进化
```

所以它本质上是在做两件事：

### 1. 专家知识蒸馏

把专家经验、规则、任务边界、正反例材料，蒸馏成一个真正可运行的 Skill package，而不是一段散乱的提示词。

### 2. 反馈驱动进化

让 Skill 在执行之后，基于 verifier 反馈、失败模式、证据摘要和轨迹，生成候选升级，并用统一证据链决定是否晋升。

## 这个系统已经能做什么

当前仓库已经具备下面这些工程能力：

- 把专家材料蒸馏成可安装 Skill 包
- 用 `SKILL.md + manifest.json` 表达 Skill
- 安装、切换、回滚不同 Skill 版本
- 在不同任务族上做 task-conditioned capability activation
- 运行后自动落盘 evidence bundle
- 比较 `no_skill / v1 / v2 / active_installed` 的边际收益
- 根据 verifier/evidence 生成 candidate Skill
- 用 promotion gate / rejected buffer / rollback 防止“越进化越坏”

换句话说，这里不是只在“写 Skill”，而是在把 **Skill 当成一类可管理、可验证、可演化的运行对象**。

## 当前内置的两个示例方向

### `secure_code_review`

当前最成熟的主线，用来验证：

- upload security
- config security
- API / code review
- auth / access control
- out-of-scope guard

### `software_patch_review`

用于补丁审查与外部软件工程任务衔接的辅助 Skill。

它不是 `secure_code_review` 的替代品，而是给更广的“Skill 可迁移到软件修复任务”这条线打基础。

## 最短路径上手

### 1. 安装项目

```powershell
python -m pip install -e .[dev]
```

### 2. 从专家材料蒸馏一个 Skill

下面这个命令会把内置的四类安全专家材料，蒸馏成一个新的可安装 Skill 包：

```powershell
skill-deploy distill-skill --cases upload,config,api_review,auth --skill-id secure_code_review_distilled --version v1
```

### 3. 安装刚蒸馏出来的 Skill

```powershell
skill-deploy install --skill outputs/distilled_skills/secure_code_review_distilled --version v1
```

### 4. 跑一个真实 runtime case

```powershell
skill-deploy run-skill --installed secure_code_review_distilled --case upload_security_001 --backend offline_deterministic
```

### 5. 对比版本与收益

```powershell
skill-deploy compare-variants --cases upload,config --backend offline_deterministic --source installed --installed-skill secure_code_review
```

## 如果你想直接用仓库自带的标准包

```powershell
skill-deploy build-codex-skill
skill-deploy install --skill outputs/deployable_codex_skill/secure_code_review --version v2
skill-deploy run-skill --installed secure_code_review --case upload_security_001 --backend offline_deterministic
```

这条路径更像“标准示例包”；`distill-skill` 则是“从材料生成 Skill”的主入口。

## 为什么这不只是 prompt engineering

普通 prompt 调整最大的问题，是它通常缺少下面这些东西：

- 明确版本
- 运行态安装与切换
- 统一 evidence
- verifier 反馈闭环
- 候选晋升门控
- 拒绝与回滚机制

这个仓库尝试把这些全都放进同一条链里。我们更关心的是：

> Skill 的新增、修改、拒绝、晋升和回滚，能不能都由同一套证据驱动？

## 适合拿它来做什么

如果你在做下面这些方向，这个仓库会比较对路：

- Agent Skill engineering
- Expert knowledge distillation
- Evidence-grounded runtime
- Skill evolution / repair gating
- Defensive security review
- Software patch review

## 项目边界

当前定位是 **研究级原型**，不是现成的生产安全产品。

它现在强调的是：

- Skill 如何被蒸馏
- Skill 如何被安装和执行
- Skill 如何被验证
- Skill 如何基于反馈演化

它不宣称：

- 通用漏洞扫描器
- exploit 自动生成器
- 真实未授权目标利用工具
- 已经完成官方外部 benchmark 证明的生产系统

## 安全边界

当前安全方向只做防御性工作：

- 检测
- 解释
- 修复建议
- patch / contract validation

不会做：

- exploit 生成
- 攻击链执行
- 未授权目标测试

## 仓库结构

```text
src/skill_deployment/   runtime、runner、verifier、install state、distillation
agents/                 本地 / live agent 包装
scripts/                构建、蒸馏、验证、对比、演化脚本
data/                   controlled task cases 与本地样本
outputs/                Skill 包、运行产物、evidence bundles
reports/                状态报告与验证结果
docs/                   设计、边界、复现、使用说明
review_package/         对外审阅材料
```

## 推荐阅读顺序

如果你第一次看这个仓库，建议从这里开始：

1. `docs/QUICKSTART.md`
2. `docs/ARCHITECTURE_AND_DESIGN.md`
3. `docs/CLAIM_BOUNDARY.md`
4. `reports/REPRESENTATIVE_VALIDATION_MATRIX.md`

## 基础检查

```powershell
python -m pytest -q
python scripts\validate_task_cases.py
skill-deploy validate-review-package
```

## License

MIT
