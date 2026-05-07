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

如果插件声明了 Pydantic ``config_model``，这里会输出 JSON Schema。

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
