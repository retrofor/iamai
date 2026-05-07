iamai 文档
==============

.. container:: iamai-hero

   iamai 是一个面向插件开发和多平台接入的消息运行时。业务代码写成普通 Python 插件；
   适配器负责协议边界；配置、权限、状态、审计和文档都作为工程能力保留下来。

   :doc:`快速开始 <quickstart>` · :doc:`渐进式教程 <tutorials/index>` · :doc:`社区资源 <community/blog/index>`


.. container:: iamai-path

      **先跑起来**
         从安装、配置检查和终端 Runtime 开始，确认本地开发链路是通的。
         :doc:`installation` · :doc:`quickstart`

      **写业务插件**
         学命令、规则、权限、状态、会话和中间件，逐步把 Runtime 写成可维护模块。
         :doc:`tutorials/index` · :doc:`guides/plugins`

      **接入平台**
         理解 Adapter 边界，使用 OneBot11、Telegram、Webhook 或编写自己的适配器。
         :doc:`guides/adapters` · :doc:`tutorials/part-5-adapter-development`

      **准备上线**
         检查配置、安全、Webhook 签名、质量门禁、运维和社区发布流程。
         :doc:`guides/operations` · :doc:`reference/index`

文档路线
--------

.. container:: iamai-path

   **新用户**
      先读 :doc:`concepts`，再跑 :doc:`quickstart`，随后按顺序完成 :doc:`tutorials/index`。

   **插件作者**
      重点看 :doc:`guides/plugins`、:doc:`reference/rules`、:doc:`guides/state-and-sessions` 和
      :doc:`reference/extensions`。

   **适配器作者**
      重点看 :doc:`guides/adapters`、:doc:`tutorials/part-5-adapter-development` 和 API 参考里的
      ``iamai.adapter``。

   **社区贡献者**
      先查看 :doc:`community/blog/index` 和 :doc:`community/store`，再按 :doc:`tutorials/part-6-ecosystem-publishing` 提交条目。

设计取向
--------

- 插件只关心统一的 ``Event``、``Message``、``Context`` 和声明式规则。
- 适配器集中处理网络、鉴权、协议字段、重连、回包和平台 API。
- 配置在启动前校验，生产风险通过参考文档和质量门禁显式暴露。
- 社区条目使用静态 registry，适合 GitHub Pages 和 Pull Request 审核流程。

.. toctree::
   :hidden:
   :maxdepth: 1
   :caption: 入门

   installation
   concepts
   quickstart

.. toctree::
   :hidden:
   :maxdepth: 2
   :caption: 学习路径

   tutorials/index

.. toctree::
   :hidden:
   :maxdepth: 2
   :caption: 构建与运维

   guides/index

.. toctree::
   :hidden:
   :maxdepth: 2
   :caption: 社区资源

   community/blog/index
   community/store

.. toctree::
   :hidden:
   :maxdepth: 2
   :caption: 参考

   reference/index
   api/index
