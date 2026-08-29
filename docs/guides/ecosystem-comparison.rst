生态对比与发展方向
====================

本页用于校准 iamai 的定位。结论先说清楚：iamai 不应该追求“再做一个大而全的消息平台”，
也不应该只做“插件 decorator 的薄封装”。更有价值的方向是成为一个边界清晰、强工程约束、能把
协议接入、规则、状态、审计、Agent workflow 和 Rust 数据核心组合起来的开发框架。

.. container:: iamai-path

  **定位结论**
    iamai 是安全、可测试、可嵌入的 Python + Rust runtime/agent runtime，不是全功能平台替代品。

    **下一步行动**
      优先补适配器 SDK、生态发布规范、Agent 工具权限和管理 HTTP API。

    **落地入口**
      :doc:`roadmap` · :doc:`../reference/extensions` · :doc:`agent-runtime`

调研对象
--------

本节参考了这些框架和文档：

- NoneBot：`适配器 <https://nonebot.dev/docs/advanced/adapter>`__、
  `编写适配器 <https://nonebot.dev/docs/developer/adapter-writing>`__、
  `依赖注入 <https://nonebot.dev/docs/advanced/dependency>`__。
- Koishi：`适配器 API <https://koishi.chat/zh-CN/api/core/adapter>`__、
  `实现适配器 <https://koishi.chat/zh-CN/guide/adapter/adapter.html>`__。
- AliceBot：`适配器工具基类 <https://docs.alicebot.dev/api/adapter/utils>`__、
  `CQHTTP 适配器 <https://docs.alicebot.dev/guide/adapters/cqhttp-adapter.html>`__。
- iamai：`项目首页 <https://retrofor.github.io/iamai/>`__、
  `Adapter API <https://retrofor.github.io/iamai/api/>`__。
- LangBot：`文档首页 <https://docs.langbot.app/en/insight/guide>`__、
  `插件系统 <https://docs.langbot.app/en/plugin/plugin-intro>`__、
  `实现消息平台适配器 <https://docs.langbot.app/en/workshop/impl-platform-adapter>`__。
- AstrBot：`文档首页 <https://docs.astrbot.app/en/>`__、
  `插件开发入口 <https://docs.astrbot.app/en/dev/plugin.html>`__、
  `AI 能力 <https://docs.astrbot.app/en/dev/star/guides/ai.html>`__。
- OpenClaw：公开资料较分散，主要参考其自托管 agent、渠道 gateway、技能和工具执行方向：
  `OpenClaw Docs <https://clawdocs.org/>`__。
- Hermes Agent：`官方文档 <https://hermes-agent.nousresearch.com/docs/>`__、
  `GitHub <https://github.com/nousresearch/hermes-agent>`__、
  `Multi-Agent <https://hermes-agent.ai/features/multi-agent>`__。

架构形态
--------

这些项目大致可以分成四类，旧调研草稿中的分类已经合并到这里：

重核心分层型
   代表是 NoneBot。它强调 ``Driver / Adapter / Plugin`` 的明确分层、依赖注入和 matcher 体系，适合大型插件生态。

上下文 / 服务图型
   代表是 Koishi。适配器、服务、插件和控制台能力统一进入上下文图，运行时装卸、热重载和可视化管理很强。

轻量核心 + 适配器优先型
   代表是 AliceBot 和 iamai。核心 API 少，协议包外置，插件接口直接，适合快速二次开发和自定义接入。

协议标准层
   代表是 OneBot。它不解决插件模型，而是把实现端和应用端解耦，适合作为消息运行时的外部协议边界。

能力矩阵
--------

.. container:: iamai-table-scroll

   .. list-table::
      :header-rows: 1
      :widths: 13 11 11 11 11 11 11 11 11

      * - 项目
        - 协议适配
        - 插件生态
        - 规则/Matcher
        - 配置与运维
        - WebUI/管理 API
        - Agent 能力
        - 安全审计
        - 可嵌入性
      * - NoneBot
        - 成熟，多协议 adapter
        - Python 生态大
        - Matcher/DI 强
        - CLI 和驱动组合成熟
        - 依赖第三方插件
        - 非核心重点
        - 依赖项目治理
        - 中等，框架主导
      * - Koishi
        - 多账户、多平台强
        - 插件市场成熟
        - 中间件和服务图
        - 控制台和热重载强
        - 强
        - 可由插件扩展
        - 管理面强，权限需项目配置
        - 中等，平台主导
      * - LangBot
        - IM 平台接入完整
        - LLM 插件生态
        - Pipeline 偏产品化
        - 部署和运营面强
        - 强
        - RAG/MCP/LLM 原生
        - 需要隔离和工具治理
        - 中等，偏平台
      * - AstrBot
        - 多平台易用
        - 插件数量多
        - 面向 runtime 技能
        - 易部署
        - 强
        - 知识库/MCP/Agent
        - 适合轻量使用，需边界治理
        - 中等，偏应用
      * - AliceBot
        - 协议包清晰
        - 较小
        - Rule + handle 直接
        - 简洁
        - 弱
        - 非核心重点
        - 主要交给项目
        - 强
      * - iamai
        - Adapter/Event 主干清晰
        - 较小
        - Hook 和等待事件方便
        - 生命周期可控
        - 弱
        - 非核心重点
        - 主要交给项目
        - 强
      * - OpenClaw
        - 渠道 gateway 方向
        - 技能和工具生态
        - Agent workflow
        - 自托管运维
        - 项目化管理
        - 强
        - 权限和沙箱是核心风险
        - 中等
      * - Hermes Agent
        - 非 runtime 协议重点
        - Agent 工具生态
        - Multi-agent 编排
        - Agent runtime 配置
        - 管理面随实现
        - 强
        - 工具执行风险高
        - 中等
      * - iamai
        - 内置少量高质量 adapter，第三方包扩展
        - 起步中，静态商店
        - Rule/Permission 可组合
        - 配置校验、metrics、审计、热重载
        - 先做管理 API，不把 WebUI 放进核心
        - 先做 tool registry 和权限声明
        - 作为差异化重点
        - 强，库式 runtime

