# V1 Walking Skeleton Quickstart

## 安装与单命令演示

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .[dev]
eskill --state-dir .eskill demo --data-dir data/v1_walking_skeleton
```

V1 core 不需要 Docker、Harbor、向量数据库或商业模型。

## 审计与运行

```powershell
eskill --state-dir .eskill history
eskill --state-dir .eskill inspect bundle <bundle-digest>
eskill --state-dir .eskill inspect session <session-id>
eskill --state-dir .eskill baselines
eskill --state-dir .eskill evaluate-compiler --data-dir data/v1_walking_skeleton
```

`.eskill/metadata.sqlite` 是运行状态真相源；历史 `outputs/` 不参与 V1 active runtime。

## Independent Judge

```powershell
$env:DEEPSEEK_API_KEY = "<your-key>"
eskill --state-dir .eskill build python-advisory `
  --require-judge `
  --judge-base-url https://api.deepseek.com `
  --judge-model deepseek-chat
```

HTTP、认证、schema 或 Judge fail 都不会被改写为 pass，密钥不会进入 artifact。

## 外部适配资格检查

```powershell
eskill --state-dir .eskill qualify-agent-host
eskill --state-dir .eskill qualify-harbor
```

这些命令会留下成功或硬阻塞证据。contract test 不能替代真实 AgentHost/Harbor pass。

## 演化评估

必须使用全新状态目录：

```powershell
eskill --state-dir .tmp/evolution-eval evaluate-evolution `
  --expert-spec data/v1_walking_skeleton/expert_spec/python_advisory_review.md
```

该实验验证 accepted update、unsafe rejection 与 original-digest rollback；结果只支持有界 source-update improvement。

## 完整验证

```powershell
python -m pytest -q
python -m ruff check src/expert_skill_system tests/v1
python scripts/validate_task_cases.py
python -m skill_deployment.cli validate-review-package
```

失败语义严格区分：领域未知是 `completed + unresolved`；缺 hard knowledge binding 是 `blocked`；Bundle 损坏是 `runtime_failure`；AgentHost failure 不能写成领域 unresolved。
