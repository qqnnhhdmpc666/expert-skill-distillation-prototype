# Demo Acceptance Check

This checklist verifies that the Streamlit demo is a minimal closed run console, not a fixed artifact viewer.

## Stable Demo Mode

Run:

```powershell
python -m streamlit run demo\streamlit_app.py --server.port 8501
```

Open:

```text
http://localhost:8501
```

Use the default `稳定演示模式`.

## Must Pass

1. 修改专家规则文本后，规则账本和 Skill 内容会随输入变化。
2. 修改任务环境对象后，Verifier expected rules / observed findings / missing rules 会随任务证据变化。
3. A1 failure 由 verifier 比较 `expected_rule_ids` 与 agent output 中的 observed rule ids 得到，不是页面硬编码。
4. Skill v1 缺少 `R005/R006` 时，Attempt A1 的 agent output 也缺少 `R005/R006`。
5. Verifier feedback 显示：
   - expected rules
   - observed findings
   - missing rules
   - failure type
6. Feedback 中的 affected rules 会进入 patch proposal。
7. 修正决策展示：
   - `missing_rule -> patch_rule`
   - `output_contract_error -> rewrite_output_contract`
   - `evidence_missing / failure_critical_rule -> add_trace_requirement`
8. Skill v2 diff 中能看到新增 `R005/R006` 和 trace / output contract 要求。
9. 点击“只重跑 Skill v2”后，页面显示 Skill v2 rerun result，并展示 `v1 FAIL -> v2 PASS`。
10. Gate 显示 `accept / reject_and_rollback`、token budget、lost previous rules 和原因。
11. 自由探索模式明确标注为 best-effort。
12. 稳定演示模式不连接真实网络目标，不执行真实漏洞利用，只检查受控 toy code / config / API。
13. 每次运行会落盘生成 `runs/demo_session_<scenario>/` 运行产物目录。
14. “运行产物”tab 能展示 source material、target asset、skills、attempts、revision、summary、timeline 和 model calls。
15. “效果对比”tab 能展示 Skill v1 与 Skill v2 的覆盖规则、漏检规则、证据链、输出契约和 verifier 结果差异。
16. 三个稳定场景触发不同机制：
    - 文件上传：`missing_rule -> patch_rule + add_trace_requirement`
    - 鉴权越权：`regression_observed -> reject_and_rollback`
    - 配置安全：`output_contract_error -> rewrite_output_contract`
17. 运行模式区分清楚：
    - 离线稳定演示模式明确标注未调用真实模型。
    - 真实模型模式未配置时不伪装调用。
    - 录制回放模式显示 recorded latency/tokens/response preview。

## Demo Claim Boundary

Can claim:

```text
This is a minimal expert-skill distillation and posterior-revision run console.
It demonstrates expert material -> Skill v1 -> execution -> verifier feedback -> typed repair -> gate -> Skill v2 -> rerun.
```

Do not claim:

```text
Full SPARK-PDI reproduction.
General vulnerability scanner.
Real exploit automation.
Large-scale empirical validation.
```
