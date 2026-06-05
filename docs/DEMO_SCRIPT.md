# Demo Script

## 1. 一句话开场

我们做的是一个专家 Skill 蒸馏原型：从专家材料生成 skill，再用执行反馈检查它是否真的可靠，最后把失败反馈回写成更适合调用的 compact skill。

## 2. 演示主线

第一步，输入专家材料。

系统读取 API 设计规范、review checklist 和历史专家评审意见，生成：

```text
full_skill.md
evidence_map.json
rule_ledger.json
```

第二步，生成 compact v1。

为了降低调用成本，系统先保留高优先级、材料证据充分的规则：

```text
R001-R004
```

所以 compact v1 更短，但它会漏掉：

```text
R005 response envelope
R006 idempotency
```

第三步，执行验证。

我们用 Harbor verifier、mock agent 和 RightCode `gpt-5.5` 都验证过：

```text
compact v1 -> review.json -> missing R005/R006 -> reward 0.0
compact v2 -> review.json -> covers R001-R006 -> reward 1.0
```

第四步，回写 ledger。

verifier 的失败不是普通日志，而是进入 `rule_ledger`：

```text
R005/R006 -> failure_critical -> compact_patch -> decision_v2 = patch
```

第五步，生成 compact v2。

compact v2 把 R005/R006 补回去，在成本仍低于 full skill 的情况下恢复完整 checklist coverage。

## 3. 新增 failure type

我们还做了第二种失败：

```text
output_format_error
```

这不是漏规则，而是输出 JSON 不满足 verifier 合约，例如缺少 `severity` 或 `evidence` 字段。系统对应的 patch 不是补 R005/R006，而是：

```text
rewrite_output_contract
```

也就是在 compact skill v2 中补入明确 JSON schema 和 required fields。

## 4. 当前边界

这不是大规模 benchmark。当前重点是证明：

- skill 可以从专家材料生成；
- compact skill 会影响 agent 输出；
- verifier failure 可以回写到具体规则或输出合约；
- 不同 failure type 可以触发不同 patch action；
- decision policy 已经可以开始比较，但还需要更多 case 才能形成强结论。
