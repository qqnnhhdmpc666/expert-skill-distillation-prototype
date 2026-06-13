# Expert Skill Distillation Prototype

这是一个面向研究验证的 **证据驱动 Skill Evolution Runtime 原型系统**。

它的目标不是做一个“什么都能干”的 Agent，也不是直接做成生产级漏洞扫描器，而是把下面这条链条真正跑通并留下可检查证据：

```text
Skill 安装 -> 任务执行 -> 证据采集 -> Verifier 判定 -> 版本比较 -> 候选生成 -> 拒绝 / 晋升 / 回滚
```

当前仓库的第一条主线是 `secure_code_review`，也就是防御性的安全代码审计 / 修复建议 Skill；第二条辅助主线是 `software_patch_review`，用于软件补丁评审和外部软件工程场景衔接。

## 这个项目现在能做什么

目前原型已经支持：

- 把 Skill 打包成可安装目录，包含 `SKILL.md` 和 `manifest.json`
- 用 `skill-deploy` CLI 安装、运行、比较、回滚 Skill
- 根据任务类型做 **task-conditioned capability activation**
- 为每次运行写出统一的 `evidence_bundle`
- 对 `no_skill / v1 / v2 / active_installed` 做边际效用比较
- 用 verifier 反馈驱动候选 Skill 生成，并执行严格的拒绝 / 晋升门控
- 支持本地 deterministic、non-oracle local semantic、live LLM 等多条后端路径
- 输出较完整的报告、审计材料和 review package

一句话说，这个仓库现在更像一个“**可验证的 Skill 运行与演化实验平台**”，而不是一份单纯的 prompt 集合。

## 当前效果

按仓库中最新的状态文档，当前最稳妥的结论是：

- `controlled_internal`: `pass`
- `security_depth`: `pass_local_bounded`
- `live_contract_effectiveness`: `pass`
- `external_generalization`: `partial`
- `mechanism_ablation`: `supports_mechanism`
- `evolution_improvement`: `demonstrated as staged promotion proposal`
- `external_harness`: `infra_blocked`
- `public_release_readiness`: `pass`
- `academic_claim_readiness`: `strong_candidate_with_external_gap`

更直白一点解释：

- 本地受控运行链已经打通，而且不是“只会跑一个 case”。
- `secure_code_review` 在本地有比较强的 **bounded security evidence**，但这还不是官方外部 benchmark 结论。
- live contract 路径已经能工作，说明我们不只是靠 deterministic 假跑。
- 外部 / 半外部泛化已经有一部分证据，但还没有到“广泛真实世界有效”这个级别。
- 候选改进已经能产生 **staged promotion proposal**，但不是自动上线，也不是无限自进化。
- SWE-bench 官方 harness 这条线目前还是 `infra_blocked`，不能拿它假装成外部成功。

## 这不是什麽

为了避免误解，这里明确说清楚：

- 它不是生产级漏洞扫描器
- 它不是 exploit 自动化工具
- 它不是完整的 SPARK 复现
- 它不是官方 CyberSecEval / AutoPatchBench / CVE-Bench 结果
- 它不是已经证明“Skill 会自动越进化越强”的系统

## 快速开始

### 1. 安装

```powershell
python -m pip install -e .[dev]
```

### 2. 构建并安装安全审计 Skill

```powershell
skill-deploy build-codex-skill
skill-deploy install --skill outputs/deployable_codex_skill/secure_code_review --version v2
```

### 3. 跑一个最小示例

```powershell
skill-deploy run-skill --installed secure_code_review --case upload_security_001 --backend offline_deterministic
```

### 4. 比较不同版本 / 变体

```powershell
skill-deploy compare-variants --cases upload,config --backend offline_deterministic --source installed
```

### 5. 检查 review package

```powershell
skill-deploy validate-review-package
```

## 如果你要跑 live LLM

当前仓库支持 OpenAI-compatible 接口。不要把 API key 写进仓库文件，只在当前进程环境里设置。

示例：

```powershell
$env:OPENAI_API_KEY = "<your key>"
skill-deploy live-contract-validation --installed secure_code_review --base-url https://api.deepseek.com --model deepseek-v4-flash
```

## 当前仓库里的“代表性验证”包括什么

当前比较值得看的几条验证线：

1. **Installed Skill Runtime**
   - Skill 可以被安装、运行、比较、回滚

2. **Local Defensive Security Validation**
   - upload / config / auth / API 等安全类 case
   - negative control
   - out-of-scope guard

3. **Live Contract Validation**
   - live LLM 输出经过 contract-safe normalization
   - verifier 不会因为“看起来像对”就直接放过

4. **Mechanism Ablation**
   - 验证 task router / out_of_scope_guard / normalizer 这些机制不是摆设

5. **Candidate Evolution**
   - 候选 Skill 会被比较、拒绝、保留
   - 当前最强结论是：已经出现 staged promotion proposal，但并非自动晋升

## 你第一次进入这个仓库，建议按这个顺序看

1. `docs/CODEX_CONTEXT_HANDOFF.md`
2. `docs/USER_GUIDE.md`
3. `docs/ARCHITECTURE_AND_DESIGN.md`
4. `docs/QUICKSTART.md`
5. `reports/REPRESENTATIVE_VALIDATION_MATRIX.md`
6. `reports/GRAND_AUTONOMOUS_SPRINT_STATUS.md`
7. `reports/ITERATIVE_CONTRACT_IMPROVEMENT_STATUS.md`

## 目录结构

```text
src/skill_deployment/   核心 runtime、runner、verifier、install state、normalizer
agents/                 本地 / live agent 包装器
scripts/                运行验证、生成报告、构建技能包的脚本
data/                   受控 task cases 和本地代表性样本
outputs/                所有运行产物、evidence bundles、validation outputs
reports/                人类可读的状态报告、审计报告、成熟度总结
docs/                   使用说明、结构说明、边界说明、复现实验说明
review_package/         用于审阅和归档的证据打包结果
skill_packages/         历史 / 示例 Skill 包
```

## 目前仓库级别的最小健康状态

当前本地最小验证命令是：

```powershell
python -m pytest -q
python scripts\validate_task_cases.py
skill-deploy validate-review-package
```

最近一次我在本地跑到的结果是：

- `46 passed`
- `case_count=8`
- `validate-review-package: 0 errors`

## 适合谁看

这个仓库比较适合下面几类人：

- 想研究 Agent Skill 如何被“证据化、版本化、可回滚化”的人
- 想看一个较完整的 Skill runtime 原型而不是单个 prompt demo 的人
- 想做安全审计 Skill、任务条件路由、候选晋升门控的人
- 想把“经验总结”从玄学 prompt 调整变成可验证工程流程的人

## 边界提醒

请不要用这个仓库当前结果直接宣称：

- 广泛真实世界安全有效
- 官方 benchmark 已通过
- 已经证明自进化稳定优于人工设计
- 已经达到生产部署标准

更稳妥的说法是：

> 这是一个研究级、可运行、可安装、可验证、可审计的 Skill Evolution Runtime 原型；它已经在本地受控条件下形成了较强证据，但外部官方 benchmark 和更强真实世界泛化仍需继续补证。

## 补充文档

- `README_PROTOTYPE.md`：简洁版原型定位
- `PROJECT_OVERVIEW_FOR_GITHUB.md`：GitHub 面向外部读者的项目概览
- `docs/CLAIM_BOUNDARY.md`：哪些能说，哪些不能说
- `docs/ARTIFACT_TYPES.md`：不同证据类型怎么区分
- `docs/TROUBLESHOOTING.md`：常见问题

