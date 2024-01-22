# iamai.adapter.kook

Kook 协议适配器。

本适配器适配了 Kook 协议。
协议详情请参考: [Kook 开发者平台](https://developer.kookapp.cn/) 。

## _class_ `KookAdapter` {#KookAdapter}

Bases: `iamai.adapter.utils.WebSocketAdapter`

Kook 协议适配器。

- **Attributes**

  - **name** (_str_)

### _class_ `Config` {#Config}

Bases: `iamai.config.ConfigModel`

Kook 配置类，将在适配器被加载时被混入到机器人主配置中。

- **Attributes**

  - **adapter\_type** (_Literal\['ws', 'wb'\]_) - 适配器类型，需要和协议端配置相同。

  - **reconnect\_interval** (_int_) - 重连等待时间。

  - **api\_timeout** (_int_) - 进行 API 调用时等待返回响应的超时时间。

  - **access\_token** (_str_) - 鉴权。

  - **compress** (_Literal\[0, 1\]_) - 是否启用压缩，默认为 0，不启用。

  - **show\_raw** (_bool_) - 是否显示原始数据，默认为 False，不显示。

  - **report\_self\_message** (_bool_)

#### _method_ `__init__(__pydantic_self__, **data)` {#BaseModel.\_\_init\_\_}

Create a new model by parsing and validating input data from keyword arguments.

Raises [`ValidationError`][pydantic_core.ValidationError] if the input data cannot be
validated to form a valid model.

`__init__` uses `__pydantic_self__` instead of the more common `self` for the first arg to
allow `self` as a field name.

- **Arguments**

  - **data** (_Any_)

- **Returns**

  Type: _None_

### _method_ `__init__(self, bot)` {#Adapter.\_\_init\_\_}

初始化。

- **Arguments**

  - **bot** (_Bot_) - 当前机器人对象。

- **Returns**

  Type: _None_

### _async method_ `call_api(self, api, **data)` {#KookAdapter.call\_api}

- **Arguments**

  - **api** (_str_)

  - **data** (_dict_)

- **Returns**

  Type: _Any_

### _async method_ `handle_kook_event(self, data)` {#KookAdapter.handle\_kook\_event}

处理 kook 事件。

- **Arguments**

  - **data** (_Dict\[str, Any\]_)

  - **msg** - 接收到的信息。

### _async method_ `handle_websocket_msg(self, msg)` {#KookAdapter.handle\_websocket\_msg}

处理 WebSocket 消息。

- **Arguments**

  - **msg** (_aiohttp.http\_websocket.WSMessage_)

### _async method_ `send(self, message_, message_type, id_)` {#KookAdapter.send}

发送消息，调用 message/create 或 direct-message/create API 发送消息。

- **Arguments**

  - **message\_** (_T\_KookMSG_) - 消息内容，可以是 str, Mapping, Iterable[Mapping],
  'KookMessageSegment', 'KookMessage'。
  将使用 `KookMessage` 进行封装。

  - **message\_type** (_Literal\['GROUP', 'PERSON'\]_) - 消息类型。应该是 GROUP 或者 PERSON。

  - **id\_** (_int_) - 发送对象的 ID ，Kook 用户码或者Kook频道码。

- **Returns**

  Type: _Dict\[str, Any\]_

  API 响应。

- **Raises**

  - **TypeError** - message_type 不是 'PERSON' 或 'GROUP'。

  - **...** - 同 `call_api()` 方法。

### _async method_ `start_heartbeat(self, session)` {#KookAdapter.start\_heartbeat}

每30s一次心跳

- **Arguments**

  - **session** (_str_)

- **Returns**

  Type: _None_

### _async method_ `startup(self)` {#KookAdapter.startup}

初始化适配器。

### _async method_ `websocket_connect(self)` {#KookAdapter.websocket\_connect}

创建正向 WebSocket 连接。
