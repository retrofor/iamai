# iamai.adapter.kook.api.model

## _class_ `User` {#User}

Bases: `pydantic.main.BaseModel`

开黑啦 User 字段

https://developer.kaiheila.cn/doc/objects

- **Attributes**

  - **id\_** (_Optional\[str\]_)

  - **username** (_Optional\[str\]_)

  - **nickname** (_Optional\[str\]_)

  - **identify\_num** (_Optional\[str\]_)

  - **online** (_Optional\[bool\]_)

  - **bot** (_Optional\[bool\]_)

  - **os** (_Optional\[str\]_)

  - **status** (_Optional\[int\]_)

  - **avatar** (_Optional\[str\]_)

  - **vip\_avatar** (_Optional\[str\]_)

  - **mobile\_verified** (_Optional\[bool\]_)

  - **roles** (_Optional\[List\[int\]\]_)

  - **joined\_at** (_Optional\[int\]_)

  - **active\_time** (_Optional\[int\]_)

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

## _class_ `Role` {#Role}

Bases: `pydantic.main.BaseModel`

角色

- **Attributes**

  - **role\_id** (_Optional\[int\]_)

  - **name** (_Optional\[str\]_)

  - **color** (_Optional\[int\]_)

  - **position** (_Optional\[int\]_)

  - **hoist** (_Optional\[int\]_)

  - **mentionable** (_Optional\[int\]_)

  - **permissions** (_Optional\[int\]_)

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

## _class_ `PermissionOverwrite` {#PermissionOverwrite}

Bases: `pydantic.main.BaseModel`

Usage docs: https://docs.pydantic.dev/2.5/concepts/models/

A base class for creating Pydantic models.

- **Attributes**

  - **role\_id** (_Optional\[int\]_)

  - **allow** (_Optional\[int\]_)

  - **deny** (_Optional\[int\]_)

  - **\_\_class\_vars\_\_** - The names of classvars defined on the model.

  - **\_\_private\_attributes\_\_** - Metadata about the private attributes of the model.

  - **\_\_signature\_\_** - The signature for instantiating the model.

  - **\_\_pydantic\_complete\_\_** - Whether model building is completed, or if there are still undefined fields.

  - **\_\_pydantic\_core\_schema\_\_** - The pydantic-core schema used to build the SchemaValidator and SchemaSerializer.

  - **\_\_pydantic\_custom\_init\_\_** - Whether the model has a custom `__init__` function.

  - **\_\_pydantic\_decorators\_\_** - Metadata containing the decorators defined on the model.
  This replaces `Model.__validators__` and `Model.__root_validators__` from Pydantic V1.

  - **\_\_pydantic\_generic\_metadata\_\_** - Metadata for generic models; contains data used for a similar purpose to
  __args__, __origin__, __parameters__ in typing-module generics. May eventually be replaced by these.

  - **\_\_pydantic\_parent\_namespace\_\_** - Parent namespace of the model, used for automatic rebuilding of models.

  - **\_\_pydantic\_post\_init\_\_** - The name of the post-init method for the model, if defined.

  - **\_\_pydantic\_root\_model\_\_** - Whether the model is a `RootModel`.

  - **\_\_pydantic\_serializer\_\_** - The pydantic-core SchemaSerializer used to dump instances of the model.

  - **\_\_pydantic\_validator\_\_** - The pydantic-core SchemaValidator used to validate instances of the model.

  - **\_\_pydantic\_extra\_\_** - An instance attribute with the values of extra fields from validation when
  `model_config['extra'] == 'allow'`.

  - **\_\_pydantic\_fields\_set\_\_** - An instance attribute with the names of fields explicitly set.

  - **\_\_pydantic\_private\_\_** - Instance attribute with the values of private attributes set on the model instance.

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

## _class_ `PermissionUser` {#PermissionUser}

Bases: `pydantic.main.BaseModel`

Usage docs: https://docs.pydantic.dev/2.5/concepts/models/

A base class for creating Pydantic models.

