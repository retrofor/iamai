插件系统
========

插件是 iamai 的业务单元。一个成熟插件应该把入口声明、配置模型、状态范围和依赖关系写清楚，
这样它才能被配置检查、自动 API 文档和管理命令正确理解。

最小插件
--------

.. code-block:: python

   from iamai import Context, Plugin, command


   class EchoPlugin(Plugin):
       name = "echo"
       description = "Echo command for local testing."

       @command("echo")
       async def echo(self, ctx: Context) -> None:
           await ctx.reply(ctx.args or "empty")

``name`` 是配置、状态和管理命令里的稳定标识。不要依赖类名自动生成，除非插件只是临时实验。

Handler 类型
------------

``@command(...)``
   显式命令入口，适合用户主动触发的功能。

``@message_handler(...)``
   普通消息入口，适合关键词、正则、自然语言路由。

``@event_handler(...)``
   事件入口，适合非消息事件或需要直接按事件类型处理的逻辑。

规则、权限和依赖注入可以同时使用。规则描述消息是否匹配，权限描述调用者是否允许执行。

规则入口
--------

简单入口可以直接使用内置规则：

.. code-block:: python

   from iamai import Context, Plugin, message_handler, raw_field, when_all, word_in


   class DeployPlugin(Plugin):
       name = "deploy"

       @message_handler(
           rule=when_all(
               word_in("deploy"),
               raw_field("sender.role", equals="admin", capture_as="role"),
           )
       )
       async def deploy(self, ctx: Context, role: str) -> None:
           await ctx.reply(f"deploy requested by {role}")

如果入口分支很多，用 ``ruleset`` 给每个分支命名，并用 ``priority`` 控制匹配顺序：

.. code-block:: python

   from iamai import Context, Plugin, message_handler, ruleset, word_in

   route_rule = (
       ruleset("support-router")
       .when("bug", word_in("bug", "error").with_payload(kind="bug"), priority=10)
       .when("question", word_in("how", "why").with_payload(kind="question"), priority=20)
   )


   class SupportPlugin(Plugin):
       name = "support"

       @message_handler(rule=route_rule.as_rule())
       async def route(self, ctx: Context, kind: str) -> None:
           await ctx.reply(f"ticket kind: {kind}")

规则 payload 会进入 ``ctx.matches``，并参与依赖注入。上面的 ``role`` 和 ``kind`` 参数都来自规则。
完整规则清单见 :doc:`../reference/rules`。

配置模型
--------

插件可以声明 Pydantic 配置模型：

.. code-block:: python

   from pydantic import BaseModel, Field

   from iamai import Context, Plugin, command


   class GreetingConfig(BaseModel):
       greeting: str = Field(default="hello", min_length=1)


   class GreetingPlugin(Plugin):
       name = "greeting"
       config_model = GreetingConfig

       @command("hello")
       async def hello(self, ctx: Context) -> None:
           config = self.config_obj
           await ctx.reply(f"{config.greeting}, {ctx.event.user_id or 'user'}")

这样做有三个直接收益：启动前验证、``config-schema`` 自动导出、API 文档能展示配置结构。

运行时内省
----------

插件可以通过 ``self.runtime`` 或 ``ctx.runtime`` 查看当前运行时已经加载的扩展：

.. code-block:: python

   class InspectorPlugin(Plugin):
       async def startup(self) -> None:
           plugins = self.runtime.list_plugins()
           handlers = self.runtime.list_handlers()

``list_plugins()`` 返回已加载插件的名称、依赖、加载顺序、配置模型和来源。``list_handlers()``
返回 JSON 友好的 handler 元数据，包括所属插件、函数名、类型、命令名、匹配条件、优先级和是否阻断。

如果插件需要访问真实的已绑定回调，可以使用 ``self.runtime.iter_handlers()``。它返回
``BoundHandler`` 对象，包含 ``plugin``、``spec`` 和 ``callback``，顺序与运行时调度顺序一致。

插件依赖与加载顺序
------------------

可用字段包括：

``requires``
   强依赖。缺失时启动失败。

``optional_requires``
   可选依赖。存在时会影响加载顺序，缺失时不报错。

``load_after`` / ``load_before``
   相对加载顺序，适合协调 middleware 或共享状态初始化。

``priority``
   同层级排序权重，数值越小越靠前。

如果插件必须依赖另一个插件的运行时副作用，优先把它表达成显式依赖，而不是假设文件扫描顺序。

状态范围
--------

默认 ``state_scope = "memory"``。需要跨重启保存时，声明：

.. code-block:: python

   class CounterPlugin(Plugin):
       name = "counter"
       state_scope = "persistent"

插件状态适合保存本插件的数据。跨插件共享数据应谨慎使用 ``ctx.shared_state``，并在文档或代码
注释里说明所有者。

插件开发检查清单
----------------

- 每个公开插件都有稳定 ``name`` 和简短 ``description``。
- 配置使用 ``config_model``，不要在 handler 里手写散乱校验。
- handler 参数有类型注解，常见参数使用 ``Context``、``Event``、``Message``。
- 可发布插件包使用 ``[project.entry-points."iamai.plugins"]`` 暴露入口。
- 插件自己的第三方依赖写在包的 ``project.dependencies``。
- 依赖其他 iamai 插件时，用 ``requires``、``optional_requires``、``load_after`` 或 ``load_before`` 表达。
- reload 后不会残留后台任务、文件句柄或未关闭连接。
- 持久化状态只保存 JSON 友好的数据结构。

发布为 uv 可安装插件
-------------------------

插件可以作为普通 Python 包发布。使用者通过 ``uv add iamai-plugin-xxx`` 安装后，既可以显式启用：

.. code-block:: toml

   [runtime]
   plugins = ["echo"]

也可以在受控环境里开启自动发现：

.. code-block:: toml

   [runtime]
   auto_discover_plugins = true

插件包需要在 ``pyproject.toml`` 中声明 entry point：

.. code-block:: toml

   [project.entry-points."iamai.plugins"]
   echo = "iamai_plugin_echo:EchoPlugin"

完整发布规范见 :doc:`../reference/extensions`。
