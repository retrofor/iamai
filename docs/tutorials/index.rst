渐进式教程
==========

这一组教程按“从能跑到能上线”的路径组织。每一章只引入一个主要能力，并在结尾留下
一个可以自查的 checkpoint。你不需要先理解全部架构，再开始写插件。

学习路线
--------

.. container:: iamai-path

   **1. 跑通终端 Runtime**
      建立 ``Adapter``、``Event``、``Plugin`` 和 ``Context`` 的直觉。

   **2. 加入命令、规则与权限**
      让 Runtime 开始有选择地响应消息，并把匹配结果交给 handler。

   **3. 引入状态、会话与中间件**
      支持多轮交互、持久化状态和横切处理。

   **4. 进入 Webhook 与生产化**
      补上鉴权、验签、出站回调和观测能力。

   **5. 编写真实适配器**
      把 Telegram 长轮询适配器拆成配置、接收、归一化、发送和测试。

   **6. 发布到社区商店**
      走完整的表单、GitHub issue、维护者审核和 registry 合入流程。

这些章节不是 API 手册。遇到参数细节时，可以同时打开 :doc:`../api/index` 和
:doc:`../reference/index`。

.. toctree::
   :maxdepth: 1

   part-1-terminal-runtime
   part-2-commands-rules
   part-3-state-sessions
   part-4-webhook-production
   part-5-adapter-development
   part-6-ecosystem-publishing