- **Attributes**

  - **user** (_Optional\[iamai.adapter.kook.api.model.User\]_)

  - **allow** (_Optional\[int\]_)

  - **deny** (_Optional\[int\]_)

  - **\_\_class\_vars\_\_** - The names of classvars defined on the model.

  - **\_\_private\_attributes\_\_** - Metadata about the private attributes of the model.

  - **\_\_signature\_\_** - The signature for instantiating the model.

  - **\_\_pydantic\_complete\_\_** - Whether model building is completed, or if there are still undefined fields.

  - **\_\_pydantic\_core\_schema\_\_** - The pydantic-core schema used to build the SchemaValidator and SchemaSerializer.

  - **\_\_pydantic\_custom\_init\_\_** - Whether the model has a custom `__init__` function.

  - **\_\_pydantic\_decorators\_\_** - Metadata containing the decorators defined on the model.
  This replaces `Model.__validators__` and `Model.__root_validators__` from Pydantic V1.

  - **\_\_pydantic\_generic\_metadata\_\_** - Metadata for generic models; contains data used for a similar purpose to
  __args__, __origin__, __parameters__ in typing-module generics. May eventually be replaced by these.

  - **\_\_pydantic\_parent\_namespace\_\_** - Parent namespace of the model, used for automatic rebuilding of models.

  - **\_\_pydantic\_post\_init\_\_** - The name of the post-init method for the model, if defined.

  - **\_\_pydantic\_root\_model\_\_** - Whether the model is a `RootModel`.

  - **\_\_pydantic\_serializer\_\_** - The pydantic-core SchemaSerializer used to dump instances of the model.

  - **\_\_pydantic\_validator\_\_** - The pydantic-core SchemaValidator used to validate instances of the model.

  - **\_\_pydantic\_extra\_\_** - An instance attribute with the values of extra fields from validation when
  `model_config['extra'] == 'allow'`.

  - **\_\_pydantic\_fields\_set\_\_** - An instance attribute with the names of fields explicitly set.

  - **\_\_pydantic\_private\_\_** - Instance attribute with the values of private attributes set on the model instance.

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

## _class_ `ChannelRoleInfo` {#ChannelRoleInfo}

Bases: `pydantic.main.BaseModel`

频道角色权限详情

- **Attributes**

  - **permission\_overwrites** (_Optional\[List\[iamai.adapter.kook.api.model.PermissionOverwrite\]\]_)

  - **permission\_users** (_Optional\[List\[iamai.adapter.kook.api.model.PermissionUser\]\]_)

  - **permission\_sync** (_Optional\[int\]_)

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

## _class_ `Channel` {#Channel}

Bases: `iamai.adapter.kook.api.model.ChannelRoleInfo`

开黑啦 频道 字段

- **Attributes**

  - **id\_** (_Optional\[str\]_)

  - **name** (_Optional\[str\]_)

  - **user\_id** (_Optional\[str\]_)

  - **master\_id** (_Optional\[str\]_)

  - **guild\_id** (_Optional\[str\]_)

  - **topic** (_Optional\[str\]_)

  - **is\_category** (_Optional\[bool\]_)

  - **parent\_id** (_Optional\[str\]_)

  - **level** (_Optional\[int\]_)

  - **slow\_mode** (_Optional\[int\]_)

  - **type** (_Optional\[int\]_)

  - **has\_password** (_Optional\[bool\]_)

  - **limit\_amount** (_Optional\[int\]_)

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

## _class_ `Guild` {#Guild}

Bases: `pydantic.main.BaseModel`

服务器

- **Attributes**

  - **id\_** (_Optional\[str\]_)

  - **name** (_Optional\[str\]_)

  - **topic** (_Optional\[str\]_)

  - **user\_id** (_Optional\[str\]_)

  - **icon** (_Optional\[str\]_)

  - **notify\_type** (_Optional\[int\]_)

  - **region** (_Optional\[str\]_)

  - **enable\_open** (_Optional\[bool\]_)

  - **open\_id** (_Optional\[str\]_)

  - **default\_channel\_id** (_Optional\[str\]_)

  - **welcome\_channel\_id** (_Optional\[str\]_)

  - **roles** (_Optional\[List\[iamai.adapter.kook.api.model.Role\]\]_)

  - **channels** (_Optional\[List\[iamai.adapter.kook.api.model.Channel\]\]_)

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

## _class_ `Quote` {#Quote}

Bases: `pydantic.main.BaseModel`

引用消息

- **Attributes**

  - **id\_** (_Optional\[str\]_)

  - **type** (_Optional\[int\]_)

  - **content** (_Optional\[str\]_)

  - **create\_at** (_Optional\[int\]_)

  - **author** (_Optional\[iamai.adapter.kook.api.model.User\]_)

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

## _class_ `Attachments` {#Attachments}

Bases: `pydantic.main.BaseModel`

附加的多媒体数据

- **Attributes**

  - **type** (_Optional\[str\]_)

  - **url** (_Optional\[str\]_)

  - **name** (_Optional\[str\]_)

  - **size** (_Optional\[int\]_)

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

## _class_ `Emoji` {#Emoji}

Bases: `pydantic.main.BaseModel`

Usage docs: https://docs.pydantic.dev/2.5/concepts/models/

A base class for creating Pydantic models.

