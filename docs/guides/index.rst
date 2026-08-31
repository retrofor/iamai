模块指南
========

教程负责把你带过一条连续路径；指南负责回答真实项目里会反复遇到的问题。这里按职责拆成
“理解架构、构建扩展、运行上线、发展方向”几组，每页都说明边界、推荐实践和常见误区。

按任务选择
----------

.. container:: iamai-path

   **理解框架边界**
      架构、配置系统、插件与适配器如何分工。
      :doc:`architecture` · :doc:`configuration`

   **构建业务能力**
      插件、状态、会话和消息侧 Agent helpers 的实践路径。
      :doc:`plugins` · :doc:`state-and-sessions` · :doc:`agent-runtime`

   **运行研究 Trial**
      用 headless Harness 组合 Task、Agent、Environment、Trajectory 与 Evaluation，并把持久化 Experiment
      保存为可校验的 JSONL，再从预登记分布生成固定分母的配对证据。
      :doc:`research-harness` · :doc:`roadmap`

   **接入与上线**
      平台适配、Webhook、运维、安全和质量门禁。
      :doc:`adapters` · :doc:`operations` · :doc:`migration-0.3-to-1.0`

   **生态方向**
      和主流 Runtime/Agent 框架对比，明确 iamai 的定位、路线图和设计决策。
      :doc:`ecosystem-comparison` · :doc:`roadmap`

章节列表
--------

.. toctree::
   :maxdepth: 1

   architecture
   configuration
   plugins
   state-and-sessions
   adapters
   agent-runtime
   research-harness
   operations
   migration-0.3-to-1.0
   ecosystem-comparison
   roadmap
