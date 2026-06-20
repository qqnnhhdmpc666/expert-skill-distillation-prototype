# V1 Walking Skeleton Quickstart

## 环境

- Windows PowerShell 或等价 shell
- Python 3.11+
- V1 core 不需要 Docker、Harbor、向量数据库或商业模型

## 干净安装

```powershell
git clone <repository-url>
cd expert-skill-distillation-prototype
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .[dev]
```

`streamlit` 只属于 legacy UI，可按需执行 `python -m pip install -e .[ui]`，不是 V1 core 依赖。

## 单命令 smoke

```powershell
eskill --state-dir .eskill demo --data-dir data/v1_walking_skeleton
```

该命令真实执行：source capture、EvidenceUnit materialization、Stage 0–9 Compiler、ReleaseBundle build、validation、首次 promotion 和 pair decision。

## 审计

```powershell
eskill --state-dir .eskill history
eskill --state-dir .eskill inspect bundle <bundle-digest>
eskill --state-dir .eskill inspect session <session-id>
```

`.eskill/metadata.sqlite` 是状态真相源；`outputs/` 中的历史文件不参与 V1 active runtime。

## Formal independent Judge

Core-local smoke 不依赖商业模型。正式 source-grounding gate 可显式启用独立 LLM Judge：

```powershell
$env:DEEPSEEK_API_KEY = "<your-key>"
eskill --state-dir .eskill build python-advisory `
  --require-judge `
  --judge-base-url https://api.deepseek.com `
  --judge-model deepseek-chat
```

Judge 只看到盲化 node/support/Skill IR，不看到方法标签或 held-out gold。密钥不进入 artifact；HTTP、schema 或 Judge failure 均不会被改写为通过。

## 失败语义

- 不支持的 requirements 语法：`completed + parse_error`
- advisory 不在冻结 snapshot：`completed + unresolved / ADVISORY_NOT_FOUND`
- hard knowledge binding 不可用：`blocked`
- Bundle 闭包损坏：`runtime_failure`

这些状态不得相互替代。
