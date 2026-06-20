# Design v03 规格入口

本目录定义下一代专家知识蒸馏与 Skill 演化系统的 V1 目标。它描述的是待实现系统，不等于当前仓库已经具备相应能力。

## 阅读顺序

1. `SYSTEM_ARCHITECTURE_FREEZE_V1.md`
   - 冻结系统问题、对象边界、不变量、ReleaseBundle 和 V1 纵向任务。
2. `IMPLEMENTATION_TECHNOLOGY_FREEZE_V1.md`
   - 把对象映射到进程、Python 模块、存储、接口、运行后端和失败语义。
3. `INITIAL_SKILL_CONSTRUCTION_METHOD_SPEC.md`
   - 定义专家材料到 Knowledge IR、Skill IR 和 Knowledge Projection 的真实编译流程。
4. `WALKING_SKELETON_V1.md`
   - 定义第一条必须跑通的端到端纵向闭环、命令和验收。
5. `EXTERNAL_REFERENCE_ADOPTION_MATRIX.md`
   - 记录外部方法中借什么、如何适配、明确不借什么，以及采用前如何验收。

## 规范优先级

发生冲突时按以下顺序处理：

```text
架构不变量与主张边界
> V1 domain/output contract
> Implementation Technology Freeze
> Initial Construction Method Spec
> Walking Skeleton
> 参考项目的默认做法
> 当前原型代码的偶然行为
```

当前代码和旧报告不能反向修改冻结规范。若实现发现规范不可行，应提交 ADR，说明问题、替代方案和迁移影响；不能在脚本中静默形成第二套契约。

## 当前状态

```text
architecture: freeze_ready
implementation_technology: specified_not_implemented
knowledge_compiler: specified_not_implemented
walking_skeleton: specified_not_implemented
legacy_runtime: controlled_prototype_available
```

当前 `src/skill_deployment/` 中可复用的是安装状态、BackendRunner、Evidence Bundle、provenance、verifier 和门控经验。当前 keyword/capability-registry 蒸馏、脚本式 CLI、JSON active pointer 和 replay adapter 都是迁移输入，不是 V1 目标实现。