- **Attributes**

  - **id\_** (_Optional\[str\]_)

  - **name** (_Optional\[str\]_)

  - **\_\_class\_vars\_\_** - The names of classvars defined on the model.

  - **\_\_private\_attributes\_\_** - Metadata about the private attributes of the model.

  - **\_\_signature\_\_** - The signature for instantiating the model.

  - **\_\_pydantic\_complete\_\_** - Whether model building is completed, or if there are still undefined fields.

  - **\_\_pydantic\_core\_schema\_\_** - The pydantic-core schema used to build the SchemaValidator and SchemaSerializer.

  - **\_\_pydantic\_custom\_init\_\_** - Whether the model has a custom `__init__` function.

  - **\_\_pydantic\_decorators\_\_** - Metadata containing the decorators defined on the model.
  This replaces `Model.__validators__` and `Model.__root_validators__` from Pydantic V1.

  - **\_\_pydantic\_generic\_metadata\_\_** - Metadata for generic models; contains data used for a similar purpose to
  __args__, __origin__, __parameters__ in typing-module generics. May eventually be replaced by these.

  - **\_\_pydantic\_parent\_namespace\_\_** - Parent namespace of the model, used for automatic rebuilding of models.

  - **\_\_pydantic\_post\_init\_\_** - The name of the post-init method for the model, if defined.

  - **\_\_pydantic\_root\_model\_\_** - Whether the model is a `RootModel`.

  - **\_\_pydantic\_serializer\_\_** - The pydantic-core SchemaSerializer used to dump instances of the model.

  - **\_\_pydantic\_validator\_\_** - The pydantic-core SchemaValidator used to validate instances of the model.

  - **\_\_pydantic\_extra\_\_** - An instance attribute with the values of extra fields from validation when
  `model_config['extra'] == 'allow'`.

  - **\_\_pydantic\_fields\_set\_\_** - An instance attribute with the names of fields explicitly set.

  - **\_\_pydantic\_private\_\_** - Instance attribute with the values of private attributes set on the model instance.

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

## _class_ `URL` {#URL}

Bases: `pydantic.main.BaseModel`

Usage docs: https://docs.pydantic.dev/2.5/concepts/models/

A base class for creating Pydantic models.

- **Attributes**

  - **url** (_Optional\[str\]_)

  - **\_\_class\_vars\_\_** - The names of classvars defined on the model.

  - **\_\_private\_attributes\_\_** - Metadata about the private attributes of the model.

  - **\_\_signature\_\_** - The signature for instantiating the model.

  - **\_\_pydantic\_complete\_\_** - Whether model building is completed, or if there are still undefined fields.

  - **\_\_pydantic\_core\_schema\_\_** - The pydantic-core schema used to build the SchemaValidator and SchemaSerializer.

  - **\_\_pydantic\_custom\_init\_\_** - Whether the model has a custom `__init__` function.

  - **\_\_pydantic\_decorators\_\_** - Metadata containing the decorators defined on the model.
  This replaces `Model.__validators__` and `Model.__root_validators__` from Pydantic V1.

  - **\_\_pydantic\_generic\_metadata\_\_** - Metadata for generic models; contains data used for a similar purpose to
  __args__, __origin__, __parameters__ in typing-module generics. May eventually be replaced by these.

  - **\_\_pydantic\_parent\_namespace\_\_** - Parent namespace of the model, used for automatic rebuilding of models.

  - **\_\_pydantic\_post\_init\_\_** - The name of the post-init method for the model, if defined.

  - **\_\_pydantic\_root\_model\_\_** - Whether the model is a `RootModel`.

  - **\_\_pydantic\_serializer\_\_** - The pydantic-core SchemaSerializer used to dump instances of the model.

  - **\_\_pydantic\_validator\_\_** - The pydantic-core SchemaValidator used to validate instances of the model.

  - **\_\_pydantic\_extra\_\_** - An instance attribute with the values of extra fields from validation when
  `model_config['extra'] == 'allow'`.

  - **\_\_pydantic\_fields\_set\_\_** - An instance attribute with the names of fields explicitly set.

  - **\_\_pydantic\_private\_\_** - Instance attribute with the values of private attributes set on the model instance.

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

## _class_ `Meta` {#Meta}

Bases: `pydantic.main.BaseModel`

Usage docs: https://docs.pydantic.dev/2.5/concepts/models/

A base class for creating Pydantic models.

