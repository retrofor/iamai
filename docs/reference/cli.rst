CLI 参考
========

``iamai`` 和 ``python -m iamai`` 使用同一套入口。

运行 Runtime
------------

.. code-block:: bash

   iamai --config config.toml
   iamai --config config.toml run

如果没有指定子命令，默认执行 ``run``。

配置检查
--------

.. code-block:: bash

   iamai --config config.toml config-check

该命令会：

- 加载 TOML；
- 校验内置配置模型；
- 加载插件；
- 校验插件配置；
- 构建适配器；
- 打印风险告警。

配置 Schema
-----------

.. code-block:: bash

   iamai --config config.toml config-schema
   iamai --config config.toml config-schema echo

无插件参数时输出版本化的根配置 JSON Schema，其中包含 runtime、logging、state、adapter 和
plugin 表。指定插件名时，继续输出该插件的单独配置 Schema，供现有工具兼容使用。

根 Schema 的 ``$id`` 是 ``urn:iamai:config-schema:v1:root``，合同版本位于
``x-iamai-contract-version``。同一配置加载的扩展集合与 management API ``GET /schema``
输出完全一致。

内置管理命令
------------

启用 ``management`` 插件并允许 introspection 后，可在消息入口使用这些诊断命令：

- ``/plugins``：列出已加载插件。
- ``/plugin <name>``：查看单个插件元数据。
- ``/plugin-config <name>``：查看插件配置 schema。
- ``/handlers``：列出已注册 handler。
- ``/adapters``：列出已加载适配器。
- ``/health``：查看运行时健康摘要。
- ``/metrics``：查看运行时计数器。
- ``/sessions``：查看活跃 session。
- ``/trace`` / ``/trace last``：查看插件 trace 摘要或最近一条 trace。
