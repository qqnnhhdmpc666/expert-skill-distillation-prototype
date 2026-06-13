# 给老师的阶段进展说明（2026-06-13）

## 一句话概括

目前项目已经不是“一个安全审计 prompt”，而是一个围绕 **专家知识蒸馏 + 证据驱动 Skill 进化** 的研究级运行时原型。

它的核心闭环现在已经具备可执行工程载体：

```text
专家/用户/公开材料
-> 自动蒸馏成 Skill package
-> install 到 runtime
-> 在任务中执行并留下 evidence
-> verifier 给出 pass/fail/误报/缺失反馈
-> 生成 candidate Skill
-> promotion / rejection / rollback gate
```

## 当前项目定位

当前最准确的定位是：

> An Evidence-Grounded Skill Evolution Runtime delivered as Codex Skill + CLI.

它不是：

- 生产级漏洞扫描器
- exploit 生成工具
- 完整 SPARK 复现
- 已经拿到官方外部 benchmark 结论的成熟系统

## 当前已经拿到的三条主要证据线

### 1. Runtime 主闭环已经成型

这条线现在已经有真实代码入口和 artifact：

- Skill package 构建、安装、运行、版本切换
- evidence bundle 与 marginal utility 比较
- candidate generation 与 rejection buffer
- staged promotion / rollback gate
- task-conditioned activation

这说明“Skill 作为一个被安装、执行、比较、修订、门控的运行对象”已经成立。

### 2. 有界 open-world 自动蒸馏与有界稳定改进已经得到支持

我们已经补上了两条更贴主命题的证据：

#### A. 有界 open-world 自动蒸馏

- 输入：公开安全材料（当前主要用 OWASP）
- 输出：可安装的 `secure_code_review_open_world_distilled`
- 当前结果：
  - distilled effective pass：`8 / 10`
  - baseline effective pass：`5 / 10`
  - false positives：`0`
  - clean negative controls：`3`
  - unsupported limitations retained：`3`

这支持的是：

> 在有界公开材料场景中，系统已经能把外部材料自动蒸馏成有实际收益的 Skill。

#### B. 有界稳定改进

在 open-world distilled skill 之上，我们又跑通了一条窄闭环改进链：

- 从真实失败模式出发生成 candidate
- candidate 与 base skill 直接比较
- 连续 fresh rerun 满足严格 gate

已存在的有界结果表明：

> 至少在当前一条窄闭环上，系统已经出现了可重复的改进证据。

### 3. v0.2 teaching-utility pilot 已经跑通，而且保留了负结果

这是当前最值得看的新增结果，因为它更直接对应研究问题本身：

> 一条轨迹对当前任务有用，不等于它对“教会下一个 Skill”有用。

我们新加了一个 live pilot：

- 2 个 domain：`api_review`、`config_security`
- 8 个本地任务
- 1 个真实 live tool-agent
- 5 种轨迹选择策略：
  - `random`
  - `top_reward_success_only`
  - `success_failure_contrast`
  - `diversity`
  - `active_discriminative_evidence`
- 3 次 repeat
- 物理拆分：
  - `source_generation`
  - `active_query_pool`
  - `promotion_validation`
  - `sealed_hidden_test`

当前 fresh 结果：

| Method | Mean query score | Mean hidden delta |
|---|---:|---:|
| random | 0.3889 | 0.1722 |
| top_reward_success_only | 0.3167 | 0.2222 |
| success_failure_contrast | 0.8222 | 0.0333 |
| diversity | 0.6500 | 0.2000 |
| active_discriminative_evidence | 0.8222 | 0.0000 |

当前结论：

- `active_selection_hypothesis = hypothesis_not_supported`
- `best_method_by_hidden_delta = top_reward_success_only`

这条结果的意义非常大，因为它不是“漂亮成功”，而是一个可信的研究判断：

> 当前我们写的 active discriminative 选择器，还没有在 teaching utility 上赢过更朴素的选择策略。  
> 也就是说，轨迹选择确实是研究问题，但当前 active 设计还不够好。

## 现在可以合理声称的内容

当前比较稳妥的说法是：

1. 项目已经形成一个研究级原型，核心机制链完整。
2. “材料蒸馏 -> 安装运行 -> evidence/verifier -> candidate/gate” 这条主链已成立。
3. 有界 open-world 自动蒸馏已经拿到支持性证据。
4. 有界稳定改进已经拿到支持性证据。
5. 更强的 teaching-utility v0.2 pilot 已经跑通，但当前 active 轨迹选择策略没有被证明优于朴素基线。

## 当前还不能声称的内容

当前还不能说：

1. 任意 open-world 自动蒸馏都已经成立。
2. evolution 已经在广泛任务上稳定产出更优 Skill。
3. active evidence selection 已经被证明是最优 teaching-utility 策略。
4. 已经拿到官方外部安全 benchmark 结论。
5. 系统已经是可直接部署的真实安全产品。

## 下一步建议

当前最有价值的下一步不是继续堆 case，而是：

1. 重新设计 active evidence selection，使它更贴 teaching utility，而不是只看表面分歧。
2. 在更真实但仍可控的任务池里复验 v0.2 结果，看 `top_reward/diversity` 是否稳定领先。
3. 把“公开材料蒸馏”与“trajectory teaching utility”两条线合并，验证公开材料 + 轨迹选择是否比任一单线更强。
4. 在不越界的前提下，逐步补更强 external evidence，但继续保留失败和 blocked。

## 建议优先看的文件

如果老师只想快速把握现在的阶段，建议先看这 4 个文件：

1. `README.md`
2. `reports/OPEN_WORLD_DISTILLATION_VALIDATION_STATUS.md`
3. `reports/OPEN_WORLD_CLOSED_LOOP_STATUS.md`
4. `reports/TEACHING_UTILITY_V02_STATUS.md`

如果要看边界，再补：

5. `docs/CLAIM_BOUNDARY.md`
