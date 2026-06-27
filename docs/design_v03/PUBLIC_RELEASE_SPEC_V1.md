# Public Release Specification V1

状态：`normative_release_target`

公开版本交付的是可复现研究原型，不是生产漏洞扫描器。

## 必须交付

- Python package 与 `eskill` CLI；
- pinned dependencies/lock、license、supported Python/OS matrix；
- Agent Skills 兼容导出和 example ReleaseBundle；
- clean-environment build/run/inspect/rollback demo；
- frozen public data snapshot、generator、split 和 evaluator；
- model/prompt/resource manifest，密钥除外；
- Harbor task pack 仅在 parity 通过后发布为正式 evaluation adapter；
- raw result、failure、blocked 与 claim-boundary 文档。

## 一条主流程

```text
install -> init -> source add -> build -> validate -> promote -> run -> inspect -> rollback
```

文档不得要求用户理解仓库内部脚本。发布 smoke 必须从不含 `.eskill`、`outputs` 和开发缓存的 clean checkout 执行。

## 发布门

```text
package_install=pass
core_walking_skeleton=pass
artifact_closure_reproducible=pass
rollback_original_digest=pass
public_data_provenance=pass
secret_scan=pass
license_metadata=pass
external_agent_effectiveness=pass|partial|blocked
```

最后一项可 blocked，但必须限制公开主张。没有 AgentHost/公开 evaluator 证据时，只能发布 core/runtime prototype，不能声称自动蒸馏或 evolution 的外部有效性。

## 暂不承诺

- 多租户、服务 SLA、Web UI；
- live CVE 完整性或 exploitability；
- 通用 open-world 自动蒸馏；
- evolution 稳定产生更优 Skill；
- Harbor/OpenHands/Codex 在所有环境即装即用。

版本替换、数据更新和模型 profile 变化都必须产生新的 manifest/digest；不能静默覆盖已报告结果。