iamai 当前优势
------------------

- 公共 API 小，插件作者只需要理解 ``Plugin``、``Context``、``Event``、``Message``。
- Python 负责异步运行时，Rust 负责消息和纯数据转换，边界清晰。
- 配置校验、敏感信息 redaction、审计、metrics、热重载和状态后端已经在核心里。
- 规则系统和适配器中间件开始形成“可组合层”，适合做工程化扩展。
- 文档可以按教程、指南、参考分层，不必把全部能力塞进一个平台 UI。

工程路线图入口
--------------

iamai 当前不需要追求“大而全平台”。下一步优先补齐最能形成差异化的三件事：

.. list-table::
   :header-rows: 1
   :widths: 18 28 32

   * - 优先级
     - 要补的能力
     - 交付形态
   * - P0
     - 适配器 SDK 和 conformance tests
     - ``iamai-adapter-<platform>`` 发布规范、inbound/outbound/API/error 测试模板
   * - P0
     - 插件和适配器可发布生态
     - 静态商店字段、entry point 规范、包命名和兼容性说明
   * - P0
     - Agent 工具安全边界
     - tool permission、输入 schema、审计字段、人工审批声明
   * - P1
     - 多账户配置草案
     - ``adapter instance id`` 或 ``account id``，保留现有单实例写法
   * - P1
     - 管理 HTTP API
     - ``/health``、``/metrics``、``/adapters``、``/plugins``、``/sessions``、``/state``、``/schema``

具体版本目标见 :doc:`roadmap`。第三方扩展发布规范见 :doc:`../reference/extensions`。

差距到实现
----------

.. list-table::
   :header-rows: 1
   :widths: 22 28 28

   * - 当前差距
     - 本轮实现入口
     - 验收方式
   * - 第三方适配器缺少统一测试口径
     - ``iamai.testing.adapters`` 和 :doc:`adapters`
     - conformance helper 覆盖事件、出站、API 和关闭流程
   * - 社区商店安全字段不够强
     - :doc:`../reference/extensions`、:doc:`../community/blog/index` 和 :doc:`../community/store`
     - registry、表单、issue template 和校验脚本字段一致
   * - Agent tool 权限和审计不正式
     - :doc:`agent-runtime`
     - ``ToolRegistry`` 暴露权限名、输入 schema、审计字段和审批标记
   * - 运维只有聊天命令
     - :doc:`operations`
     - 可选 ``management_api`` 插件暴露只读 HTTP JSON API

差异化定位
----------

``iamai 1.0`` 的已发布定位是：

   一个安全、可测试、可嵌入的 Python + Rust 消息 Runtime。它不替用户隐藏工程边界，而是把协议、
   插件、规则、状态、权限与审计边界做清楚。

post-1.0 的架构方向是 :doc:`research-harness`：在不重定义稳定消息类型的前提下，建立 headless、
record-first 的通用 Agent 研究 Harness。消息 Runtime 以后可以通过桥接成为一种 Environment，
但 Harness 执行模型本身不构造或使用 Adapter、Plugin、Event、SessionManager 或某个 LLM provider。

这和几个方向不同：

- 不是 NoneBot 的生态替代品，而是更强调配置、观测和 Rust 数据核心的小型工程 runtime。
- 不是 Koishi/AstrBot/LangBot 那样的全功能平台，而是可以被平台、服务和私有系统嵌入的库。
- 不是 OpenClaw/Hermes 那样面向单个自主 Agent 产品的封装；Harness 优先保证 Task、Environment、
  Trajectory、Evaluation、预算和基线被显式记录、可审计、可回放、可比较。只有组件与外部依赖都
  确定且版本一致时，同一规范的 Re-execution 才应产生相同结果。

短期结论
--------

稳定消息 Runtime 继续遵守 ``1.x`` 合同；新增研究能力进入 provisional 的 ``iamai.harness``。
短期顺序是先完成可回放的 headless Trial，再扩展受控执行、持久化 Experiment 与消息桥接。
AGI 只是研究北极星，能力结论必须明确 Task/Environment 分布、seed、预算、组件版本和基线；
WebUI 仍作为独立插件或独立项目，不进入核心。具体里程碑见 :doc:`roadmap`。
