# iamai.adapter.gensokyo.exceptions

GSK 适配器异常。

## _class_ `GSKException` {#GSKException}

Bases: `iamai.exceptions.AdapterException`

GSK 异常基类。

### _method_ `__init__(self, /, *args, **kwargs)` {#Exception.\_\_init\_\_}

Initialize self.  See help(type(self)) for accurate signature.

- **Arguments**

  - **args**

  - **kwargs**

## _class_ `NetworkError` {#NetworkError}

Bases: `iamai.adapter.gensokyo.exceptions.GSKException`

网络异常。

### _method_ `__init__(self, /, *args, **kwargs)` {#Exception.\_\_init\_\_}

Initialize self.  See help(type(self)) for accurate signature.

- **Arguments**

  - **args**

  - **kwargs**

## _class_ `ActionFailed` {#ActionFailed}

Bases: `iamai.adapter.gensokyo.exceptions.GSKException`

API 请求成功响应，但响应表示 API 操作失败。

### _method_ `__init__(self, resp)` {#ActionFailed.\_\_init\_\_}

初始化。

- **Arguments**

  - **resp** (_Dict\[str, Any\]_) - 返回的响应。

- **Returns**

  Type: _None_

## _class_ `ApiNotAvailable` {#ApiNotAvailable}

Bases: `iamai.adapter.gensokyo.exceptions.ActionFailed`

API 请求返回 404，表示当前请求的 API 不可用或不存在。

- **Attributes**

  - **ERROR\_CODE** (_ClassVar\[int\]_)

### _method_ `__init__(self, resp)` {#ActionFailed.\_\_init\_\_}

初始化。

- **Arguments**

  - **resp** (_Dict\[str, Any\]_) - 返回的响应。

- **Returns**

  Type: _None_

## _class_ `ApiTimeout` {#ApiTimeout}

Bases: `iamai.adapter.gensokyo.exceptions.GSKException`

API 请求响应超时。

### _method_ `__init__(self, /, *args, **kwargs)` {#Exception.\_\_init\_\_}

Initialize self.  See help(type(self)) for accurate signature.

- **Arguments**

  - **args**

  - **kwargs**
