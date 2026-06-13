# 专家 Skill 蒸馏 Demo

## 一句话定位

用户输入专家材料和目标资产，系统生成一个可执行 Skill，并用三次运行证明它是否真的帮助解决任务：

```text
A0 无 Skill -> A1 初始 Skill -> A2 优化后 Skill
```

前端默认只展示用户关心的结果：任务是否解决、成功率是否提升、漏检是否减少、token 成本是多少、最终报告和纠错报告在哪里。

## 启动

在仓库根目录运行：

```powershell
python -m streamlit run demo\streamlit_app.py --server.port 8501
```

打开：

```text
http://localhost:8501
```

## 展示方式

1. 在“创建一个要解决的任务”里粘贴专家材料、目标资产或任务说明。
2. 默认样例是文件上传服务安全审查。
3. 页面会生成一个安全审查 Skill，并展示它能做什么。
4. 页面用 A0/A1/A2 对比说明 Skill 是否真的有帮助。
5. 完整证据不铺在首页，只通过“文档入口”和“证据入口”查看。

## 评审包

生成外部评审包：

```powershell
python scripts\export_review_package.py
```

输出：

```text
review_package/index.html
review_package.zip
```

`index.html` 是给外部评审看的摘要页，包含：

- “先看有没有用”的结果摘要
- 多任务闭环验证：同一 pipeline 跨 3 类任务，触发 3 类反馈，生成 3 类修正，A2 3/3 通过
- WSL2 / Harbor 真实上传安全审查任务：reward 1.0
- 项目级验收报告：测试、多任务闭环、评审包导出、WSL2 后端和真实安全任务一键检查
- 生成的 Skill
- 最终输出摘要
- 最终报告、纠错报告、Skill manifest、多任务产物、WSL2 安全任务产物和实现借鉴说明入口

## 真实模型模式

页面支持 OpenAI-compatible 接口：

```text
OPENAI_BASE_URL
OPENAI_API_KEY
MODEL
```

如果这些环境变量没有配置，页面不会伪造模型调用，而是使用离线稳定流程。真实模型可参与 Skill 候选生成和解释，最终 verifier、报告落盘和评审产物仍保持本地确定性。

选择“真实模型”不会自动发起网络请求。页面会先显示“真实模型生成控制”，用户点击“开始真实模型生成”后才进入阶段化过程记录：

```text
准备请求 -> 生成 Skill 候选 -> 本地结构化落盘 -> A0/A1/A2 验证 -> 报告入口
```

## 真实 Agent 闭环

仓库现在包含一个可单独运行的真实 LLM agent loop：

```powershell
$env:OPENAI_BASE_URL="https://www.right.codes/codex/v1"
$env:OPENAI_API_KEY="..."
$env:MODEL="gpt-5.5"
python scripts\run_generic_agent_loop.py --output-dir runs\real_agent_loop_rightcode
```

该脚本会把任意任务文本落成完整证据链：

```text
inputs/task.md
trajectory.jsonl
model_calls.json
skills/skill_v1.md
skills/skill_v2.md
attempts/A0_no_skill.json
attempts/A1_skill_v1.json
attempts/A2_skill_v2.json
verifier/A1_feedback.json
verifier/A2_feedback.json
revision/patch_plan.json
reports/correction_report.md
run_summary.json
```

当前网页的“真实模型”按钮已经接入该脚本。点击开始后，页面会触发：

```text
A0 无 Skill -> distill Skill v1 -> A1 -> verifier -> distill Skill v2 -> A2
```

并显示真实模型调用状态、token、延迟、trajectory 和 A2 输出入口。若模型未配置或远端失败，页面会记录错误，不会伪造成真实执行成功。

## 边界

当前 Demo 不是通用漏洞扫描器。它展示的是在受控安全审查任务中，专家材料如何变成 Skill，Skill 如何通过执行反馈被修正，以及修正后报告质量如何提升。

WSL2 / Harbor / SPARK sandbox 已经跑通两个层次：

```text
1. SPARK hello-local smoke：Harbor oracle -> Docker task -> verifier reward -> RightCode/gpt-5.5 distills SKILL.md
2. real-upload-security-review：WSL2/Docker/Harbor 中执行上传安全审查任务，verifier 检查 security_report.json，reward 1.0
```

仍需明确边界：当前 Harbor 安全任务使用的是 Harbor `oracle` agent，证明了 sandbox、真实任务、artifact 和 verifier 链路；还没有证明 `codex` / `qwen-coder` / `claude-code` 等真实 CLI agent 能独立解决任意漏洞任务。

## 与 SPARK-PDI / COLLEAGUE.SKILL 的关系

- SPARK-PDI 启发本项目采用 evidence-first 的 A0/A1/A2 轨迹展示。
- COLLEAGUE.SKILL 启发本项目保留 Skill manifest、版本和纠错文档入口。
- 具体实现差距与借鉴说明见：

```text
docs/review/implementation_borrowing_from_spark_colleague.md
```
