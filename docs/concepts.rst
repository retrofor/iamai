核心概念
========

这一页先解释 iamai 的词汇。理解这些概念后，再读教程和 API 会更顺。

Runtime
---

``Runtime`` 是运行时容器。它负责读取配置、创建适配器、加载插件、管理状态、调度事件、
处理热重载，并向插件提供依赖注入。

Adapter
-------

``Adapter`` 是协议边界。它把外部系统的消息转换成统一的 ``Event``，也负责把
``Message`` 发回外部系统。

适配器应该处理网络、鉴权、协议格式和限流等边界问题；业务逻辑不应该依赖某个平台的
原始 payload。

Event
-----

``Event`` 是框架内部的统一事件模型。插件通常读取这些字段：

- ``event.type``
- ``event.detail_type``
- ``event.user_id``
- ``event.channel_id``
- ``event.text``
- ``event.raw``

``raw`` 仍然保留平台原始数据，但应当作为补充信息，而不是插件的主要依赖。

Message
-------

``Message`` 是协议无关的消息链容器。插件可以从纯文本开始，也可以构造更复杂的 segment。
适配器在发送时再转换成目标协议格式。

Plugin
------

``Plugin`` 是业务模块。一个插件可以声明：

- 命令 handler；
- 普通消息 handler；
- 事件 handler；
- middleware；
- Pydantic 配置模型；
- 持久化状态。

Context
-------

``Context`` 是一次 handler 执行的上下文。它把 ``runtime``、``adapter``、``plugin``、
``event``、匹配结果和快捷方法放在一起。

Rule 与 Permission
------------------

``Rule`` 负责判断事件是否应该进入某个 handler。``Permission`` 负责判断调用者是否有资格
执行该 handler。

``Rule`` 可以组合文本规则、事件字段规则、原始 payload 字段规则和命名 ``Ruleset``。规则成功时
可以返回 payload，这些值会进入 ``ctx.matches`` 并参与依赖注入。``Permission`` 只看“谁能做”，
不要和消息形态判断混在一起。

把这两层拆开会让业务代码更清晰，也让管理命令、群聊权限和平台限制更容易审计。规则细节见
:doc:`reference/rules`。

State 与 Session
----------------

``state`` 用于保存插件状态。``SessionManager`` 用于等待同一会话里的下一条消息。
当前 session key 默认由 ``adapter:channel:user`` 组成，避免群聊中不同用户互相串会话。
