# iamai.adapter.kook.exceptions

Kook 适配器异常。

## _class_ `KookException` {#KookException}

Bases: `iamai.exceptions.AdapterException`

Kook 异常基类。

### _method_ `__init__(self, /, *args, **kwargs)` {#Exception.\_\_init\_\_}

Initialize self.  See help(type(self)) for accurate signature.

- **Arguments**

  - **args**

  - **kwargs**

## _class_ `NetworkError` {#NetworkError}

Bases: `iamai.adapter.kook.exceptions.KookException`

网络异常。

### _method_ `__init__(self, /, *args, **kwargs)` {#Exception.\_\_init\_\_}

Initialize self.  See help(type(self)) for accurate signature.

- **Arguments**

  - **args**

  - **kwargs**

## _class_ `ActionFailed` {#ActionFailed}

Bases: `iamai.adapter.kook.exceptions.KookException`

API 请求成功响应，但响应表示 API 操作失败。

### _method_ `__init__(self, resp)` {#ActionFailed.\_\_init\_\_}

Args:

resp: 返回的响应。

- **Arguments**

  - **resp**

## _class_ `ApiNotAvailable` {#ApiNotAvailable}

Bases: `iamai.adapter.kook.exceptions.ActionFailed`

API 请求返回 404，表示当前请求的 API 不可用或不存在。

### _method_ `__init__(self, resp)` {#ActionFailed.\_\_init\_\_}

Args:

resp: 返回的响应。

- **Arguments**

  - **resp**

## _class_ `ApiTimeout` {#ApiTimeout}

Bases: `iamai.adapter.kook.exceptions.KookException`

API 请求响应超时。

### _method_ `__init__(self, /, *args, **kwargs)` {#Exception.\_\_init\_\_}

Initialize self.  See help(type(self)) for accurate signature.

- **Arguments**

  - **args**

  - **kwargs**

## _class_ `UnauthorizedException` {#UnauthorizedException}

Bases: `iamai.adapter.kook.exceptions.KookException`

Kook 异常基类。

### _method_ `__init__(self, /, *args, **kwargs)` {#Exception.\_\_init\_\_}

Initialize self.  See help(type(self)) for accurate signature.

- **Arguments**

  - **args**

  - **kwargs**

## _class_ `RateLimitException` {#RateLimitException}

Bases: `iamai.adapter.kook.exceptions.KookException`

Kook 异常基类。

### _method_ `__init__(self, /, *args, **kwargs)` {#Exception.\_\_init\_\_}

Initialize self.  See help(type(self)) for accurate signature.

- **Arguments**

  - **args**

  - **kwargs**

## _class_ `UnsupportedMessageType` {#UnsupportedMessageType}

Bases: `iamai.adapter.kook.exceptions.KookException`

### _method_ `__init__(self, message = '')` {#UnsupportedMessageType.\_\_init\_\_}

Initialize self.  See help(type(self)) for accurate signature.

- **Arguments**

  - **message** (_str_)

## _class_ `UnsupportedMessageOperation` {#UnsupportedMessageOperation}

Bases: `iamai.adapter.kook.exceptions.KookException`

### _method_ `__init__(self, message = '')` {#UnsupportedMessageOperation.\_\_init\_\_}

Initialize self.  See help(type(self)) for accurate signature.

- **Arguments**

  - **message** (_str_)

## _class_ `ReconnectError` {#ReconnectError}

Bases: `iamai.adapter.kook.exceptions.KookException`

### _method_ `__init__(self, /, *args, **kwargs)` {#Exception.\_\_init\_\_}

Initialize self.  See help(type(self)) for accurate signature.

- **Arguments**

  - **args**

  - **kwargs**

## _class_ `TokenError` {#TokenError}

Bases: `iamai.adapter.kook.exceptions.KookException`

### _method_ `__init__(self, msg = None)` {#TokenError.\_\_init\_\_}

Initialize self.  See help(type(self)) for accurate signature.

- **Arguments**

  - **msg** (_Optional\[str\]_)
