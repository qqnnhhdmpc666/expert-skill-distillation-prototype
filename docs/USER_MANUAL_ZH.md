# 用户说明书（中文）

这份说明书不是内部审计报告，而是给第一次接触这个仓库的人看的。

如果你只想知道三件事，请先记住：

1. 这个系统的核心是“把材料蒸馏成 Skill，再让 Skill 在证据约束下进化”。
2. 你不需要理解仓库里所有目录，先会用几个命令就够了。
3. 当前最可信的是“有界场景下的可执行闭环”，不是“已经变成通用安全产品”。

## 1. 它到底是什么

你可以把它理解成一个 Skill Runtime：

- 输入可以是专家知识、用户规则、公开安全材料
- 系统把这些材料蒸馏成一个可安装 Skill
- Skill 安装后可以被 runtime 调用
- 运行过程中会留下 evidence bundle
- verifier 用统一规则判断是否 pass、是否误报、是否越界
- 系统再基于这些反馈生成 candidate Skill，并决定 promote / reject / rollback

所以这个项目研究的是：

> Skill 能不能像一个被版本化、被验证、被门控的运行对象那样持续进化。

## 2. 你最常用的三条路径

### 路径 A：直接跑仓库自带的 secure_code_review

适合你想先看系统怎么工作的情况。

```powershell
python -m pip install -e .[dev]
skill-deploy build-codex-skill
skill-deploy install --skill outputs/deployable_codex_skill/secure_code_review --version v2
skill-deploy run-skill --installed secure_code_review --case upload_security_001 --backend offline_deterministic
```

这条路径会直接验证：

- install state 是否生效
- run-skill 是否真的读取 installed package
- evidence bundle 是否落盘

### 路径 B：从你自己的材料蒸馏一个 Skill

适合你已经有规则文档、经验总结、内部审查规范、公开指南等材料。

示例材料文件：

- `demo/open_materials_example.json`

命令：

```powershell
skill-deploy distill-open-materials --materials demo/open_materials_example.json --skill-id my_distilled_skill --version v1
skill-deploy install --skill outputs/distilled_open_materials/my_distilled_skill --version v1
skill-deploy run-skill --installed my_distilled_skill --case upload_security_001 --backend offline_deterministic
```

材料文件最小格式：

```json
{
  "materials": [
    {
      "source_id": "upload_guidance_demo",
      "task_family": "upload_security",
      "title": "Upload review guidance",
      "material_text": "..."
    }
  ]
}
```

每条材料至少需要：

- `source_id`
- `task_family`
- `title`
- 以下三者之一：
  - `material_text`
  - `source_path`
  - `source_url`

### 路径 C：看 Skill 是否真的比旧版本更好

```powershell
skill-deploy compare-variants --cases upload,config --backend offline_deterministic --source installed --installed-skill secure_code_review
```

你会得到：

- `no_skill`
- `skill_v1`
- `skill_v2`
- `active_installed`

之间的对比结果，以及对应 hash、pointer snapshot、metadata。

## 3. 如果你想看“自动蒸馏 + 自动改进”这一整条链

### 第一步：跑公开材料蒸馏验证

```powershell
$env:OPENAI_API_KEY = "<your key>"
skill-deploy open-world-distill-validation --backend live_llm_text --base-url https://api.deepseek.com --model deepseek-v4-flash
```

这一步会：

- 下载有限的公开安全材料
- 自动蒸馏出 `secure_code_review_open_world_distilled`
- 安装并验证它
- 与 baseline skill 对比

看结果优先看：

- `reports/OPEN_WORLD_DISTILLATION_VALIDATION_STATUS.md`
- `outputs/open_world_distillation_validation/open_world_distillation_validation_summary.json`

### 第二步：跑 open-world 闭环改进

```powershell
$env:OPENAI_API_KEY = "<your key>"
skill-deploy open-world-closed-loop --installed secure_code_review_open_world_distilled --repeats 3 --base-url https://api.deepseek.com --model deepseek-v4-flash
```

这一步会：

- 读取上一轮真实失败模式
- 生成窄 candidate Skill
- 连续重复比较 candidate 与 base skill
- 判断是否满足 staged promotion proposal

