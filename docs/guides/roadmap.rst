路线图与设计决策
================

这页把 :doc:`ecosystem-comparison` 的定位落到工程顺序。目标不是把 iamai 做成全功能平台，
而是稳定一个安全、可测试、可嵌入的 Python + Rust runtime/agent runtime。

版本路线图
----------

``0.1``
   |planned| 稳定核心 API、文档、社区商店和发布流程。插件、适配器、规则、权限和状态后端应能通过
   ``uv add`` 安装，并通过 entry point 或显式导入路径启用。

``0.2``
   |drafting| 发布适配器 SDK 草案、adapter conformance tests、多账户配置草案，并至少补齐一个新增主流适配器。
   适配器包命名固定为 ``iamai-adapter-<platform>``，entry point 使用
   ``[project.entry-points."iamai.adapters"]``。

``0.3``
   |drafting| 引入 tool registry、agent permission、审计 trace 和 MCP gateway 试验。Agent tool 必须声明权限名、
   输入 schema、审计字段，以及是否需要人工审批。

``0.4``
   |planned| 增加管理 HTTP API 候选实现、配置 schema 导出和运行时检查增强。WebUI 不进入核心；如果需要 UI，
   应作为独立插件或独立项目调用管理 API。

``1.0``
   |planned| 冻结核心公共 API，发布兼容性规范，并明确 ``0.x`` 到 ``1.x`` 的迁移窗口。

.. |planned| raw:: html

   <span class="iamai-status-pill">planned</span>

.. |drafting| raw:: html

   <span class="iamai-status-pill">drafting</span>

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
   候选端点包括 ``/health``、``/metrics``、``/adapters``、``/plugins``、``/sessions``、``/state``、
   ``/schema``。WebUI 可以消费这些 API，但不绑定核心 runtime。

Rust 只承接纯数据热路径
   消息段转换、规则字段匹配、签名校验和事件 schema validation 可以逐步下沉到 Rust。网络生命周期、
   插件运行和平台 SDK 仍留在 Python，避免过早固化 PyO3 边界。
