快速开始
==========

这一页只完成一件事：让你在本地跑起一个 iamai，并理解一次消息从输入到回复会经过哪些对象。
更深入的插件、状态、适配器和运维内容放在后面的教程与指南里。

你会得到什么
------------

跑完这一页后，你应该能判断：

- 配置文件是否能被 iamai 正确读取；
- 插件路径是否能被发现和加载；
- ``TerminalAdapter`` 是否能把本地输入转换成统一 ``Event``；
- handler 是否能通过 ``Context`` 回复消息。

准备环境
--------

在仓库根目录安装依赖：

.. code-block:: bash

   uv sync

先不要直接启动长期进程。对一个 Runtime 项目来说，第一步应该是让配置检查通过：

.. code-block:: bash

   uv run python -m iamai --config examples/echo-runtime/config.terminal.toml config-check

``config-check`` 会验证 TOML 结构、适配器配置、插件配置模型和高风险运行参数。
如果这里已经报错，启动命令通常只会把问题暴露得更晚。

运行示例 Runtime
----------------

最小的本地交互入口是 ``TerminalAdapter``：

.. code-block:: bash

   uv run python -m iamai --config examples/echo-runtime/config.terminal.toml

终端出现提示符后，输入：

.. code-block:: text

   /echo hello iamai

示例插件会把文本回复回来。这个流程虽然简单，但已经走完整条运行链路：

.. code-block:: text

   terminal input -> TerminalAdapter -> Event -> Runtime -> Plugin handler -> Context.reply()

读懂最小配置
------------

一个可运行配置通常包含四块：

.. code-block:: toml

   [runtime]
   command_prefixes = ["/"]
   adapters = ["terminal"]
   plugins = ["src/echo_runtime/plugins/echo.py:EchoPlugin"]

   [adapter.terminal]
   prompt = "iamai> "

``[runtime]``
   定义全局运行时行为，例如命令前缀、启用哪些适配器、加载哪些插件。

``[adapter.<name>]``
   定义协议接入点。终端、OneBot11、Webhook 都是适配器，只是外部协议不同。

``[plugin.<name>]``
   放插件自己的配置。插件如果声明了 ``config_model``，这里会在启动前被严格校验。

``[state]``
   定义插件持久化后端。没有配置时，状态只存在内存里。

写一个自己的插件
----------------

创建一个插件类，暴露一个命令：

.. code-block:: python

   from iamai import Context, Plugin, command


   class HelloPlugin(Plugin):
       name = "hello"

       @command("hello")
       async def hello(self, ctx: Context) -> None:
           await ctx.reply("Hello from iamai.")

把插件加入 ``[runtime].plugins`` 后重新运行：

.. code-block:: toml

   [runtime]
   command_prefixes = ["/"]
   adapters = ["terminal"]
   plugins = [
     "src/echo_runtime/plugins/echo.py:EchoPlugin",
     "src/echo_runtime/plugins/hello.py:HelloPlugin",
   ]

如果启用了热重载，也可以用管理命令重新加载插件；生产环境应只允许 superuser 使用这类命令。

常见卡点
--------

``ModuleNotFoundError``
   插件路径不在配置根目录或 ``python_paths`` 里。优先使用相对配置文件的路径。

``config-check`` 通过但没有响应
   先确认命令前缀，例如默认示例使用 ``/``，所以命令是 ``/echo`` 而不是 ``echo``。

管理命令提示权限不足
   检查 ``[runtime].superusers`` 和 ``[plugin.management]`` 的权限开关。

下一步
------

如果你要从零构建一个项目，继续阅读 :doc:`tutorials/index`。
如果你已经准备接真实平台，先看 :doc:`guides/adapters` 和 :doc:`guides/operations`。
