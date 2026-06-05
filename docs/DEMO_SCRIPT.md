# Demo Script

Target length: 3-5 minutes.

## 1. Opening

这次原型不是完整复刻 SPARK，也不是简单做一个 prompt 压缩工具。我们做的是一个受控 API-review family 上的 full vertical loop：

```text
专家材料
-> evidence-grounded full skill
-> compact deployment skill
-> agent output
-> verifier feedback
-> patch proposal
-> validation gate
-> compact v2 / rollback
-> selective trace for high-risk rules
```

核心问题是：

```text
专家 skill 如何在正确性约束下变成低成本、可追踪、可修正的部署 artifact？
```

## 2. Stable Demo Loop

先看最稳定的主线。系统读取 API 设计规范、review checklist 和历史专家评审意见，生成：

```text
full_skill.md
evidence_map.json
rule_ledger.json
compact_skill_v1.md
```

为了降低调用成本，`compact_v1` 先保留 R001-R004，所以更短，但它漏了两个执行中重要的规则：

```text
R005 response envelope
R006 idempotency / duplicate submission
```

在 baseline 中结果是：

```text
full_skill: 6/6
compact_v1: 4/6
compact_v2: 6/6
```

我们又用 Harbor verifier、mock agent 和 RightCode `gpt-5.5` 做了受控验证。结果一致：

```text
compact_v1 -> missing R005/R006
compact_v2 -> covers R001-R006
```

也就是说，失败不是停留在日志里，而是会回写到规则层：

```text
R005/R006 -> failure_critical -> patch proposal -> compact_v2
```

## 3. Method Discovery

接下来我们检查这个修正过程是否可靠。这里有三个关键发现。

第一，patch 不能盲目接受。一个 fixed-budget patch 可以补回 R005/R006，但可能丢掉 R003。rollback gate 会拒绝这种 patch：

```text
fixes original failure
but introduces regression
-> reject_and_rollback
```

第二，compact skill 不能只靠 rule ID 过 verifier。我们做了 semantic preservation audit，检查压缩规则是否仍保留触发条件、检查动作和输出行为。

第三，agent 不能只是机械输出 `R001-R006`。所以我们引入 invocation protocol，让 agent 输出 `rule_applications`，说明每条规则如何应用到输入证据上。

这一步发现一个真实 tradeoff：

```text
full trace can block shortcut
but costs 300 / 237 tokens
therefore validation gate rejects it
```

这不是失败，而是告诉我们：可验证性不是免费的。

## 4. Effect and Deployment Evaluation

为了避免只证明机制漂亮，我们补了一个 4-case controlled holdout。结果是：

```text
compact_v1 avg coverage: 0.58
patched_compact avg coverage: 1.00
```

这说明在当前 controlled API-review family 中，patch 不只是 artifact 变化，也反映到了任务行为上。

然后我们测试 selective trace：不是所有规则都 trace，而是只对 failure-critical / high-risk 规则付出 trace 成本。

关键结果：

```text
full_trace:
  300 / 237 tokens
  shortcut_blocked=true
  rejected as over budget

selective_trace_failure_critical:
  trace R005/R006
  183 / 237 tokens
  shortcut_blocked=true
  accepted
```

这给出当前最有价值的方向：

```text
risk-budgeted traceable skill deployment
```

也就是：专家规则要可信，compact 不能只省 token，patch 不能制造 regression，agent 使用规则要可观察，但 trace 成本要按风险分配。

## 5. Closing Boundary

当前不能说我们证明了通用正确性，也不能说这是 benchmark 或成熟 skill compiler。

我们可以保守地说：

```text
这个原型在受控 API-review family 中展示了一个 risk-budgeted traceable skill deployment loop：
专家材料生成 skill，verifier feedback 驱动 patch，validation gate 阻止 regression 和超预算部署，selective trace 把可验证性成本集中到高风险规则上。
```
