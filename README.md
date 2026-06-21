# Expert Skill Distillation System

这是一个面向 Agent 的专家知识编译与 Skill 演化研究原型。它把异构专家材料转换成可追溯的 Knowledge IR、可执行的 Skill IR 和运行时知识投影，并将它们连同权限、验证器和依赖一起发布为不可变 `ReleaseBundle`。

项目关注的不是“把文档改写成一段提示词”，而是形成完整闭环：

```text
专家材料 -> Knowledge Compiler -> Skill + Knowledge Projection
         -> Agent Runtime -> Execution Evidence
         -> Validate / Promote / Reject / Rollback
```

## 当前可以做什么

V1 提供一个可安装、可审计的 Python 依赖安全公告适用性切片：读取固定版本依赖、环境信息和冻结 OSV 公告，判断公告是否适用，并给出证据摘要与原因码。

系统目前支持：

- 专家 Markdown、pinned requirements、冻结 OSV JSON 的来源接入；
- 带行号、字节范围和内容摘要的 EvidenceUnit；
- Knowledge IR、Skill IR、Knowledge Projection 分离；
- 内容寻址存储、SQLite 状态、不可变 ReleaseBundle；
- 安装、执行、验证、晋升、拒绝与完整 Bundle 回滚；
- `no_skill / full_material / direct_to_skill_ir / compiler_distilled_skill` 诊断对照；
- 独立 LLM Judge、Codex AgentHost 和 Harbor 的可选适配与失败契约。

## 快速开始

需要 Python 3.11+：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .[dev]

eskill --state-dir .eskill demo --data-dir data/v1_walking_skeleton
```

成功后会返回真实的 `bundle_digest`、`session_id`、适用性结论、reason code 以及 OSV snapshot/query/result digest。

## 分步运行

```powershell
eskill --state-dir .eskill init
eskill --state-dir .eskill source add data/v1_walking_skeleton/expert_spec/python_advisory_review.md --adapter expert-document
eskill --state-dir .eskill source add data/v1_walking_skeleton/osv/PYSEC-2018-28.json --adapter osv-snapshot
eskill --state-dir .eskill build python-advisory
eskill --state-dir .eskill validate bundle <bundle-digest>
eskill --state-dir .eskill promote python-advisory <bundle-digest> --expected-generation 0
eskill --state-dir .eskill run python-advisory --requirements data/v1_walking_skeleton/runtime_inputs/requirements.txt --environment data/v1_walking_skeleton/runtime_inputs/environment.json --advisory PYSEC-2018-28
```

研究诊断：

```powershell
eskill --state-dir .eskill evaluate-compiler --data-dir data/v1_walking_skeleton
eskill --state-dir .tmp/evolution-eval evaluate-evolution
eskill --state-dir .eskill qualify-agent-host
eskill --state-dir .eskill qualify-harbor
```

## 为什么 Skill 和知识分开

Skill 保存稳定的流程、约束、异常处理和工具使用方法；Knowledge Projection 保存会变化的公告、版本范围和环境事实。更新 OSV snapshot 时，Skill 可以保持不变，而知识投影与 ReleaseBundle 获得新 digest。这样二者可以独立更新、验证和回滚。

## 当前证据

- Core Walking Skeleton：通过。
- 安全更新事务：晋升、危险更新拒绝、原 digest 回滚均通过。
- 有界演化改进：一个 changed-source case 从错误变为正确，旧回归和负例未退化；这是 source-bound Bundle 改进，不是稳定自主 Skill 进化证明。
- Compiler 对照：已在 6 个 dev case 上运行，但 reference backend 不消费条件特定 Skill，因此结果为 inconclusive，不能声称 compiler 优于直接生成。
- Independent Judge：正式请求到达 DeepSeek，但当前凭据返回 HTTP 401。
- Codex AgentHost：适配与失败契约完成，当前执行环境的认证/网络阻塞真实 Agent 完成。
- Harbor：本机缺少 Harbor、Docker 和 WSL distribution，仅完成非 replay contract test。

详见 [V1 状态](reports/V1_WALKING_SKELETON_STATUS.md) 和 [Quickstart](docs/V1_WALKING_SKELETON_QUICKSTART.md)。

## 不能据此声明什么

- 不能声明通用 open-world 自动蒸馏已经成立；
- 不能声明 Knowledge Compiler 稳定优于 direct baseline；
- 不能声明 evolution 会稳定产生更优 Skill；
- 不能声明 AgentHost、Harbor 或公开外部 benchmark 已通过；
- 不能把公告适用性等同于漏洞可达、可利用或项目已受影响。

## 仓库结构

```text
src/expert_skill_system/   V1 compiler、registry、runtime、deployment、evaluation
data/v1_walking_skeleton/ 冻结专家规范、OSV snapshot 与 dev/runtime cases
tests/v1/                 V1 contract、integration、transaction tests
docs/design_v03/          Freeze v1.0.3 架构规格
reports/                  实验状态与边界报告
src/skill_deployment/     旧受控实验系统，保留作 legacy baseline
```

项目采用 [MIT License](LICENSE)。只处理防御性安全分析，不生成 exploit、不执行攻击链、不访问未授权目标。
