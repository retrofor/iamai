配置系统
========

iamai 使用 TOML 配置，并在启动前做结构化校验。配置系统的目标不是替代部署平台，
而是把“消息运行时必须知道的边界”写成可审计、可检查、可文档化的输入。

基本结构
--------

.. code-block:: toml

   [runtime]
   command_prefixes = ["/"]
   adapters = ["terminal"]
   plugins = ["src/my_runtime/plugins/hello.py:HelloPlugin"]
   superusers = ["10000"]

   [adapter.terminal]
   prompt = "iamai> "

   [plugin.hello]
   greeting = "hello"

   [state]
   backend = "json"
   path = "var/state.json"

``[runtime]`` 定义运行时骨架，``[adapter.*]`` 定义协议入口，``[plugin.*]`` 交给插件模型验证，
``[state]`` 定义持久化后端。

可安装扩展
----------

插件和适配器可以作为 Python 包发布。使用者通过 ``uv add`` 安装后，有两种启用方式。

显式启用：

.. code-block:: toml

   [runtime]
   plugins = ["echo"]
   adapters = ["telegram"]

``echo`` 和 ``telegram`` 可以是内置名、entry point 名或 ``module:Class`` 导入路径。

自动发现：

.. code-block:: toml

   [runtime]
   auto_discover_plugins = true
   auto_discover_adapters = true

自动发现会加载当前环境中所有 ``iamai.plugins`` 和 ``iamai.adapters`` entry points。生产环境建议
显式列出扩展；自动发现更适合开发、示例和受控私有运行环境。发布规范见 :doc:`../reference/extensions`。

配置检查命令
------------

.. code-block:: bash

   uv run python -m iamai --config config.toml config-check

这个命令不仅验证语法和类型，也会输出高风险运行时告警，例如：

- 非 loopback 监听却没有 ``access_token``；
- 管理命令打开但没有 ``superusers``；
- ``allow_query_token = true``；
- ``runtime.allow_external_paths = true``；
- webhook 对公网开放却没有 ``signature_secret``。

路径解析
--------

``plugin_dirs`` 和 ``python_paths`` 默认被限制在配置根目录内。只有显式设置
``runtime.allow_external_paths = true`` 才允许引用根目录外的路径。

这条约束是为了让开发、CI 和部署的行为一致。共享示例时可以使用相对路径；生产环境应避免让
配置文件指向不受版本控制的外部 Python 文件。

敏感字段
--------

配置展示和管理命令输出会自动脱敏 ``token``、``secret``、``password``、``api_key`` 等字段。
不要把脱敏当作密钥管理。真实密钥仍应通过部署系统、环境变量或受控 secret store 管理。

配置 Schema
-----------

插件声明 ``config_model`` 后，可以导出 JSON Schema：

.. code-block:: bash

   uv run python -m iamai --config config.toml config-schema
   uv run python -m iamai --config config.toml config-schema greeting

这适合放进文档、CI 或内部平台表单生成流程。

推荐实践
--------

- 把 ``config-check`` 放进 CI。
- 生产配置显式列出 ``runtime.superusers``。
- 网络适配器同时考虑入站鉴权和出站回调限制。
- 示例配置可以宽松，生产配置应保守。