- **Attributes**

  - **page** (_Optional\[int\]_)

  - **page\_total** (_Optional\[int\]_)

  - **page\_size** (_Optional\[int\]_)

  - **total** (_Optional\[int\]_)

  - **\_\_class\_vars\_\_** - The names of classvars defined on the model.

  - **\_\_private\_attributes\_\_** - Metadata about the private attributes of the model.

  - **\_\_signature\_\_** - The signature for instantiating the model.

  - **\_\_pydantic\_complete\_\_** - Whether model building is completed, or if there are still undefined fields.

  - **\_\_pydantic\_core\_schema\_\_** - The pydantic-core schema used to build the SchemaValidator and SchemaSerializer.

  - **\_\_pydantic\_custom\_init\_\_** - Whether the model has a custom `__init__` function.

  - **\_\_pydantic\_decorators\_\_** - Metadata containing the decorators defined on the model.
  This replaces `Model.__validators__` and `Model.__root_validators__` from Pydantic V1.

  - **\_\_pydantic\_generic\_metadata\_\_** - Metadata for generic models; contains data used for a similar purpose to
  __args__, __origin__, __parameters__ in typing-module generics. May eventually be replaced by these.

  - **\_\_pydantic\_parent\_namespace\_\_** - Parent namespace of the model, used for automatic rebuilding of models.

  - **\_\_pydantic\_post\_init\_\_** - The name of the post-init method for the model, if defined.

  - **\_\_pydantic\_root\_model\_\_** - Whether the model is a `RootModel`.

  - **\_\_pydantic\_serializer\_\_** - The pydantic-core SchemaSerializer used to dump instances of the model.

  - **\_\_pydantic\_validator\_\_** - The pydantic-core SchemaValidator used to validate instances of the model.

  - **\_\_pydantic\_extra\_\_** - An instance attribute with the values of extra fields from validation when
  `model_config['extra'] == 'allow'`.

  - **\_\_pydantic\_fields\_set\_\_** - An instance attribute with the names of fields explicitly set.

  - **\_\_pydantic\_private\_\_** - Instance attribute with the values of private attributes set on the model instance.

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

## _class_ `ListReturn` {#ListReturn}

Bases: `pydantic.main.BaseModel`

Usage docs: https://docs.pydantic.dev/2.5/concepts/models/

A base class for creating Pydantic models.

- **Attributes**

  - **meta** (_Optional\[iamai.adapter.kook.api.model.Meta\]_)

  - **sort** (_Optional\[Dict\[str, Any\]\]_)

  - **\_\_class\_vars\_\_** - The names of classvars defined on the model.

  - **\_\_private\_attributes\_\_** - Metadata about the private attributes of the model.

  - **\_\_signature\_\_** - The signature for instantiating the model.

  - **\_\_pydantic\_complete\_\_** - Whether model building is completed, or if there are still undefined fields.

  - **\_\_pydantic\_core\_schema\_\_** - The pydantic-core schema used to build the SchemaValidator and SchemaSerializer.

  - **\_\_pydantic\_custom\_init\_\_** - Whether the model has a custom `__init__` function.

  - **\_\_pydantic\_decorators\_\_** - Metadata containing the decorators defined on the model.
  This replaces `Model.__validators__` and `Model.__root_validators__` from Pydantic V1.

  - **\_\_pydantic\_generic\_metadata\_\_** - Metadata for generic models; contains data used for a similar purpose to
  __args__, __origin__, __parameters__ in typing-module generics. May eventually be replaced by these.

  - **\_\_pydantic\_parent\_namespace\_\_** - Parent namespace of the model, used for automatic rebuilding of models.

  - **\_\_pydantic\_post\_init\_\_** - The name of the post-init method for the model, if defined.

  - **\_\_pydantic\_root\_model\_\_** - Whether the model is a `RootModel`.

  - **\_\_pydantic\_serializer\_\_** - The pydantic-core SchemaSerializer used to dump instances of the model.

  - **\_\_pydantic\_validator\_\_** - The pydantic-core SchemaValidator used to validate instances of the model.

  - **\_\_pydantic\_extra\_\_** - An instance attribute with the values of extra fields from validation when
  `model_config['extra'] == 'allow'`.

  - **\_\_pydantic\_fields\_set\_\_** - An instance attribute with the names of fields explicitly set.

  - **\_\_pydantic\_private\_\_** - Instance attribute with the values of private attributes set on the model instance.

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

## _class_ `BlackList` {#BlackList}

Bases: `pydantic.main.BaseModel`

黑名单

- **Attributes**

  - **user\_id** (_Optional\[str\]_)

  - **created\_time** (_Optional\[int\]_)

  - **remark** (_Optional\[str\]_)

  - **user** (_Optional\[iamai.adapter.kook.api.model.User\]_)

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

## _class_ `BlackListsReturn` {#BlackListsReturn}

Bases: `iamai.adapter.kook.api.model.ListReturn`

获取黑名单列表返回信息

- **Attributes**

  - **blacklists** (_Optional\[List\[iamai.adapter.kook.api.model.BlackList\]\]_)

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

## _class_ `MessageCreateReturn` {#MessageCreateReturn}

Bases: `pydantic.main.BaseModel`

发送频道消息返回信息

