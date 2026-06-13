# 真实 Agent 闭环纠错报告

## 任务摘要

任务：外部专家材料安全审查任务

任务目标：

根据用户粘贴的专家材料和目标资产，构建一个受控安全审查 Skill，并展示优化前后的效果。

专家知识：

请审查下面这段专家材料和目标资产，生成一个可执行的安全审查 Skill。

专家材料：
- 高风险文件上传需要 MIME、内容魔数、扩展名和隔离存储共同约束。
- 用户可控文件名不能直接拼接到公开目录。
- 上传、下载、删除应记录审计日志并有保留周期。
- 错误响应不能泄露内部路径、邮箱、token 或 api_key。

目标资产：
Python 上传接口只检查 filename.endswith，并把文件保存到 /public/uploads/；
返回值包含 debug_path；配置里 debug=true，audit_log_retention_days=null。

目标资产：

请审查下面这段专家材料和目标资产，生成一个可执行的安全审查 Skill。

专家材料：
- 高风险文件上传需要 MIME、内容魔数、扩展名和隔离存储共同约束。
- 用户可控文件名不能直接拼接到公开目录。
- 上传、下载、删除应记录审计日志并有保留周期。
- 错误响应不能泄露内部路径、邮箱、token 或 api_key。

目标资产：
Python 上传接口只检查 filename.endswith，并把文件保存到 /public/uploads/；
返回值包含 debug_path；配置里 debug=true，audit_log_retention_days=null。

期望输出：生成可执行 Skill，并用该 Skill 产出带证据、修复建议和限制说明的任务报告。

## A1 verifier 反馈


## 修正策略

- 将缺失项写入 Skill v2 的 Evidence Protocol 和 Output Contract。
- 要求 agent 输出更具体的 evidence、improvements、limits。
- 重跑 A2，并保留完整 trajectory 和 model_calls 证据。

## A2 结果

- passed: True
- score: 1.0
- remaining missing: none