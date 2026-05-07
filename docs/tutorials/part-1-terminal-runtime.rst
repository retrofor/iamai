第一步：跑通一个终端 Runtime
============================

这一章把 iamai 当成本地程序来使用。终端适配器没有网络鉴权、平台账号和回调地址，
适合先把插件模型理解清楚。

本章目标
--------

- 跑通一个已有示例；
- 写一个新的 ``@command``；
- 看懂一次事件分发中各对象的职责。

使用现成示例
------------

先做配置检查：

.. code-block:: bash

   uv run python -m iamai --config examples/echo-runtime/config.terminal.toml config-check

再启动：

.. code-block:: bash

   uv run python -m iamai --config examples/echo-runtime/config.terminal.toml

输入：

.. code-block:: text

   /echo hello

示例已经包含一个终端适配器、一个 echo 插件和一组开发态管理命令配置。

自己写一个命令
--------------

新插件只需要继承 ``Plugin``，并用 decorator 声明 handler：

.. code-block:: python

   from iamai import Context, Plugin, command


   class HelloPlugin(Plugin):
       name = "hello"

       @command("hello")
       async def hello(self, ctx: Context) -> None:
           await ctx.reply("你好，iamai 已经工作。")

``Context`` 是插件作者最常用的对象。它把事件、适配器、插件配置、状态和回复方法放在一起，
避免 handler 直接依赖具体平台。

把插件挂进配置
--------------

插件可以用 ``module:ClassName`` 或 ``path/to/file.py:ClassName`` 引用。示例项目通常使用
后者，因为它对新读者更直观：

.. code-block:: toml

   [runtime]
   command_prefixes = ["/"]
   adapters = ["terminal"]
   plugins = ["src/echo_runtime/plugins/hello.py:HelloPlugin"]

如果你把插件放在包里，也可以配置 ``python_paths`` 后使用模块路径。

Checkpoint
----------

到这里你应该能说清楚：

- 事件来自适配器，而不是插件自己读取输入；
- ``Runtime`` 负责把事件分发给匹配的 handler；
- handler 通过 ``Context`` 回复消息；
- 命令是否匹配，先受 ``command_prefixes`` 影响。

下一章会加入规则和权限，让同一个 Runtime 根据消息内容、来源和用户身份做不同响应。
