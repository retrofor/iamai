路线图与设计决策
================

这页把 :doc:`ecosystem-comparison` 的定位落到工程顺序。目标不是把 iamai 做成全功能平台，
而是稳定一个安全、可测试、可嵌入的 Python + Rust runtime/agent runtime。

版本路线图
----------

``0.1``
   |shipped| 建立 Rust + PyO3 消息核心、Python runtime、插件与适配器基础契约。

``0.2``
   |shipped| 补齐规则、权限、中间件、状态后端、适配器 conformance tests、Telegram/Webhook 支持、
   社区商店和管理命令。

``0.3``
   |latest-stable| ``v0.3.0`` 提供 tool registry、agent permission、审计 trace、MCP gateway、管理 HTTP API
   和多种 Agent runtime 示例；同时为 handler 并发和 Session backlog 加入可配置资源边界。

``0.4``
   |implemented| 第三方适配器与插件的独立包发布规范、扩展 conformance tests 和配置 schema 导出已进入
   ``dev``，并纳入 ``1.0`` 发布线，不单独承诺 ``v0.4.0`` tag。WebUI 不进入核心；如果需要 UI，
   应作为独立插件或独立项目调用管理 API。

``1.0``
   |release-candidate| 核心公共 API、兼容性规范和 ``0.x`` 到 ``1.x`` 迁移窗口已形成并通过 RC 验证，
   当前仍是候选契约。
   ``dev`` 当前为 ``1.0.0rc1``；稳定版仍需完成 `发布治理 #436
   <https://github.com/retrofor/iamai/issues/436>`_ 和最终精确 revision 验证。

.. |shipped| raw:: html

   <span class="iamai-status-pill">shipped</span>

.. |latest-stable| raw:: html

   <span class="iamai-status-pill">latest stable</span>

.. |implemented| raw:: html

   <span class="iamai-status-pill">implemented</span>

.. |release-candidate| raw:: html

   <span class="iamai-status-pill">release candidate</span>

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
