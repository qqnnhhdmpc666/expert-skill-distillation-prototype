# 给老师的阶段进展说明（2026-06-13）

## 一句话概括

我们现在做成的，不是一个单点安全 Skill，而是一个“专家知识蒸馏 + 证据驱动 Skill 进化”的运行时原型系统。

它已经支持：

1. 把材料蒸馏成可安装 Skill。
2. 让 Skill 在统一 runtime 中执行并留下证据。
3. 基于 verifier 反馈生成 candidate Skill。
4. 用统一门控决定 promote / reject / rollback。

## 当前项目定位

最准确的定位是：

> An Evidence-Grounded Skill Evolution Runtime delivered as Codex Skill + CLI.

它不是：

- 生产级漏洞扫描器
- exploit 生成工具
- 完整 SPARK 复现
- 已经拿到官方外部 benchmark 的成熟系统

## 当前最关键的进展

### 1. Runtime 闭环已经成型

系统现在不是单纯生成报告，而是具备真实运行闭环：

- Skill package 生成
- install / active pointer / rollback
- task-conditioned activation
- evidence bundle 落盘
- marginal utility comparison
- candidate generation
- promotion gate / rejection buffer

这意味着“Skill 作为一个可验证、可版本化、可演化对象”已经有工程载体。

### 2. 有界 open-world 自动蒸馏已经拿到支持性证据

我们新增了一条更接近真实研究主张的链路：

- 输入不是仓库内置 expert material，而是公开安全材料
- 当前验证源主要是 OWASP 公开材料
- 系统自动抽取 capability，编译成可安装 Skill
- 再用独立样本验证蒸馏出来的 Skill 是否真的比现有基线更好

当前结果：

- distilled effective pass：`8 / 10`
- baseline effective pass：`5 / 10`
- false positives：`0`
- clean negative controls：`3`
- unsupported limitations retained：`3`

这支持的不是“任意 open-world 都能自动成功”，而是：

> 在有界公开材料场景中，系统已经能把外部材料自动蒸馏为有实际收益的 Skill。

### 3. 有界 stable evolution improvement 已经得到一条真实证据

我们进一步在 open-world 蒸馏得到的 Skill 之上做了窄闭环演化：

- 从真实失败模式出发，而不是手工写一个“故意更好”的版本
- candidate 与 base skill 做直接比较
- 连续 3 次 fresh rerun 都满足严格晋升条件
- 没有 false positive 增加，也没有正例退化

当前结果：

- base score：`0.93`
- candidate score：`0.97`
- score delta：`+0.04`
- promotion count：`3 / 3`

这支持的不是“演化已经普遍稳定”，而是：

> 在当前有界 open-world 闭环上，系统已经出现可重复的、受门控约束的改进证据。

## 现在可以合理声称的内容

当前比较稳妥的说法是：

1. 我们已经完成了一个研究级原型，核心机制链是完整的。
2. secure_code_review 主线已经有 controlled、本地 holdout、mini-suite、non-oracle/local semantic、ablation 等多条证据。
3. 在此基础上，我们又补上了“公开材料自动蒸馏”和“公开材料蒸馏后的一次稳定闭环改进”两条更贴近主命题的证据线。

## 现在还不能声称的内容

当前还不能说：

1. 已经证明任意 open-world 自动蒸馏都成立。
2. 已经证明 evolution 在广泛任务上稳定产出更优 Skill。
3. 已经拿到官方外部安全 benchmark 结论。
4. 已经变成真实世界可直接部署的安全产品。

## 为什么这一步重要

如果只有内部 controlled case，系统更像“工程化 prompt/runtime”。

现在补上的这两条证据线，意义在于：

- 把“蒸馏”从内置材料推进到外部公开材料
- 把“进化”从候选拒绝机制推进到真实改进闭环

也就是说，系统开始更接近它最初的研究命题，而不只是一个工程演示。

## 下一步最值得补的证据

按价值排序，下一步最重要的是：

1. 扩大 open-world/distilled skill 的独立验证覆盖面，但仍保持有界和可审计。
2. 再拿到一条不同 failure family 的稳定改进闭环，而不是只有一条 config 相关闭环。
3. 配置并跑更真实的 live non-oracle / live LLM 复验。
4. 在不越界的前提下，继续补 open-source/release 质量，让别人更容易复现。

## 相关证据文件

建议老师如果只看三个文件，可以先看：

1. `reports/OPEN_WORLD_DISTILLATION_VALIDATION_STATUS.md`
2. `reports/OPEN_WORLD_CLOSED_LOOP_STATUS.md`
3. `docs/CLAIM_BOUNDARY.md`

如果要看项目全貌，再补：

4. `README.md`
5. `docs/USER_MANUAL_ZH.md`
6. `reports/ACADEMIC_CLAIM_READINESS_ASSESSMENT.md`

## 当前结论

当前最稳的总结是：

> 这个项目已经从“内部 controlled runtime 原型”推进到“具备有界 open-world 自动蒸馏证据、并出现有界稳定演化改进证据的研究级原型”。  
> 但它仍然不是外部 benchmark 已充分证明的成熟安全工具，研究结论仍需要继续以保守边界表述。
