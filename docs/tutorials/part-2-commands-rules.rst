第二步：命令、规则与权限
=========================

上一章的 Runtime 只证明了“能响应”。真实项目还需要回答两个问题：这条消息是否应该进入某个
handler，以及这个用户是否有资格执行它。iamai 用 ``Rule`` 和 ``Permission`` 把这两件事
分开。

命令与普通消息
--------------

``@command`` 适合清晰的入口；``@message_handler`` 适合关键词、正则和普通消息流。

.. code-block:: python

   from iamai import Context, Plugin, command, message_handler, startswith


   class RouterPlugin(Plugin):
       name = "router"

       @command("ping")
       async def ping(self, ctx: Context) -> None:
           await ctx.reply("pong")

       @message_handler(rule=startswith("你好", "hello"))
       async def greet(self, ctx: Context) -> None:
           await ctx.reply("你好。")

命令 handler 会从命令前缀开始匹配；普通消息 handler 不要求命令前缀，更适合自然语言入口。

组合规则
--------

``Rule`` 支持 ``&``、``|`` 和 ``~``。组合规则应该描述“消息形态”，例如平台、事件类型、
文本模式或群聊/私聊。

.. code-block:: python

   from iamai import Context, Plugin, adapter_is, command, group_message


   class GroupPlugin(Plugin):
       name = "group-tools"

       @command("where", rule=adapter_is("onebot11") & group_message())
       async def where(self, ctx: Context) -> None:
           await ctx.reply(f"group={ctx.event.guild_id or ctx.event.channel_id}")

正则规则可以把匹配结果放进依赖注入参数。命名分组会进入 match payload：

.. code-block:: python

   from iamai import Context, Plugin, message_handler, regex


   class IssuePlugin(Plugin):
       name = "issue"

       @message_handler(rule=regex(r"^#(?P<number>\\d+)$"))
       async def issue(self, ctx: Context, number: str) -> None:
           await ctx.reply(f"issue number: {number}")

字段规则
--------

当平台 payload 里有结构化字段时，不要在 handler 里先写一大段 ``if``。可以用 ``field``、
``raw_field`` 和 ``state_field`` 把条件留在入口处：

.. code-block:: python

   from iamai import Context, Plugin, command, raw_field, when_all


   class AdminPlugin(Plugin):
       name = "admin-route"

       @command(
           "audit",
           rule=when_all(
               raw_field("sender.role", equals="admin", capture_as="role"),
               raw_field("message_type", equals="group"),
           ),
       )
       async def audit(self, ctx: Context, role: str) -> None:
           await ctx.reply(f"matched role={role}")

``capture_as`` 会把字段值放进 ``ctx.matches``，也可以像 ``role`` 一样直接作为 handler 参数注入。

Ruleset 路由
------------

当一个 handler 需要先判断多个意图，可以用 ``ruleset`` 写出命名分支。它的写法接近规则引擎：
每个 ``when`` 有名字、规则和优先级，默认只命中优先级最高的第一个分支。

.. code-block:: python

   from iamai import Context, Plugin, message_handler, ruleset, word_in

   intent_router = (
       ruleset("intent")
       .when("deploy", word_in("deploy").with_payload(intent="deploy"), priority=10)
       .when("rollback", word_in("rollback").with_payload(intent="rollback"), priority=20)
   )


   class IntentPlugin(Plugin):
       name = "intent"

       @message_handler(rule=intent_router.as_rule())
       async def route(self, ctx: Context, intent: str) -> None:
           await ctx.reply(f"intent={intent}")

这适合把“可解释的入口路由”放在规则层。真正执行部署、回滚、查数据库这类动作，仍然应该放在
handler 或依赖注入 provider 里。

权限只看资格
------------

``Permission`` 应该描述“谁可以做这件事”。它和规则一样可以组合，但语义不同：

.. code-block:: python

   from iamai import Context, Plugin, command, superusers


   class OpsPlugin(Plugin):
       name = "ops"

       @command("reload", permission=superusers())
       async def reload(self, ctx: Context) -> None:
           await ctx.reload_plugins()
           await ctx.reply("plugins reloaded")

如果把身份判断写成 ``Rule``，后续调试时很难区分“消息没有匹配”和“用户没有权限”。

自定义规则和权限
----------------

普通函数也可以被包装成规则或权限，并且会参与 iamai 的依赖注入：

.. code-block:: python

   from iamai import Context, Plugin, command, permission


   @permission
   async def from_internal_channel(ctx: Context) -> bool:
       return ctx.event.channel_id == "internal"


   class InternalPlugin(Plugin):
       name = "internal"

       @command("report", permission=from_internal_channel)
       async def report(self, ctx: Context) -> None:
           await ctx.reply("internal report")

Checkpoint
----------

到这里你应该能把 handler 的入口拆成三层：命令或消息模式决定候选 handler，``Rule`` 决定
事件是否匹配，``Permission`` 决定调用者是否允许执行。
