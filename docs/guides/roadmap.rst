路线图与设计决策
================

这页把 :doc:`ecosystem-comparison` 的定位落到工程顺序。``1.0`` 已经稳定消息 Runtime；
后续工作在不改变这些语义的前提下，把 iamai 演进为可审计、可回放、可比较的通用 Agent 研究 Harness。

版本路线图
----------

``0.1``
   |shipped| 建立 Rust + PyO3 消息核心、Python runtime、插件与适配器基础契约。

``0.2``
   |shipped| 补齐规则、权限、中间件、状态后端、适配器 conformance tests、Telegram/Webhook 支持、
   社区商店和管理命令。

``0.3``
   |shipped| ``v0.3.0`` 提供 tool registry、agent permission、审计 trace、MCP gateway、管理 HTTP API
   和多种 Agent runtime 示例；同时为 handler 并发和 Session backlog 加入可配置资源边界。

``0.4``
   |integrated| 第三方适配器与插件的独立包发布规范、扩展 conformance tests 和配置 schema 导出
   已纳入 ``1.0`` 发布线，没有单独发布 ``v0.4.0`` tag。WebUI 不进入核心；如果需要 UI，
   应作为独立插件或独立项目调用管理 API。

``1.0``
   |shipped| ``v1.0.0`` 已发布。Runtime、Event、Context、SessionManager、Adapter、Plugin、
   序列化格式、生命周期规则和扩展兼容性组成稳定的 ``1.x`` 合同。

.. |shipped| raw:: html

   <span class="iamai-status-pill">shipped</span>

.. |integrated| raw:: html

   <span class="iamai-status-pill">integrated</span>

.. |implemented| raw:: html

   <span class="iamai-status-pill">implemented</span>

能力里程碑（非版本承诺）
------------------------

这些里程碑表达依赖顺序，不承诺版本号或日期。AGI 是研究方向，不是其中任意一项完成后的产品声明。
依赖不是纯线性：受控执行和消息桥接都是独立 Environment 轨；离线学习必须同时建立在版本化 Agent policy 和可信评测
分布之上。

.. code-block:: text

   Headless Trial
   ├── Policy-backed Agent ─────────────────────────────────────┐
   ├── Persistent Experiment → Paired evidence → Generalization suites ─┴── Offline learning
   ├── Controlled execution (independent Environment track)
   └── Messaging bridge (parallel Environment track)

语义与兼容性基线
   保留 ``Runtime``、``Event``、``SessionManager`` 等 ``1.x`` 名称的既有含义；Harness 能力只进入
   provisional 的 ``iamai.harness``，不从顶层 ``iamai`` 重新导出。

Headless Trial
   |implemented| 第一条 ``Task → Agent → Environment → Trajectory → Evaluation`` 垂直切片已经形成：
   无消息平台依赖、有界 Action 预算、确定性基线组件、失败与取消归因、不可变 Trajectory 和无副作用 Replay。

受控执行
   |implemented| 第一条受控异步 Tool 垂直切片已提供冻结声明与 schema 子集、静态 default-deny Policy、
   绑定单次请求的 Approval、Tool attempt 预算、基于 reservation 的 token/费用上限、每次调用的协作式
   timeout，以及 ``tool.call.outcome`` 审计证据。OS/进程/网络沙箱、Trial 总时限、远程持久审批、
   独立 usage meter、分布式预算、effect rollback 和外部 exactly-once 仍属后续工作。

持久化 Experiment
   |implemented| 第一条 JSONL 垂直切片已保存不可变 Experiment plan、调用方 provenance、variant/baseline
   标签、Trial start marker 与完整终态 Trajectory；支持完整性链、显式尾修复、已提交 Trial 的幂等恢复、
   start-only Trial 防重跑、计划冲突检测和 single-writer 纪律。artifact manifest、跨 Experiment 查询和
   schema migration 仍属后续工作。

配对实验评证协议
   |implemented| ``TaskDistributionManifest`` 把 suite、split、有序 case 和 sampling rule 预登记进 plan；
   manifest plan 只允许一个 baseline 与一个 candidate，并在 slot 层校验除 Agent 外的可比性。
   ``compare_experiment`` 只从完整、Store 校验后的结果产生固定分母的 ``TrialComparison`` 与
   ``ExperimentComparison``，显式报告每种终态、pass rate 和有 Evaluation 的配对 score delta。
   这是描述性证据，不是签名、显著性检验或跨分布泛化证明。

Policy-backed Agent
   |implemented| 第一条 provider-neutral policy checkpoint 垂直切片已提供冻结、hash-bound 的
   ``PolicyCheckpoint``、可替换 ``AgentPolicy``、``PolicyAgent`` 和确定性 ``ScriptedPolicy``；声明通过
   现有 Agent configuration 进入 Trial、Experiment 和 JSONL evidence。checkpoint 是调用方声明，
   不提供 provider/model attestation，也不保存凭据。remote provider adapter、model fingerprinting、
   更强的外部真实性证明、泛化评测、离线学习和消息桥接仍属后续工作。

泛化评测套件
   在 paired evidence 之上定义多个独立 Task/Environment distribution、污染与迁移检查、重复 seed、
   不确定性报告和回归门禁。任何“更通用”的结论必须跨预登记分布成立，不能从单一 comparison hash 推导。

消息桥接
   通过独立桥接把稳定消息 Runtime 作为一种 Environment 接入；``Event`` 不改名为 Observation，
   ``SessionManager`` 也不承担 Trial 存储职责。该分支可以与 Policy-backed Agent 和评测套件并行推进。

离线学习闭环
   只有 Policy-backed Agent、泛化评测套件和可追踪 checkpoint 都落地后，才研究数据筛选、回归评测与
   离线改进。任何“更通用”的结论都必须明确 Task/Environment 分布、种子、预算、版本和基线。

设计决策
--------

核心 API 先少后稳
   ``Adapter.start``、``Adapter.send_message``、``Adapter.call_api``、``Plugin``、``Context``、
   ``Event`` 和 ``Message`` 是第三方扩展的主要契约。新增能力优先通过规范、测试和 helper 提供。

适配器外置优先
   内置适配器只覆盖高质量基础平台。更多平台通过 ``iamai-adapter-<platform>`` 包发布，并用
   conformance tests 证明事件归一化、消息编码、API 调用和错误处理行为。

安全声明前置
   插件和 Agent 工具在进入社区商店前必须说明网络访问、凭据需求、危险动作和可选依赖。本阶段先做声明、
   审核字段和审计 trace，不承诺完整隔离沙箱。

管理面先 API 后 UI
   已有管理命令和观测接口继续保持窄合同；新增 HTTP 管理端点必须先定义权限与生命周期语义。
   WebUI 可以消费这些 API，但不绑定核心 Runtime。

Rust 只承接纯数据热路径
   消息段转换、规则字段匹配、签名校验和事件 schema validation 可以逐步下沉到 Rust。网络生命周期、
   插件运行和平台 SDK 仍留在 Python，避免过早固化 PyO3 边界。