- **Attributes**

  - **msg\_id** (_Optional\[str\]_)

  - **msg\_timestamp** (_Optional\[int\]_)

  - **nonce** (_Optional\[str\]_)

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

## _class_ `ChannelRoleReturn` {#ChannelRoleReturn}

Bases: `pydantic.main.BaseModel`

创建或更新频道角色权限返回信息

- **Attributes**

  - **role\_id** (_Optional\[int\]_)

  - **user\_id** (_Optional\[str\]_)

  - **allow** (_Optional\[int\]_)

  - **deny** (_Optional\[int\]_)

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

## _class_ `GuildsReturn` {#GuildsReturn}

Bases: `iamai.adapter.kook.api.model.ListReturn`

Usage docs: https://docs.pydantic.dev/2.5/concepts/models/

A base class for creating Pydantic models.

- **Attributes**

  - **guilds** (_Optional\[List\[iamai.adapter.kook.api.model.Guild\]\]_)

  - **\_\_class\_vars\_\_** - The names of classvars defined on the model.

  - **\_\_private\_attributes\_\_** - Metadata about the private attributes of the model.

  - **\_\_signature\_\_** - The signature for instantiating the model.

  - **\_\_pydantic\_complete\_\_** - Whether model building is completed, or if there are still undefined fields.

  - **\_\_pydantic\_core\_schema\_\_** - The pydantic-core schema used to build the SchemaValidator and SchemaSerializer.

  - **\_\_pydantic\_custom\_init\_\_** - Whether the model has a custom `__init__` function.

  - **\_\_pydantic\_decorators\_\_** - Metadata containing the decorators defined on the model.
  This replaces `Model.__validators__` and `Model.__root_validators__` from Pydantic V1.

  - **\_\_pydantic\_generic\_metadata\_\_** - Metadata for generic models; contains data used for a similar purpose to
  __args__, __origin__, __parameters__ in typing-module generics. May eventually be replaced by these.

  - **\_\_pydantic\_parent\_namespace\_\_** - Parent namespace of the model, used for automatic rebuilding of models.

  - **\_\_pydantic\_post\_init\_\_** - The name of the post-init method for the model, if defined.

  - **\_\_pydantic\_root\_model\_\_** - Whether the model is a `RootModel`.

  - **\_\_pydantic\_serializer\_\_** - The pydantic-core SchemaSerializer used to dump instances of the model.

  - **\_\_pydantic\_validator\_\_** - The pydantic-core SchemaValidator used to validate instances of the model.

  - **\_\_pydantic\_extra\_\_** - An instance attribute with the values of extra fields from validation when
  `model_config['extra'] == 'allow'`.

  - **\_\_pydantic\_fields\_set\_\_** - An instance attribute with the names of fields explicitly set.

  - **\_\_pydantic\_private\_\_** - Instance attribute with the values of private attributes set on the model instance.

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

## _class_ `ChannelsReturn` {#ChannelsReturn}

Bases: `iamai.adapter.kook.api.model.ListReturn`

Usage docs: https://docs.pydantic.dev/2.5/concepts/models/

A base class for creating Pydantic models.

- **Attributes**

  - **channels** (_Optional\[List\[iamai.adapter.kook.api.model.Channel\]\]_)

  - **\_\_class\_vars\_\_** - The names of classvars defined on the model.

  - **\_\_private\_attributes\_\_** - Metadata about the private attributes of the model.

  - **\_\_signature\_\_** - The signature for instantiating the model.

  - **\_\_pydantic\_complete\_\_** - Whether model building is completed, or if there are still undefined fields.

  - **\_\_pydantic\_core\_schema\_\_** - The pydantic-core schema used to build the SchemaValidator and SchemaSerializer.

  - **\_\_pydantic\_custom\_init\_\_** - Whether the model has a custom `__init__` function.

  - **\_\_pydantic\_decorators\_\_** - Metadata containing the decorators defined on the model.
  This replaces `Model.__validators__` and `Model.__root_validators__` from Pydantic V1.

  - **\_\_pydantic\_generic\_metadata\_\_** - Metadata for generic models; contains data used for a similar purpose to
  __args__, __origin__, __parameters__ in typing-module generics. May eventually be replaced by these.

  - **\_\_pydantic\_parent\_namespace\_\_** - Parent namespace of the model, used for automatic rebuilding of models.

  - **\_\_pydantic\_post\_init\_\_** - The name of the post-init method for the model, if defined.

  - **\_\_pydantic\_root\_model\_\_** - Whether the model is a `RootModel`.

  - **\_\_pydantic\_serializer\_\_** - The pydantic-core SchemaSerializer used to dump instances of the model.

  - **\_\_pydantic\_validator\_\_** - The pydantic-core SchemaValidator used to validate instances of the model.

  - **\_\_pydantic\_extra\_\_** - An instance attribute with the values of extra fields from validation when
  `model_config['extra'] == 'allow'`.

  - **\_\_pydantic\_fields\_set\_\_** - An instance attribute with the names of fields explicitly set.

  - **\_\_pydantic\_private\_\_** - Instance attribute with the values of private attributes set on the model instance.

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

