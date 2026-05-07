第五步：编写一个可用适配器
============================

前几章都在写插件。插件只关心 ``Event``、``Context`` 和 ``Message``，不应该知道外部平台怎么鉴权、
怎么拉消息、怎么发 API 请求。适配器就是这层协议边界。

这一章用内置 ``TelegramAdapter`` 作为完整例子。它是真正可运行的适配器：通过 Telegram Runtime API
``getUpdates`` 长轮询接收消息，通过 ``sendMessage`` 发送回复。

配置入口
--------

先给 Runtime 加一个适配器配置：

.. code-block:: toml

   [runtime]
   adapters = ["telegram"]

   [adapter.telegram]
   token = "123456:replace-me"
   poll_timeout = 30
   allowed_updates = ["message"]

对应的配置模型放在 ``iamai.config``。这样做的目的不是形式主义，而是让启动前校验、管理命令和
配置参考都能看到同一份结构：

.. code-block:: python

   class TelegramConfigModel(BaseModel):
       token: str = ""
       api_base_url: str = "https://api.telegram.org"
       poll_timeout: int = 30
       request_timeout: float = 40.0
       reconnect_interval: float = 3.0
       limit: int = 100
       allowed_updates: list[str] = Field(default_factory=lambda: ["message"])

内置适配器还需要加入 ``BUILTIN_ADAPTERS``，这样用户可以写 ``adapters = ["telegram"]``。第三方适配器
也可以不注册内置名，直接在配置里写导入路径，例如 ``"my_pkg.telegram:TelegramAdapter"``。

适配器骨架
----------

适配器至少实现 ``start`` 和 ``send_message``，通常也会实现 ``close`` 和 ``call_api``：

.. code-block:: python

   from iamai import Adapter, Event, Message


   class TelegramAdapter(Adapter):
       name = "telegram"

       async def start(self) -> None:
           ...

       async def close(self) -> None:
           ...

       async def send_message(
           self,
           message: Message,
           *,
           event: Event | None = None,
           target: object | None = None,
       ) -> object:
           ...

``name`` 必须稳定。它会用于配置表 ``[adapter.telegram]``、运行时指标、审计日志和 ``event.adapter``。

接收循环
--------

Telegram 长轮询的核心是 ``getUpdates``。适配器维护 ``offset``，每处理一个 update 就把 offset 推进，
避免重启前后重复消费同一批消息。

.. code-block:: python

   async def start(self) -> None:
       while not self._closed.is_set():
           try:
               updates = await self._get_updates()
               for update in updates:
                   self._offset = update["update_id"] + 1
                   event = self._normalize_update(update)
                   if event is not None:
                       await self.emit(event)
           except Exception:
               await asyncio.sleep(self.reconnect_interval)

生产适配器必须处理失败：网络错误、平台超时、无效 payload、重复 update、关闭信号。不要让一次失败退出
整个 Runtime，除非这是明确的配置错误，例如 token 缺失。

事件归一化
----------

平台 payload 要尽早变成 iamai 的 ``Event``。Telegram 的关键字段映射是：

- ``message.text`` 或 ``message.caption`` -> ``Message``。
- ``message.from.id`` -> ``user_id``。
- ``message.chat.id`` -> ``channel_id``。
- 群组和频道的 ``chat.id`` -> ``guild_id``。
- 原始 update -> ``event.raw``。

.. code-block:: python

   def _normalize_update(self, update: Mapping[str, Any]) -> Event | None:
       message = update.get("message")
       if not isinstance(message, Mapping):
           return None
       chat = message.get("chat")
       if not isinstance(chat, Mapping):
           return None
       return Event(
           id=str(message.get("message_id") or update.get("update_id")),
           adapter=self.name,
           platform="telegram",
           type="message",
           detail_type=str(chat.get("type", "private")),
           channel_id=str(chat["id"]),
           message=Message(str(message.get("text") or "")),
           raw=dict(update),
       )

这个边界很重要：插件应该看到稳定的 ``Event``，而不是到处读 ``update["message"]["chat"]["id"]``。
平台差异留在适配器里。

发送消息和 API
--------------

``send_message`` 要支持两种调用方式：

- ``ctx.reply("pong")``：通过当前 ``event`` 推断目标。
- ``ctx.send("pong", target=12345)``：显式指定平台目标。

Telegram 的实现最终调用 ``sendMessage``：

.. code-block:: python

   async def send_message(self, message: Message, *, event=None, target=None):
       chat_id = self._resolve_chat_id(event=event, target=target)
       return await self.call_api(
           "sendMessage",
           chat_id=chat_id,
           text=Message.ensure(message).plain_text(),
       )

``call_api`` 是适配器给高级插件留下的平台逃生口。它应该处理平台失败响应，并返回平台 result：

.. code-block:: python

   async def call_api(self, action: str, **params: Any) -> Any:
       response = await request_json(self._method_url(action), json_body=params)
       if not response["ok"]:
           raise RuntimeError(response.get("description", "request failed"))
       return response.get("result")

测试适配器
----------

适配器测试不应该真的访问 Telegram。把 HTTP helper monkeypatch 掉，就能验证参数和错误处理：

.. code-block:: python

   async def fake_request_json(url: str, **kwargs):
       return {"ok": True, "result": {"message_id": 1}}

   monkeypatch.setattr("iamai.adapters.telegram.request_json", fake_request_json)

再单独测试 ``_normalize_update``，确保字段映射不会回退：

.. code-block:: python

   event = adapter._normalize_update({
       "update_id": 10,
       "message": {
           "message_id": 20,
           "from": {"id": 30},
           "chat": {"id": -40, "type": "group"},
           "text": "hello",
       },
   })

   assert event.channel_id == "-40"
   assert event.text == "hello"

Checkpoint
----------

写适配器时按这个顺序自查：

- 配置能被 ``load_config`` 校验，敏感字段会被 redaction。
- ``start`` 能持续接收事件，失败后能重试，``close`` 能停下来。
- inbound payload 会变成稳定 ``Event``，原始数据只放在 ``raw``。
- ``send_message`` 同时支持 ``event`` 和显式 ``target``。
- ``call_api`` 暴露平台通用能力，并清晰处理失败。
- 不访问真实外部服务也能测试字段映射和出站参数。
