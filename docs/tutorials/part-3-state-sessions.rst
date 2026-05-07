第三步：状态、会话与中间件
===========================

一个 Runtime 开始服务真实用户后，很快会遇到三类需求：记住某个插件的数据、等待用户的下一条消息、
以及在多个 handler 前后执行同一段逻辑。这一章分别对应状态、会话和中间件。

插件状态
--------

插件的 ``ctx.state`` 默认是插件私有的。把 ``state_scope`` 声明为 ``persistent`` 后，
它会配合 ``[state]`` 后端跨重启保存。

.. code-block:: python

   from iamai import Context, Plugin, command


   class CounterPlugin(Plugin):
       name = "counter"
       state_scope = "persistent"

       @command("count")
       async def count(self, ctx: Context) -> None:
           value = int(ctx.state.get("value", 0)) + 1
           ctx.state["value"] = value
           await ctx.reply(f"count={value}")

对应配置可以先用 JSON，部署后再按需要切到 SQLite：

.. code-block:: toml

   [state]
   backend = "json"
   path = "var/state.json"

多轮会话
--------

``wait_for_message`` 会等待同一个会话键下的下一条消息。它适合短流程，例如确认、问卷、
补充参数，不适合长时间业务状态机。

.. code-block:: python

   from iamai import Context, Plugin, command


   class SurveyPlugin(Plugin):
       name = "survey"

       @command("survey")
       async def survey(self, ctx: Context) -> None:
           await ctx.reply("你喜欢的语言是？")
           answer = await ctx.wait_for_message(timeout=30)
           await ctx.reply(f"收到：{answer.text}")

如果超时，handler 会抛出超时异常；生产插件通常应捕获它并给用户一个明确反馈。

中间件
------

中间件适合横切逻辑，例如统一审计、输入规范化、耗时统计或异常兜底。不要把核心业务流程藏进
中间件里，否则 handler 的行为会变得难以阅读。

.. code-block:: python

   from iamai import Context, Plugin, middleware


   class AuditPlugin(Plugin):
       name = "audit"

       @middleware("before")
       async def before(self, ctx: Context) -> None:
           ctx.runtime.count_metric("handler_input_seen", adapter=ctx.event.adapter)

中间件阶段包括 ``before``、``around``、``after`` 和 ``error``。当你只需要一个 handler
自己的前置逻辑时，直接写在 handler 里通常更清楚。

Checkpoint
----------

到这里你应该能区分：

- ``ctx.state`` 用于插件自己的数据；
- ``ctx.shared_state`` 用于确有必要跨插件共享的数据；
- ``wait_for_message`` 用于短时间多轮交互；
- middleware 用于横切能力，而不是业务主流程。