## _class_ `GuildUsersRetrun` {#GuildUsersRetrun}

Bases: `iamai.adapter.kook.api.model.ListReturn`

服务器中的用户列表

- **Attributes**

  - **users** (_Optional\[List\[iamai.adapter.kook.api.model.User\]\]_)

  - **user\_count** (_Optional\[int\]_)

  - **online\_count** (_Optional\[int\]_)

  - **offline\_count** (_Optional\[int\]_)

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

## _class_ `Reaction` {#Reaction}

Bases: `pydantic.main.BaseModel`

Usage docs: https://docs.pydantic.dev/2.5/concepts/models/

A base class for creating Pydantic models.

- **Attributes**

  - **emoji** (_Optional\[iamai.adapter.kook.api.model.Emoji\]_)

  - **count** (_Optional\[int\]_)

  - **me** (_Optional\[bool\]_)

  - **\_\_class\_vars\_\_** - The names of classvars defined on the model.

  - **\_\_private\_attributes\_\_** - Metadata about the private attributes of the model.

  - **\_\_signature\_\_** - The signature for instantiating the model.

  - **\_\_pydantic\_complete\_\_** - Whether model building is completed, or if there are still undefined fields.

  - **\_\_pydantic\_core\_schema\_\_** - The pydantic-core schema used to build the SchemaValidator and SchemaSerializer.

  - **\_\_pydantic\_custom\_init\_\_** - Whether the model has a custom `__init__` function.

  - **\_\_pydantic\_decorators\_\_** - Metadata containing the decorators defined on the model.
  This replaces `Model.__validators__` and `Model.__root_validators__` from Pydantic V1.

  - **\_\_pydantic\_generic\_metadata\_\_** - Metadata for generic models; contains data used for a similar purpose to
  __args__, __origin__, __parameters__ in typing-module generics. May eventually be replaced by these.

  - **\_\_pydantic\_parent\_namespace\_\_** - Parent namespace of the model, used for automatic rebuilding of models.

  - **\_\_pydantic\_post\_init\_\_** - The name of the post-init method for the model, if defined.

  - **\_\_pydantic\_root\_model\_\_** - Whether the model is a `RootModel`.

  - **\_\_pydantic\_serializer\_\_** - The pydantic-core SchemaSerializer used to dump instances of the model.

  - **\_\_pydantic\_validator\_\_** - The pydantic-core SchemaValidator used to validate instances of the model.

  - **\_\_pydantic\_extra\_\_** - An instance attribute with the values of extra fields from validation when
  `model_config['extra'] == 'allow'`.

  - **\_\_pydantic\_fields\_set\_\_** - An instance attribute with the names of fields explicitly set.

  - **\_\_pydantic\_private\_\_** - Instance attribute with the values of private attributes set on the model instance.

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

## _class_ `MentionInfo` {#MentionInfo}

Bases: `pydantic.main.BaseModel`

Usage docs: https://docs.pydantic.dev/2.5/concepts/models/

A base class for creating Pydantic models.

- **Attributes**

  - **mention\_part** (_Optional\[List\[dict\]\]_)

  - **mention\_role\_part** (_Optional\[List\[dict\]\]_)

  - **channel\_part** (_Optional\[List\[dict\]\]_)

  - **item\_part** (_Optional\[List\[dict\]\]_)

  - **\_\_class\_vars\_\_** - The names of classvars defined on the model.

  - **\_\_private\_attributes\_\_** - Metadata about the private attributes of the model.

  - **\_\_signature\_\_** - The signature for instantiating the model.

  - **\_\_pydantic\_complete\_\_** - Whether model building is completed, or if there are still undefined fields.

  - **\_\_pydantic\_core\_schema\_\_** - The pydantic-core schema used to build the SchemaValidator and SchemaSerializer.

  - **\_\_pydantic\_custom\_init\_\_** - Whether the model has a custom `__init__` function.

  - **\_\_pydantic\_decorators\_\_** - Metadata containing the decorators defined on the model.
  This replaces `Model.__validators__` and `Model.__root_validators__` from Pydantic V1.

  - **\_\_pydantic\_generic\_metadata\_\_** - Metadata for generic models; contains data used for a similar purpose to
  __args__, __origin__, __parameters__ in typing-module generics. May eventually be replaced by these.

  - **\_\_pydantic\_parent\_namespace\_\_** - Parent namespace of the model, used for automatic rebuilding of models.

  - **\_\_pydantic\_post\_init\_\_** - The name of the post-init method for the model, if defined.

  - **\_\_pydantic\_root\_model\_\_** - Whether the model is a `RootModel`.

  - **\_\_pydantic\_serializer\_\_** - The pydantic-core SchemaSerializer used to dump instances of the model.

  - **\_\_pydantic\_validator\_\_** - The pydantic-core SchemaValidator used to validate instances of the model.

  - **\_\_pydantic\_extra\_\_** - An instance attribute with the values of extra fields from validation when
  `model_config['extra'] == 'allow'`.

  - **\_\_pydantic\_fields\_set\_\_** - An instance attribute with the names of fields explicitly set.

  - **\_\_pydantic\_private\_\_** - Instance attribute with the values of private attributes set on the model instance.

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

