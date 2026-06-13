# 用户说明书（中文）

这份文档给第一次真正使用仓库的人，不是内部审计报告。

如果你只记三句话：

1. 这个系统研究的是“材料蒸馏成 Skill，再让 Skill 在证据约束下进化”。
2. 你不需要先理解所有目录，先会跑几条主命令就够了。
3. 当前最可信的是 **bounded、可审计、可重复** 的闭环证据，不是“已经变成通用安全产品”。

## 1. 它到底是什么

你可以把它理解成一个 **Skill Runtime + Distillation + Evolution** 系统：

- 输入可以是专家知识、用户规则、公开安全材料
- 系统把这些材料蒸馏成可安装 Skill
- Skill 安装后进入 runtime，被真实任务调用
- 执行会留下 evidence bundle
- verifier 判断 pass / fail / missing capability / false positive / scope violation
- 系统再基于这些反馈生成 candidate Skill，并决定 promote / reject / rollback

它关心的不是单次 prompt 调参，而是：

> Skill 能不能像一个被安装、执行、验证、修订、门控的运行对象那样持续进化。

## 2. 最常用的 4 条路径

### 路径 A：直接跑内置 secure_code_review

```powershell
python -m pip install -e .[dev]
skill-deploy build-codex-skill
skill-deploy install --skill outputs/deployable_codex_skill/secure_code_review --version v2
skill-deploy run-skill --installed secure_code_review --case upload_security_001 --backend offline_deterministic
```

这条路径会直接验证：

- install state 是否真实生效
- run-skill 是否真的读取 installed package
- evidence bundle 是否落盘

### 路径 B：从你自己的材料蒸馏一个 Skill

仓库自带了一个最小示例：

- `demo/open_materials_example.json`

命令：

```powershell
skill-deploy distill-open-materials --materials demo/open_materials_example.json --skill-id my_distilled_skill --version v1 --projection-mode hybrid_semantic --base-url https://api.deepseek.com --model deepseek-v4-flash
skill-deploy install --skill outputs/distilled_open_materials/my_distilled_skill --version v1
skill-deploy run-skill --installed my_distilled_skill --case upload_security_001 --backend offline_deterministic
```

最小材料格式：

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

### 路径 C：比较 Skill 是否真的带来净收益

```powershell
skill-deploy compare-variants --cases upload,config --backend offline_deterministic --source installed --installed-skill secure_code_review
```

你会拿到：

- `no_skill`
- `skill_v1`
- `skill_v2`
- `active_installed`

之间的对比，以及对应 hash、pointer snapshot、run metadata。

### 路径 D：跑公开材料蒸馏 + 闭环改进

```powershell
$env:OPENAI_API_KEY = "<your key>"
skill-deploy open-world-distill-validation --skill-id secure_code_review_open_world_hybrid_distilled --version v1 --backend live_llm_text --base-url https://api.deepseek.com --model deepseek-v4-flash --projection-mode hybrid_semantic
skill-deploy open-world-closed-loop --installed secure_code_review_open_world_hybrid_distilled --repeats 3 --base-url https://api.deepseek.com --model deepseek-v4-flash --candidate-mode live_semantic
```

这条路径最贴近仓库主命题：

- 公开材料自动蒸馏
- install 到 runtime
- 用真实失败反馈生成 candidate
- 严格 gate 决定是否 staged promotion proposal

## 3. projection-mode 和 candidate-mode 怎么选

### `distill-open-materials --projection-mode`

- `keyword`
  - 最稳定
  - 主要做 registry keyword projection
  - 更像受控 baseline

- `live_semantic`
  - 纯语义蒸馏
  - 更接近真正 open-world 自动蒸馏
  - 但当前仍可能出现 abstain 或弱稳定性

- `hybrid_semantic`
  - 先语义选择
  - 如果某条材料上模型明确 abstain，再记录 fallback 到 keyword projection
  - 当前最适合做 bounded open-world 自动蒸馏验证

### `open-world-closed-loop --candidate-mode`

- `template`
  - 规则化 candidate
  - 更像原始窄闭环 baseline

- `live_semantic`
  - 用真实 failure feedback 生成结构化 capability edit
  - 当前是更接近“真实 evolution”的模式

## 4. 当前最值得看的三条结果

### A. bounded open-world 自动蒸馏

当前 fresh hybrid-semantic 结果：

- effective pass：`8 / 10`
- baseline：`7 / 10`
- false positives：`0`
- clean negatives：`3`
- unsupported limitations preserved：`3`

看：

- `reports/OPEN_WORLD_DISTILLATION_VALIDATION_STATUS.md`
- `outputs/open_world_distillation_validation/open_world_distillation_validation_summary.json`

### B. bounded stable evolution improvement

当前 fresh result：

- candidate mode：`live_semantic`
- repeats：`3`
- promotion count：`3 / 3`
- score delta：稳定 `+0.04`
- false-positive delta：`0`
- positive regressions：`0`

看：

- `reports/OPEN_WORLD_CLOSED_LOOP_STATUS.md`
- `outputs/open_world_closed_loop/open_world_closed_loop_summary.json`

### C. teaching-utility v0.2

这条线当前最重要的意义，是**保留负结果**：

- active discriminative 轨迹选择目前还没有赢过更朴素基线
- 所以当前 active hypothesis 不能声称成立

看：

- `reports/TEACHING_UTILITY_V02_STATUS.md`
- `outputs/teaching_utility_v02/teaching_utility_v02_summary.json`

## 5. evidence 怎么读

不要只看“有没有报告”，要看 evidence type。

当前仓库里最重要的标签：

- `fresh_run`：真实新运行证据，最强
- `derived_summary`：已有结果汇总
- `scaffold`：结构或占位，不算完成
- `infra_blocked`：基础设施阻塞，不是成功也不是模型失败
- `replay`：复用旧运行
- `external_official_harness`：官方 harness 输出

如果一个结论没有 fresh evidence 支撑，就要天然保守一点。

## 6. 你真正需要记住的目录

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
- `outputs/teaching_utility_v02/`

### 核心结论

- `reports/`
- `docs/CLAIM_BOUNDARY.md`

## 7. 现在能合理声称什么

当前最安全的说法是：

- 这是一个研究级的 Evidence-Grounded Skill Evolution Runtime 原型
- 它支持从材料蒸馏 Skill、安装 Skill、运行 Skill、比较版本、生成候选修订、门控晋升/拒绝/回滚
- 在 bounded 公开材料验证中，`hybrid_semantic` 模式已经支持 open-world 自动蒸馏
- 在 bounded open-world 闭环中，`live_semantic` 结构化 candidate 已经支持稳定产出更优 Skill

当前**不能**说：

- 生产级漏洞扫描器
- 通用 exploit 工具
- 任意公开材料上都稳定成功
- evolution 已经在广泛任务上稳定产出更优 Skill
- 官方外部 benchmark 已经通过

## 8. 第一次接手仓库时建议这样看

1. `README.md`
2. `docs/USER_MANUAL_ZH.md`
3. `docs/CLAIM_BOUNDARY.md`
4. `reports/OPEN_WORLD_DISTILLATION_VALIDATION_STATUS.md`
5. `reports/OPEN_WORLD_CLOSED_LOOP_STATUS.md`
6. `reports/TEACHING_UTILITY_V02_STATUS.md`
7. `reports/TEACHER_PROGRESS_BRIEF_20260613.md`

## 9. 最后做一次基础校验

```powershell
python -m pytest -q
python scripts\validate_task_cases.py
skill-deploy validate-review-package
```

如果这三条不过，不要急着相信更大的结论。
