状态与会话
==========

状态和会话解决两个不同问题。``state`` 保存插件跨事件的数据；``SessionManager`` 等待同一会话
里的下一条消息。把它们混在一起会让代码很难维护。

状态后端
--------

``NullStateStore``
   默认内存模式。适合测试、示例和完全无持久化需求的插件。

``JsonStateStore``
   单文件 JSON 后端。适合开发、小规模部署和容易人工检查的状态。写入时使用临时文件替换，
   避免部分写入导致文件损坏。

``SqliteStateStore``
   SQLite 后端。适合需要更稳定本地持久化的单进程部署。

配置示例：

.. code-block:: toml

   [state]
   backend = "sqlite"
   path = "var/state.sqlite3"

插件状态边界
------------

``ctx.state`` 是插件私有状态，推荐保存 JSON 友好数据：

.. code-block:: python

   from iamai import Context, Plugin, command


   class ProfilePlugin(Plugin):
       name = "profile"
       state_scope = "persistent"

       @command("nickname")
       async def nickname(self, ctx: Context) -> None:
           ctx.state["nickname"] = ctx.args.strip()
           await ctx.reply("saved")

``ctx.shared_state`` 是全局共享状态。只有当多个插件确实需要共享同一份运行时数据时才使用，
并且应在代码注释中说明所有者和数据结构。

会话键
------

``Context.wait_for_message()`` 基于 ``SessionManager``。默认 session key 是：

.. code-block:: text

   adapter:channel:user

这能避免群聊中同频道不同用户共用一个等待槽位。

多轮流程
--------

.. code-block:: python

   from asyncio import TimeoutError

   from iamai import Context, Plugin, command


   class SurveyPlugin(Plugin):
       name = "survey"

       @command("survey")
       async def survey(self, ctx: Context) -> None:
           await ctx.reply("你的昵称是？")
           try:
               answer = await ctx.wait_for_message(timeout=60)
           except TimeoutError:
               await ctx.reply("已超时，请重新开始。")
               return
           ctx.state["nickname"] = answer.text
           await ctx.reply(f"已记录：{answer.text}")

多轮会话适合短流程。长流程更适合显式状态机，并把状态保存到 ``ctx.state``。

排障点
------

- 等不到下一条消息：检查消息是否来自同一 adapter/channel/user。
- 命令被会话消费：默认等待规则会跳过命令前缀开头的消息；自定义 rule 时要保留这个约束。
- 重启后状态丢失：确认插件 ``state_scope = "persistent"``，并配置了非 memory 后端。