## _class_ `BaseMessage` {#BaseMessage}

Bases: `pydantic.main.BaseModel`

Usage docs: https://docs.pydantic.dev/2.5/concepts/models/

A base class for creating Pydantic models.

- **Attributes**

  - **id\_** (_Optional\[str\]_)

  - **type** (_Optional\[int\]_)

  - **content** (_Optional\[str\]_)

  - **embeds** (_Optional\[List\[dict\]\]_)

  - **attachments** (_Union\[bool, iamai.adapter.kook.api.model.Attachments, NoneType\]_)

  - **create\_at** (_Optional\[int\]_)

  - **updated\_at** (_Optional\[int\]_)

  - **reactions** (_Optional\[List\[iamai.adapter.kook.api.model.Reaction\]\]_)

  - **image\_name** (_Optional\[str\]_)

  - **read\_status** (_Optional\[bool\]_)

  - **quote** (_Optional\[iamai.adapter.kook.api.model.Quote\]_)

  - **mention\_info** (_Optional\[iamai.adapter.kook.api.model.MentionInfo\]_)

  - **\_\_class\_vars\_\_** - The names of classvars defined on the model.

  - **\_\_private\_attributes\_\_** - Metadata about the private attributes of the model.

  - **\_\_signature\_\_** - The signature for instantiating the model.

  - **\_\_pydantic\_complete\_\_** - Whether model building is completed, or if there are still undefined fields.

  - **\_\_pydantic\_core\_schema\_\_** - The pydantic-core schema used to build the SchemaValidator and SchemaSerializer.

  - **\_\_pydantic\_custom\_init\_\_** - Whether the model has a custom `__init__` function.

  - **\_\_pydantic\_decorators\_\_** - Metadata containing the decorators defined on the model.
  This replaces `Model.__validators__` and `Model.__root_validators__` from Pydantic V1.

  - **\_\_pydantic\_generic\_metadata\_\_** - Metadata for generic models; contains data used for a similar purpose to
  __args__, __origin__, __parameters__ in typing-module generics. May eventually be replaced by these.

  - **\_\_pydantic\_parent\_namespace\_\_** - Parent namespace of the model, used for automatic rebuilding of models.

  - **\_\_pydantic\_post\_init\_\_** - The name of the post-init method for the model, if defined.

  - **\_\_pydantic\_root\_model\_\_** - Whether the model is a `RootModel`.

  - **\_\_pydantic\_serializer\_\_** - The pydantic-core SchemaSerializer used to dump instances of the model.

  - **\_\_pydantic\_validator\_\_** - The pydantic-core SchemaValidator used to validate instances of the model.

  - **\_\_pydantic\_extra\_\_** - An instance attribute with the values of extra fields from validation when
  `model_config['extra'] == 'allow'`.

  - **\_\_pydantic\_fields\_set\_\_** - An instance attribute with the names of fields explicitly set.

  - **\_\_pydantic\_private\_\_** - Instance attribute with the values of private attributes set on the model instance.

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

## _class_ `ChannelMessage` {#ChannelMessage}

Bases: `iamai.adapter.kook.api.model.BaseMessage`

频道消息

- **Attributes**

  - **author** (_Optional\[iamai.adapter.kook.api.model.User\]_)

  - **mention** (_Optional\[List\[Any\]\]_)

  - **mention\_all** (_Optional\[bool\]_)

  - **mention\_roles** (_Optional\[List\[Any\]\]_)

  - **mention\_here** (_Optional\[bool\]_)

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

## _class_ `DirectMessage` {#DirectMessage}

Bases: `iamai.adapter.kook.api.model.BaseMessage`

私聊消息

- **Attributes**

  - **author\_id** (_Optional\[str\]_)

  - **from\_type** (_Optional\[int\]_)

  - **msg\_icon** (_Optional\[str\]_)

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

## _class_ `ChannelMessagesReturn` {#ChannelMessagesReturn}

