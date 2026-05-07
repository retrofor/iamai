规则参考
========

``Rule`` 决定事件是否进入某个 handler。它应该描述“消息或事件长什么样”，不要承担权限判断；
用户资格、角色和超级用户检查应放在 ``Permission``。

核心模型
--------

规则返回值会被归一化：

``True``
   匹配成功，没有额外 payload。

``False`` 或 ``None``
   不匹配。

``dict``
   匹配成功，并把字典合并进 ``ctx.matches``，也可作为 handler 参数注入。

``(ok, payload)``
   显式返回是否匹配和 payload。

规则可以用 ``&``、``|``、``~`` 组合，也可以用更接近规则引擎写法的别名：

.. code-block:: python

   from iamai import when_all, when_any, none_of, word_in

   deploy_rule = when_all(
       word_in("deploy"),
       none_of(word_in("danger")),
   )

常用规则
--------

事件来源：

- ``adapter_is("onebot11")``
- ``platform_is("qq")``
- ``event_type_is("message")``
- ``detail_type_is("group")``
- ``user_id_is("10001")``
- ``channel_id_is("20001")``
- ``guild_id_is("20001")``

文本：

- ``startswith("hi", "hello")``
- ``endswith("?")``
- ``contains("token", require_all=True)``
- ``text_equals("ping", ignore_case=True)``
- ``word_in("deploy", "rollback")``
- ``regex(r"#(?P<number>\\d+)")``
- ``fullmatch(r"/issue (?P<number>\\d+)")``

字段匹配
--------

``field`` 支持 dotted path，并能从不同来源读取：

``source="event"``
   ``Event`` 属性，例如 ``field("user_id", equals="10001")``。

``source="raw"``
   原始平台 payload，例如 ``raw_field("sender.role", equals="admin")``。

``source="state"``
   当前插件状态，例如 ``state_field("phase", equals="open")``。

``source="shared_state"``
   Runtime 共享状态，例如 ``field("ops.enabled", source="shared_state", equals=True)``。

``source="matches"``
   已捕获的匹配 payload。

``source="context"``
   ``Context`` 对象本身，例如 ``field("event.detail_type", source="context", equals="group")``。

支持的比较包括：

- ``exists=True`` / ``exists=False``
- ``equals=value`` / ``not_equals=value``
- ``in_=[...]``
- ``contains=value``
- ``startswith="..."`` / ``endswith="..."``
- ``regex=r"...(?P<name>...)..."``
- ``gt`` / ``ge`` / ``lt`` / ``le``

``capture_as`` 会把字段值放进 payload：

.. code-block:: python

   from iamai import command, raw_field


   @command("ban", rule=raw_field("sender.role", equals="admin", capture_as="role"))
   async def ban(ctx, role: str) -> None:
       await ctx.reply(f"allowed by {role}")

Ruleset
-------

``Ruleset`` 用来表达一组命名规则。它借鉴规则引擎的 ruleset 思路，但仍然运行在 iamai
现有 handler 规则机制内。

.. code-block:: python

   from iamai import message_handler, raw_field, ruleset, word_in

   router = (
       ruleset("intent-router")
       .when("deploy", word_in("deploy").with_payload(intent="deploy"), priority=10)
       .when("admin", raw_field("sender.role", equals="admin"), priority=20)
   )


   @message_handler(rule=router.as_rule())
   async def route(ctx, intent: str) -> None:
       await ctx.reply(f"intent={intent}")

默认只返回优先级最高的第一个匹配。需要收集全部匹配时：

.. code-block:: python

   @message_handler(rule=router.as_rule(first=False))
   async def route(ctx) -> None:
       names = ", ".join(ctx.matches["ruleset"])
       await ctx.reply(names)

设计建议
--------

- 规则只描述事件形态和业务入口，不描述权限。
- 字段规则优先使用 ``raw_field`` 读取平台差异，避免把平台 payload 传进 handler 主流程。
- 复杂路由优先用 ``Ruleset`` 命名每个分支，便于日志、测试和后续维护。
- 对外部状态、网络请求、数据库查询这类昂贵判断，优先放在依赖注入 provider 或 handler 内部。