结果优先看：

- `reports/OPEN_WORLD_CLOSED_LOOP_STATUS.md`
- `outputs/open_world_closed_loop/open_world_closed_loop_summary.json`

### 第三步：看“哪些轨迹真的值得教给 Skill”

这是当前仓库最新的一条研究线，不是为了多跑几个 case，而是为了回答：

> 一条轨迹能帮当前任务过关，是否也真的能帮助蒸馏出更好的下一个 Skill？

命令：

```powershell
$env:OPENAI_API_KEY = "<your key>"
skill-deploy teaching-utility-v02 --repeats 3 --base-url https://api.deepseek.com --model deepseek-v4-flash
```

它会做什么：

- 用 live tool-agent 跑 2 个 domain 的任务
- 把任务分成 `source_generation / active_query_pool / promotion_validation / sealed_hidden_test`
- 比较 `random / success-only / contrast / diversity / active discriminative` 这 5 种轨迹选择方法
- 分开记录 `task utility` 和 `teaching utility`

优先看：

- `reports/TEACHING_UTILITY_V02_STATUS.md`
- `outputs/teaching_utility_v02/teaching_utility_v02_summary.json`

这条线当前最重要的意义，不是“证明 active 一定最好”，而是：

- 如果 active 没赢，也必须保留这个负结果
- 这样我们才真的知道，Skill distillation 更像主动实验设计，还是更像高分轨迹收集

## 4. 你不需要关心的目录

第一次使用时，不必完整理解这些目录：

- `runs/`
- `revision/`
- `uploaded_snapshots/`
- `external_repos/`

除非你正在复现实验细节，否则它们可以先不看。

## 5. 你真正需要记住的目录

### 核心代码

- `src/skill_deployment/`
- `agents/`
- `scripts/`

### 核心输入

- `data/`
- `demo/`

### 核心输出

- `outputs/distilled_open_materials/`
- `outputs/installed_skills/`
- `outputs/runtime_runs/`
- `outputs/open_world_distillation_validation/`
- `outputs/open_world_closed_loop/`

### 核心结论

- `reports/`
- `docs/CLAIM_BOUNDARY.md`

## 6. evidence 怎么看

这个仓库里最重要的不是“有没有生成一份报告”，而是证据类型。

我们统一用这些标签：

- `fresh_run`：真实新运行证据，最强
- `derived_summary`：从已有结果汇总而来
- `scaffold`：只是结构或占位，不是结果
- `infra_blocked`：基础设施阻塞，不是失败也不是成功
- `replay`：复用旧运行，不是 fresh
- `external_official_harness`：官方 harness 输出

如果看到一个结论没有 fresh evidence 支撑，应该天然保守一点。

## 7. 当前能合理声称什么

当前最安全的说法是：

- 这是一个研究级的 Evidence-Grounded Skill Evolution Runtime 原型
- 它支持从材料蒸馏 Skill、安装 Skill、运行 Skill、比较版本、生成候选修订、门控晋升/拒绝/回滚
- 在有界公开材料验证中，它已经支持 open-world 自动蒸馏
- 在有界 open-world 闭环中，它已经支持稳定产出更优 candidate Skill

当前**不能**说：

- 生产级漏洞扫描器
- 通用 exploit 工具
- 任意公开材料上都稳定成功
- 官方外部 benchmark 已经通过

## 8. 给第一次接手这个仓库的人

如果你要在 30 分钟内接上项目，建议只看这几个文件：

1. `README.md`
2. `docs/USER_MANUAL_ZH.md`
3. `docs/CLAIM_BOUNDARY.md`
4. `reports/OPEN_WORLD_DISTILLATION_VALIDATION_STATUS.md`
5. `reports/OPEN_WORLD_CLOSED_LOOP_STATUS.md`
6. `reports/TEACHER_PROGRESS_BRIEF_20260613.md`

## 9. 最后做一次基本检查

```powershell
python -m pytest -q
python scripts\validate_task_cases.py
skill-deploy validate-review-package
```

如果这三条不过，不要急着相信更大的结论。
