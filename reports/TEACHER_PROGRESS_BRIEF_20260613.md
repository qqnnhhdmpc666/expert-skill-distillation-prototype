# 给老师的阶段进展说明（2026-06-13）

## 一句话概括

项目现在已经不是“一个安全审计 prompt”，而是一个围绕 **材料蒸馏 + 证据驱动 Skill 进化** 的研究级运行时原型。

它当前最值得关注的，不是某个单点 case，而是下面这条完整主链已经基本成立：

```text
材料
-> 蒸馏为 Skill package
-> install 到 runtime
-> 在任务中执行
-> 留下 evidence bundle
-> verifier 给出反馈
-> 生成 candidate Skill
-> promote / reject / rollback gate
```

## 当前项目定位

当前最准确的定位是：

> An Evidence-Grounded Skill Evolution Runtime delivered as Codex Skill + CLI.

它不是：

- 生产级漏洞扫描器
- exploit 生成或攻击链执行工具
- 官方外部 benchmark 已完成的成熟系统
- 已经证明广泛 open-world 自主进化的通用 Agent

## 目前已经拿到的关键证据

### 1. Runtime 主闭环已经成型

当前仓库已经具备真实 install state、runtime 调用、evidence bundle、verifier feedback、candidate proposal、promotion / rejection / rollback 的代码入口和产物。

这意味着 Skill 在这里不再只是静态 prompt，而是一个可以被安装、执行、比较、修订和门控的运行对象。

### 2. bounded open-world 自动蒸馏已经有支持性证据

这一轮把公开材料蒸馏推进到了 `hybrid_semantic` 路径：

- 先做 LLM capability 语义选择
- 对保守 abstain 的材料显式 fallback 到 keyword projection
- 所有 fallback 都写 provenance

当前最稳的说法不是“已经普遍优于基线”，而是：

- 更早一次 fresh run：distilled `8 / 10`，baseline `7 / 10`
- 最新 fresh rerun：distilled `8 / 10`，baseline `8 / 10`

这支持的是：

> 在当前有界公开材料场景里，系统已经能自动蒸馏出至少达到当前安装版基线水平、并曾在 fresh run 中严格超过基线的 Skill。

### 3. bounded evolution improvement 已经拿到更真实的证据

这条线现在不再只是“模板追加段落”，而是：

- 从 open-world failure feedback、verifier feedback、evidence summary、distilled Skill text 中生成 candidate
- 直接改写 capability section 本体
- 用严格 gate 判断 candidate 是否能晋升

当前两层最关键的结果：

#### generated-candidate fresh run

- `3 / 3` strict promotion proposals

#### frozen-candidate repeatability run

- `4 / 5` strict promotion proposals
- `base_mean_score = 0.9167`
- `candidate_mean_score = 0.95`
- `mean_score_delta = +0.0333`
- `false_positive_delta = 0`

这说明：

> 在当前 bounded open-world 线上，系统已经不只是“偶尔改对一次”，而是拿到了冻结 candidate 后仍有正均值收益、且大多数 repeats 严格胜出的重复验证证据。

同时也需要保留边界：

- 这还不是“每一轮都严格更优”
- 仍然不能宣称 broad stable autonomous evolution

### 4. teaching-utility v0.2 保留了真实负结果

当前更严格的 matched-budget live pilot 里：

- `active_discriminative_evidence` 还没有赢过 `top_reward_success_only`
- 当前仍然是 `active_selection_hypothesis = hypothesis_not_supported`

这条负结果被完整保留下来，没有被包装成成功。

## 当前可以合理对外声称的内容

1. 项目已经形成研究级原型，核心机制链完整。
2. bounded open-world 自动蒸馏已经有支持性 fresh evidence。
3. bounded evolution improvement 已经有更真实的 fresh evidence。
4. teaching-utility 这条线目前并未证明 active 选择优于朴素基线。

## 当前还不能声称的内容

1. 任意 open-world 材料上都能稳定自动蒸馏。
2. evolution 已经在广泛任务上稳定产出更优 Skill。
3. 已经拿到官方 CyberSecEval / AutoPatchBench / CVE-Bench / SWE-bench 结果。
4. 系统已经是可以直接部署的真实安全产品。

## 当前最稳的总体判断

如果需要一句更适合阶段汇报的话：

> 目前我们已经完成了一个 evidence-grounded Skill Evolution Runtime 的研究级原型。系统不只是一个安全 Skill，而是支持 Skill 蒸馏、安装、执行、证据收集、候选生成、严格门控、拒绝与回滚的完整闭环；并且在 bounded open-world 自动蒸馏与 bounded evolution improvement 上已经形成支持性 fresh evidence。但这些证据仍然是有界、本地、可审计的，还不是官方外部 benchmark 或通用真实世界能力证明。

## 建议优先看的文件

1. `README.md`
2. `reports/OPEN_WORLD_DISTILLATION_VALIDATION_STATUS.md`
3. `reports/OPEN_WORLD_CLOSED_LOOP_STATUS.md`
4. `reports/TEACHING_UTILITY_V02_STATUS.md`
5. `docs/CLAIM_BOUNDARY.md`
