# Expert Skill Distillation Prototype

一个面向 Agent 的 **Skill 安装、执行、验证、比较、演化** 原型系统。

这个项目想解决的不是“再写一个 prompt”，而是把 Agent Skill 做成一种 **可安装、可回滚、可验证、可演化** 的对象。  
我们希望回答一个更工程化的问题：

> 一个 Skill 被修改之后，究竟是真的变强了，还是只是对某几个 case 过拟合了？

为此，这个仓库实现了一条完整链路：

```text
Skill package -> installed runtime -> task-conditioned activation
-> evidence bundle -> verifier -> variant comparison
-> candidate generation -> rejection / staged promotion / rollback
```

## 它能做什么

目前这个仓库已经可以：

- 把 Skill 打包成可安装目录，包含 `SKILL.md` 和 `manifest.json`
- 用 CLI 安装、切换、回滚不同版本的 Skill
- 在不同任务类型下激活不同能力组，而不是把所有规则一股脑打开
- 运行受控任务并自动写出 evidence bundle
- 比较 `no_skill / v1 / v2 / active_installed` 的边际收益
- 用 verifier 反馈驱动候选 Skill 生成
- 对候选做严格门控：允许拒绝、隔离、暂缓晋升，而不是默认“越改越好”
- 支持多种运行后端，包括：
  - `offline_deterministic`
  - `non_oracle_local_semantic`
  - `live_llm_text`

## 当前重点场景

### 1. `secure_code_review`

这是当前最成熟的一条主线，面向 **防御性安全代码审计 / 修复建议**。

当前已覆盖的代表性任务包括：

- 文件上传安全审计
- 配置安全检查
- API / code review
- 权限与访问控制检查
- out-of-scope 保护与 false positive 控制

### 2. `software_patch_review`

这是辅助主线，用于软件补丁评审和外部软件工程任务衔接。  
它的作用不是替代 `secure_code_review`，而是为后续更广的软件修复任务和外部 harness 对接打基础。

## 为什么这个项目不只是一个 prompt demo

普通 prompt 或经验总结很容易遇到两个问题：

1. 改完以后不知道是不是只对一个 case 有效
2. 越积越多，最后变成难以维护的规则堆

这个仓库尝试把 Skill 变成一个真正可管理的运行单元：

- 有版本
- 有安装态
- 有激活条件
- 有证据记录
- 有 verifier 反馈
- 有对照比较
- 有拒绝与回滚

换句话说，我们更关心的是：

> Skill 的新增、修改、拒绝、晋升和回滚，能不能都由同一套证据链驱动。

## 快速开始

### 安装

```powershell
python -m pip install -e .[dev]
```

### 构建并安装安全审计 Skill

```powershell
skill-deploy build-codex-skill
skill-deploy install --skill outputs/deployable_codex_skill/secure_code_review --version v2
```

### 跑一个最小示例

```powershell
skill-deploy run-skill --installed secure_code_review --case upload_security_001 --backend offline_deterministic
```

### 比较不同版本

```powershell
skill-deploy compare-variants --cases upload,config --backend offline_deterministic --source installed
```

### 检查 review package

```powershell
skill-deploy validate-review-package
```

## Live LLM 用法

如果你想跑 live LLM 路径，可以使用 OpenAI-compatible 接口。  
不要把 API key 写入仓库文件，只在当前进程环境中设置。

```powershell
$env:OPENAI_API_KEY = "<your key>"
skill-deploy live-contract-validation --installed secure_code_review --base-url https://api.deepseek.com --model deepseek-v4-flash
```

## 你可以直接拿它来做什么

这个仓库现在适合拿来做几类事情：

- 验证一个安全审计 Skill 在多个任务上的表现
- 研究 task-conditioned capability activation 是否真的减少误触发
- 比较不同 Skill 版本是否带来真实净收益
- 研究 verifier 驱动的 Skill 演化机制
- 构建一套可审计、可回放、可导出的 Agent Skill 实验流程

如果你在做下面这些方向，这个仓库会比较对路：

- Agent Skill engineering
- Skill distillation
- Evidence-grounded agent runtime
- Defensive security review
- Verifier-guided candidate evolution

## 当前仓库状态

这个项目已经是 **可运行的研究原型**，不是纯设计稿。

当前最稳定的能力包括：

- installed Skill runtime
- 任务条件化能力激活
- 本地受控安全审计验证
- live contract 路径
- 候选 Skill 的严格比较与门控
- review package 导出与校验

当前还没有做成或不应过度宣称的部分包括：

- 生产级漏洞扫描器
- exploit 自动化
- 官方外部 benchmark 成绩
- 已经证明“自进化一定稳定变强”

所以更准确的定位是：

> 这是一个面向 Agent Skill 的研究级 runtime prototype，强调安装、执行、证据采集、版本比较、候选生成与门控，而不是一个现成的生产安全产品。

## 仓库结构

```text
src/skill_deployment/   核心 runtime、runner、verifier、install state、normalizer
agents/                 本地 / live agent 包装器
scripts/                验证、构建、比较、导出脚本
data/                   受控 task cases 和本地代表性样本
outputs/                运行产物、evidence bundles、验证输出
reports/                状态报告、分析报告、成熟度总结
docs/                   用户文档、结构说明、边界说明、复现说明
review_package/         审阅与归档材料
skill_packages/         示例与历史 Skill 包
```

## 建议阅读顺序

如果你是第一次进入这个仓库，建议按下面顺序看：

1. `docs/USER_GUIDE.md`
2. `docs/ARCHITECTURE_AND_DESIGN.md`
3. `docs/QUICKSTART.md`
4. `docs/CLAIM_BOUNDARY.md`
5. `reports/REPRESENTATIVE_VALIDATION_MATRIX.md`

如果你是从新设备、新会话或新的 Codex 线程接手，先看：

```text
docs/CODEX_CONTEXT_HANDOFF.md
```

## 最小健康检查

当前最基本的本地验证命令：

```powershell
python -m pytest -q
python scripts\validate_task_cases.py
skill-deploy validate-review-package
```

## 安全边界

当前安全方向只做 **防御性工作**：

- 检测
- 解释
- 修复建议
- patch / contract validation

不做：

- exploit 生成
- 攻击链执行
- 未授权目标利用

## 相关文档

- `README_PROTOTYPE.md`
- `PROJECT_OVERVIEW_FOR_GITHUB.md`
- `docs/QUICKSTART.md`
- `docs/TROUBLESHOOTING.md`
- `docs/ARTIFACT_TYPES.md`
- `docs/CLAIM_BOUNDARY.md`

## License

MIT