Bases: `pydantic.main.BaseModel`

获取私信聊天消息列表返回信息

- **Attributes**

  - **direct\_messages** (_Optional\[List\[iamai.adapter.kook.api.model.ChannelMessage\]\]_)

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

## _class_ `DirectMessagesReturn` {#DirectMessagesReturn}

Bases: `pydantic.main.BaseModel`

获取私信聊天消息列表返回信息

- **Attributes**

  - **direct\_messages** (_Optional\[List\[iamai.adapter.kook.api.model.DirectMessage\]\]_)

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

## _class_ `ReactionUser` {#ReactionUser}

Bases: `iamai.adapter.kook.api.model.User`

开黑啦 User 字段

https://developer.kaiheila.cn/doc/objects

- **Attributes**

  - **reaction\_time** (_Optional\[int\]_)

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

## _class_ `TargetInfo` {#TargetInfo}

Bases: `pydantic.main.BaseModel`

私聊会话 目标用户信息

- **Attributes**

  - **id\_** (_Optional\[str\]_)

  - **username** (_Optional\[str\]_)

  - **online** (_Optional\[bool\]_)

  - **avatar** (_Optional\[str\]_)

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

## _class_ `UserChat` {#UserChat}

Bases: `pydantic.main.BaseModel`

私聊会话

- **Attributes**

  - **code** (_Optional\[str\]_)

  - **last\_read\_time** (_Optional\[int\]_)

  - **latest\_msg\_time** (_Optional\[int\]_)

  - **unread\_count** (_Optional\[int\]_)

  - **target\_info** (_Optional\[iamai.adapter.kook.api.model.TargetInfo\]_)

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

## _class_ `UserChatsReturn` {#UserChatsReturn}

Bases: `iamai.adapter.kook.api.model.ListReturn`

获取私信聊天会话列表返回信息

- **Attributes**

  - **user\_chats** (_Optional\[List\[iamai.adapter.kook.api.model.UserChat\]\]_)

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

## _class_ `RolesReturn` {#RolesReturn}

Bases: `iamai.adapter.kook.api.model.ListReturn`

获取服务器角色列表返回信息

- **Attributes**

  - **roles** (_Optional\[List\[iamai.adapter.kook.api.model.Role\]\]_)

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

## _class_ `GuilRoleReturn` {#GuilRoleReturn}

Bases: `pydantic.main.BaseModel`

赋予或删除用户角色返回信息

- **Attributes**

  - **user\_id** (_Optional\[str\]_)

  - **guild\_id** (_Optional\[str\]_)

  - **roles** (_Optional\[List\[int\]\]_)

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

## _class_ `IntimacyImg` {#IntimacyImg}

Bases: `pydantic.main.BaseModel`

形象图片的总列表

- **Attributes**

  - **id\_** (_Optional\[str\]_)

  - **url** (_Optional\[str\]_)

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

## _class_ `IntimacyIndexReturn` {#IntimacyIndexReturn}

Bases: `pydantic.main.BaseModel`

获取用户亲密度返回信息

- **Attributes**

  - **img\_url** (_Optional\[str\]_)

  - **social\_info** (_Optional\[str\]_)

  - **last\_read** (_Optional\[int\]_)

  - **score** (_Optional\[int\]_)

  - **img\_list** (_Optional\[List\[iamai.adapter.kook.api.model.IntimacyImg\]\]_)

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

## _class_ `GuildEmoji` {#GuildEmoji}

Bases: `pydantic.main.BaseModel`

服务器表情

- **Attributes**

  - **name** (_Optional\[str\]_)

  - **id\_** (_Optional\[str\]_)

  - **user\_info** (_Optional\[iamai.adapter.kook.api.model.User\]_)

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

## _class_ `GuildEmojisReturn` {#GuildEmojisReturn}

Bases: `iamai.adapter.kook.api.model.ListReturn`

获取服务器表情列表返回信息

- **Attributes**

  - **roles** (_Optional\[List\[iamai.adapter.kook.api.model.GuildEmoji\]\]_)

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

## _class_ `Invite` {#Invite}

Bases: `pydantic.main.BaseModel`

邀请信息

- **Attributes**

  - **guild\_id** (_Optional\[str\]_)

  - **channel\_id** (_Optional\[str\]_)

  - **url\_code** (_Optional\[str\]_)

  - **url** (_Optional\[str\]_)

  - **user** (_Optional\[iamai.adapter.kook.api.model.User\]_)

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

## _class_ `InvitesReturn` {#InvitesReturn}

Bases: `iamai.adapter.kook.api.model.ListReturn`

获取邀请列表返回信息

- **Attributes**

  - **roles** (_Optional\[List\[iamai.adapter.kook.api.model.Invite\]\]_)

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
