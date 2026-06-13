# 文件上传安全审查经验材料

上传接口的高风险点通常不在单个 if 判断里，而在类型判定、路径处理、公开访问、错误响应和审计链路共同缺失。审查时应优先确认：服务端是否只依赖 filename.endswith 这类用户可控字段；是否将 Content-Type 当作唯一依据；是否校验内容魔数；是否把原始文件名直接拼接进持久化路径；上传目录是否位于可公开访问或可执行路径；错误响应是否泄露内部路径、邮箱、token、api_key 或 stacktrace；上传、下载、删除等高风险操作是否进入审计日志并有保留策略。

审查者不能因为看到扩展名检查就判断上传安全。扩展名、MIME 类型、内容魔数和隔离存储路径需要交叉验证。对于下载接口，需要检查 filename/path 参数是否可能造成 ../ 路径穿越。对于错误响应，需要检查 debug_path、SQL error、stacktrace、api_key 等敏感线索。对于合规要求，需要检查 audit_log_retention_days 或等价策略是否存在且非空。

输出 finding 时必须绑定 evidence_span，说明 affected endpoint、risk_level 和 recommended_fix。证据不足时应标记 evidence_missing 或省略 finding，不能凭经验直接下结论。
