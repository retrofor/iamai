# iamai.adapter.kook.config

Kook 适配器配置。

## _class_ `Config` {#Config}

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

### _method_ `__init__(__pydantic_self__, **data)` {#BaseModel.\_\_init\_\_}

Create a new model by parsing and validating input data from keyword arguments.

Raises [`ValidationError`][pydantic_core.ValidationError] if the input data cannot be
validated to form a valid model.

`__init__` uses `__pydantic_self__` instead of the more common `self` for the first arg to
allow `self` as a field name.

- **Arguments**

  - **data** (_Any_)

- **Returns**

  Type: _None_
