适配器
======

Adapter 是 iamai 的协议边界。它应该处理网络、鉴权、协议格式、payload 归一化和发送动作；
插件不应该直接承担这些职责。

内置适配器
----------

``TerminalAdapter``
   本地开发和演示。它把终端输入转换成 message event，把回复打印到 stdout。

``OneBot11Adapter``
   对接 OneBot11。支持 websocket 主动连接、反向 websocket 监听和 HTTP webhook 模式。

``TelegramAdapter``
   对接 Telegram Runtime API。使用 ``getUpdates`` 长轮询接收消息，使用 ``sendMessage`` 回复。

``WebhookAdapter``
   通用 HTTP webhook 入口。适合内部系统、GitHub、Stripe 或其他能发送 JSON 事件的平台。

Terminal 配置
-------------

.. code-block:: toml

   [runtime]
   adapters = ["terminal"]

   [adapter.terminal]
   prompt = "iamai> "
   output_prefix = "runtime> "

终端模式不代表玩具模式。它非常适合做插件回归测试和文档教程，因为没有外部平台变量。

OneBot11 模式
-------------

主动 websocket：

.. code-block:: toml

   [adapter.onebot11]
   mode = "ws"
   url = "ws://127.0.0.1:3001"
   access_token = "change-me"

反向 websocket：

.. code-block:: toml

   [adapter.onebot11]
   mode = "ws-reverse"
   host = "127.0.0.1"
   port = 6700
   access_token = "change-me"

HTTP webhook：

.. code-block:: toml

   [adapter.onebot11]
   mode = "http"
   host = "127.0.0.1"
   port = 6701
   path = "/onebot11"
   api_url = "http://127.0.0.1:5700"
   access_token = "change-me"

对外监听时，``ws-reverse`` 和 ``http`` 都应配置 ``access_token``，并尽量放在反向代理或内网边界后。

Telegram 长轮询
---------------

.. code-block:: toml

   [runtime]
   adapters = ["telegram"]

   [adapter.telegram]
   token = "123456:replace-me"
   poll_timeout = 30
   allowed_updates = ["message"]

``TelegramAdapter`` 不监听本地端口，适合本地开发和无法配置公网 webhook 的部署环境。它会把 Telegram
``message`` update 转成 iamai 的 ``message`` event，并把 ``chat.id`` 映射到 ``channel_id``。

Webhook 签名
------------

通用 HMAC：

.. code-block:: toml

   [adapter.webhook]
   signature_provider = "generic"
   signature_secret = "change-me"
   signature_header = "x-iamai-signature"
   signature_prefix = "sha256="
   timestamp_header = "x-iamai-timestamp"

GitHub：

.. code-block:: toml

   [adapter.webhook]
   signature_provider = "github"
   signature_secret = "github-webhook-secret"

Stripe：

.. code-block:: toml

   [adapter.webhook]
   signature_provider = "stripe"
   signature_secret = "stripe-webhook-secret"
   timestamp_tolerance_seconds = 300

出站回复
--------

``WebhookAdapter`` 支持把回复 POST 到 ``reply_url``。因为 ``reply_url`` 可能来自外部事件，
默认策略会拒绝 private/loopback 地址、非 HTTPS 地址和重定向。

生产配置应明确：

.. code-block:: toml

   [adapter.webhook]
   allow_event_reply_url = false
   reply_url_allowlist = ["hooks.example.com"]
   allowed_reply_schemes = ["https"]

自定义适配器
------------

旧式自定义适配器仍然可以直接继承 ``Adapter``，实现 ``start`` 和 ``send_message``。复杂平台可以再实现
``call_api``。适配器应尽早把平台 payload 转成 ``Event``，不要把平台 SDK 对象泄漏给插件。

新的 JSON 协议适配器建议使用 ``iamai.adapters.middleware`` 中的适配器中间件。中间件负责 HTTP/WS
网络循环、JSON 解析、鉴权、重连、pending echo 和响应封装；协议作者只需要声明字段映射，必要时覆盖少量
平台动作编码 hook。

最小 HTTP webhook 适配器示例：

.. code-block:: python

   from typing import Any

   from iamai import Event, Message
   from iamai.adapters.middleware import EventFieldMap, JsonHttpWebhookMiddleware, OutboundAction


   class AcmeWebhookAdapter(JsonHttpWebhookMiddleware):
       name = "acme"
       platform = "acme"
       field_map = EventFieldMap(
           type="event.type",
           user_id="sender.id",
           channel_id="conversation.id",
           message="message.text",
       )

       def encode_message(
           self,
           message: Message,
           *,
           event: Event | None = None,
           target: Any | None = None,
       ) -> OutboundAction:
           conversation_id = target or (event.channel_id if event else None)
           if conversation_id is None:
               raise ValueError("conversation id is required")
           return OutboundAction(
               kind="message",
               action="messages.send",
               params={"conversation_id": conversation_id, "text": message.plain_text()},
           )

继承链可以像宏包/类一样分层：先写协议通用映射，再让平台变体只覆盖差异字段或动作编码。例如父类定义
``message="message"``，子类只把 ``channel_id`` 改成 ``group.id``，其他字段会继续复用父类约定。

编写适配器的检查清单
--------------------

一个可维护的适配器至少要回答这些问题：

- ``start`` 如何接收事件，是否需要重连、超时、offset 或 pending echo。
- ``close`` 如何停止后台循环并释放连接。
- inbound payload 如何尽早转成 ``Event``，平台原始数据只放在 ``event.raw``。
- ``send_message`` 如何从 ``event`` 或显式 ``target`` 解析目标。
- ``call_api`` 是否暴露平台通用 API，并如何处理失败响应。
- 配置是否加入 ``config.py`` 校验，敏感字段名是否能被 redaction 识别。
- 是否需要注册为内置适配器，或者让用户用导入路径加载。
- 可发布适配器包使用 ``[project.entry-points."iamai.adapters"]`` 暴露入口。

如果协议是 JSON HTTP/WS，优先继承 ``iamai.adapters.middleware`` 的中间件；如果协议有特殊拉取循环，
可以直接继承 ``Adapter``。``TelegramAdapter`` 就是直接继承 ``Adapter`` 的例子，因为它的核心是
Runtime API 长轮询，而不是 webhook server。

发布为 uv 可安装适配器
---------------------------

适配器可以作为普通 Python 包发布。使用者安装：

.. code-block:: console

   uv add iamai-adapter-acme

包内 ``pyproject.toml`` 声明：

.. code-block:: toml

   [project.entry-points."iamai.adapters"]
   acme = "iamai_adapter_acme:AcmeAdapter"

使用者显式启用：

.. code-block:: toml

   [runtime]
   adapters = ["acme"]

   [adapter.acme]
   token = "replace-me"

也可以开启 ``auto_discover_adapters = true`` 自动加载环境里的适配器 entry points。适配器通常携带网络
凭据和外部暴露面，生产环境更建议显式列出。完整发布规范见 :doc:`../reference/extensions`。

Conformance tests
-----------------

第三方适配器包应在自己的测试里使用 ``iamai.testing.adapters``。这些 helper 不替代平台协议测试，
但能固定 iamai runtime 需要的最低契约：

.. code-block:: python

   from iamai.testing.adapters import (
       assert_adapter_api_result,
       assert_adapter_can_close,
       assert_adapter_event,
       assert_adapter_send_result,
   )

   assert_adapter_event(event, adapter="acme")
   assert_adapter_send_result(await adapter.send_message(message, target=target))
   assert_adapter_api_result(await adapter.call_api("get_status"))
   await assert_adapter_can_close(adapter)
