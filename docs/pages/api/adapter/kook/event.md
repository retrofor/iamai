# iamai.adapter.kook.event

Kook 适配器事件。

## _class_ `ResultStore` {#ResultStore}

Bases: `object`

- **Attributes**

### _method_ `__init__(self, /, *args, **kwargs)` {#object.\_\_init\_\_}

Initialize self.  See help(type(self)) for accurate signature.

- **Arguments**

  - **args**

  - **kwargs**

### _method_ `get_sn(self_id)` {#ResultStore.get\_sn}

- **Returns**

  Type: _int_

### _method_ `set_sn(self_id, sn)` {#ResultStore.set\_sn}

- **Arguments**

  - **sn** (_int_)

- **Returns**

  Type: _None_

## _class_ `AttrDict` {#AttrDict}

Bases: `collections.UserDict`

### _method_ `__init__(self, data=None)` {#AttrDict.\_\_init\_\_}

Initialize self.  See help(type(self)) for accurate signature.

- **Arguments**

  - **data**

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

  - **permission\_overwrites** (_Optional\[List\[iamai.adapter.kook.event.PermissionOverwrite\]\]_)

  - **permission\_users** (_Optional\[List\[iamai.adapter.kook.event.PermissionUser\]\]_)

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

  - **meta** (_Optional\[iamai.adapter.kook.event.Meta\]_)

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

Bases: `iamai.adapter.kook.event.ListReturn`

获取黑名单列表返回信息

- **Attributes**

  - **blacklists** (_Optional\[List\[iamai.adapter.kook.event.BlackList\]\]_)

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

Bases: `iamai.adapter.kook.event.ListReturn`

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

Bases: `iamai.adapter.kook.event.ListReturn`

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

Bases: `iamai.adapter.kook.event.ListReturn`

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

  - **attachments** (_Union\[bool, iamai.adapter.kook.event.Attachments, NoneType\]_)

  - **create\_at** (_Optional\[int\]_)

  - **updated\_at** (_Optional\[int\]_)

  - **reactions** (_Optional\[List\[iamai.adapter.kook.event.Reaction\]\]_)

  - **image\_name** (_Optional\[str\]_)

  - **read\_status** (_Optional\[bool\]_)

  - **quote** (_Optional\[iamai.adapter.kook.event.Quote\]_)

  - **mention\_info** (_Optional\[iamai.adapter.kook.event.MentionInfo\]_)

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

Bases: `iamai.adapter.kook.event.BaseMessage`

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

Bases: `iamai.adapter.kook.event.BaseMessage`

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

  - **direct\_messages** (_Optional\[List\[iamai.adapter.kook.event.ChannelMessage\]\]_)

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

  - **direct\_messages** (_Optional\[List\[iamai.adapter.kook.event.DirectMessage\]\]_)

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

  - **target\_info** (_Optional\[iamai.adapter.kook.event.TargetInfo\]_)

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

Bases: `iamai.adapter.kook.event.ListReturn`

获取私信聊天会话列表返回信息

- **Attributes**

  - **user\_chats** (_Optional\[List\[iamai.adapter.kook.event.UserChat\]\]_)

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

Bases: `iamai.adapter.kook.event.ListReturn`

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

  - **img\_list** (_Optional\[List\[iamai.adapter.kook.event.IntimacyImg\]\]_)

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

Bases: `iamai.adapter.kook.event.ListReturn`

获取服务器表情列表返回信息

- **Attributes**

  - **roles** (_Optional\[List\[iamai.adapter.kook.event.GuildEmoji\]\]_)

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

Bases: `iamai.adapter.kook.event.ListReturn`

获取邀请列表返回信息

- **Attributes**

  - **roles** (_Optional\[List\[iamai.adapter.kook.event.Invite\]\]_)

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

## _class_ `EventTypes` {#EventTypes}

Bases: `enum.IntEnum`

事件主要格式

Kook 协议事件，字段与 Kook 一致。各事件字段参考 `Kook 文档`

.. Kook 文档:
    https://developer.kookapp.cn/doc/event/event-introduction#事件主要格式

## _class_ `SignalTypes` {#SignalTypes}

Bases: `enum.IntEnum`

信令类型

Kook 协议信令，字段与 Kook 一致。各事件字段参考 `Kook 文档`

.. Kook 文档:
    https://developer.kookapp.cn/doc/websocket#信令格式

## _class_ `Attachment` {#Attachment}

Bases: `pydantic.main.BaseModel`

Usage docs: https://docs.pydantic.dev/2.5/concepts/models/

A base class for creating Pydantic models.

- **Attributes**

  - **type** (_str_)

  - **name** (_str_)

  - **url** (_typing.Annotated\[pydantic\_core.\_pydantic\_core.Url, UrlConstraints\(max\_length=2083, allowed\_schemes=\['http', 'https'\], host\_required=None, default\_host=None, default\_port=None, default\_path=None\)\]_)

  - **file\_type** (_Optional\[str\]_)

  - **size** (_Optional\[int\]_)

  - **duration** (_Optional\[float\]_)

  - **width** (_Optional\[int\]_)

  - **hight** (_Optional\[int\]_)

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

## _class_ `Extra` {#Extra}

Bases: `pydantic.main.BaseModel`

Usage docs: https://docs.pydantic.dev/2.5/concepts/models/

A base class for creating Pydantic models.

- **Attributes**

  - **type\_** (_Union\[int, str\]_)

  - **guild\_id** (_Optional\[str\]_)

  - **channel\_name** (_Optional\[str\]_)

  - **mention** (_Optional\[List\[str\]\]_)

  - **mention\_all** (_Optional\[bool\]_)

  - **mention\_roles** (_Optional\[List\[str\]\]_)

  - **mention\_here** (_Optional\[bool\]_)

  - **author** (_Optional\[iamai.adapter.kook.api.model.User\]_)

  - **body** (_Optional\[iamai.adapter.kook.event.AttrDict\]_)

  - **attachments** (_Optional\[iamai.adapter.kook.event.Attachment\]_)

  - **code** (_Optional\[str\]_)

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

### _class_ `Config` {#Extra.Config}

Bases: `object`

#### _method_ `__init__(self, /, *args, **kwargs)` {#object.\_\_init\_\_}

Initialize self.  See help(type(self)) for accurate signature.

- **Arguments**

  - **args**

  - **kwargs**

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

### _method_ `convert_body(v)` {#Extra.convert\_body}

## _class_ `OriginEvent` {#OriginEvent}

Bases: `iamai.event.Event[KookAdapter]`

为了区分信令中非Event事件，增加了前置OriginEvent

- **Attributes**

  - **post\_type** (_str_)

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

## _class_ `Kmarkdown` {#Kmarkdown}

Bases: `pydantic.main.BaseModel`

Usage docs: https://docs.pydantic.dev/2.5/concepts/models/

A base class for creating Pydantic models.

- **Attributes**

  - **raw\_content** (_str_)

  - **mention\_part** (_list_)

  - **mention\_role\_part** (_list_)

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

## _class_ `EventMessage` {#EventMessage}

Bases: `pydantic.main.BaseModel`

Usage docs: https://docs.pydantic.dev/2.5/concepts/models/

A base class for creating Pydantic models.

- **Attributes**

  - **type** (_Union\[int, str\]_)

  - **guild\_id** (_Optional\[str\]_)

  - **channel\_name** (_Optional\[str\]_)

  - **mention** (_Optional\[List\]_)

  - **mention\_all** (_Optional\[bool\]_)

  - **mention\_roles** (_Optional\[List\]_)

  - **mention\_here** (_Optional\[bool\]_)

  - **nav\_channels** (_Optional\[List\]_)

  - **author** (_iamai.adapter.kook.api.model.User_)

  - **kmarkdown** (_Optional\[iamai.adapter.kook.event.Kmarkdown\]_)

  - **code** (_Optional\[str\]_)

  - **attachments** (_Optional\[iamai.adapter.kook.event.Attachment\]_)

  - **content** (_iamai.adapter.kook.message.KookMessage_)

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

## _class_ `KookEvent` {#KookEvent}

Bases: `iamai.adapter.kook.event.OriginEvent`

事件主要格式，来自 d 字段

Kook 协议事件，字段与 Kook 一致。各事件字段参考 `Kook 文档`

.. Kook 文档:
    https://developer.kookapp.cn/doc/event/event-introduction

- **Attributes**

  - **channel\_type** (_Literal\['PERSON', 'GROUP'\]_)

  - **type\_** (_int_)

  - **target\_id** (_str_)

  - **author\_id** (_Optional\[str\]_)

  - **content** (_iamai.adapter.kook.message.KookMessage_)

  - **msg\_id** (_str_)

  - **msg\_timestamp** (_int_)

  - **nonce** (_str_)

  - **extra** (_Extra_)

  - **user\_id** (_str_)

  - **post\_type** (_str_)

  - **self\_id** (_Optional\[str\]_)

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

## _class_ `MessageEvent` {#MessageEvent}

Bases: `iamai.adapter.kook.event.KookEvent`

消息事件

- **Attributes**

  - **post\_type** (_Literal\['message'\]_)

  - **message\_type** (_str_)

  - **sub\_type** (_str_)

  - **event** (_EventMessage_)

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

### _method_ `get_plain_text(self)` {#MessageEvent.get\_plain\_text}

获取消息的纯文本内容。

- **Returns**

  Type: _str_

  消息的纯文本内容。

### _async method_ `reply(self, msg)` {#MessageEvent.reply}

回复消息。

- **Arguments**

  - **msg** (_T\_KookMSG_) - 回复消息的内容，同 `call_api()` 方法。

- **Returns**

  Type: _Dict\[str, Any\]_

  API 请求响应。

## _class_ `PrivateMessageEvent` {#PrivateMessageEvent}

Bases: `iamai.adapter.kook.event.MessageEvent`

私聊消息

- **Attributes**

  - **message\_type** (_Literal\['private'\]_)

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

### _async method_ `reply(self, msg)` {#PrivateMessageEvent.reply}

回复消息。

- **Arguments**

  - **msg** (_T\_KookMSG_) - 回复消息的内容，同 `call_api()` 方法。

- **Returns**

  Type: _Dict\[str, Any\]_

  API 请求响应。

## _class_ `ChannelMessageEvent` {#ChannelMessageEvent}

Bases: `iamai.adapter.kook.event.MessageEvent`

公共频道消息

- **Attributes**

  - **message\_type** (_Literal\['group'\]_)

  - **group\_id** (_str_)

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

### _async method_ `reply(self, msg)` {#ChannelMessageEvent.reply}

回复消息。

- **Arguments**

  - **msg** (_T\_KookMSG_) - 回复消息的内容，同 `call_api()` 方法。

- **Returns**

  Type: _Dict\[str, Any\]_

  API 请求响应。

## _class_ `NoticeEvent` {#NoticeEvent}

Bases: `iamai.adapter.kook.event.KookEvent`

通知事件

- **Attributes**

  - **post\_type** (_Literal\['notice'\]_)

  - **notice\_type** (_str_)

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

## _class_ `ChannelNoticeEvent` {#ChannelNoticeEvent}

Bases: `iamai.adapter.kook.event.NoticeEvent`

频道消息事件

- **Attributes**

  - **group\_id** (_int_)

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

## _class_ `ChannelAddReactionEvent` {#ChannelAddReactionEvent}

Bases: `iamai.adapter.kook.event.ChannelNoticeEvent`

频道内用户添加 reaction

- **Attributes**

  - **notice\_type** (_Literal\['added\_reaction'\]_)

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

## _class_ `ChannelDeletedReactionEvent` {#ChannelDeletedReactionEvent}

Bases: `iamai.adapter.kook.event.ChannelNoticeEvent`

频道内用户删除 reaction

- **Attributes**

  - **notice\_type** (_Literal\['deleted\_reaction'\]_)

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

## _class_ `ChannelUpdatedMessageEvent` {#ChannelUpdatedMessageEvent}

Bases: `iamai.adapter.kook.event.ChannelNoticeEvent`

频道消息更新

- **Attributes**

  - **notice\_type** (_Literal\['updated\_message'\]_)

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

## _class_ `ChannelDeleteMessageEvent` {#ChannelDeleteMessageEvent}

Bases: `iamai.adapter.kook.event.ChannelNoticeEvent`

频道消息被删除

- **Attributes**

  - **notice\_type** (_Literal\['deleted\_message'\]_)

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

## _class_ `ChannelAddedEvent` {#ChannelAddedEvent}

Bases: `iamai.adapter.kook.event.ChannelNoticeEvent`

新增频道

- **Attributes**

  - **notice\_type** (_Literal\['added\_channel'\]_)

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

## _class_ `ChannelUpdatedEvent` {#ChannelUpdatedEvent}

Bases: `iamai.adapter.kook.event.ChannelNoticeEvent`

修改频道信息

- **Attributes**

  - **notice\_type** (_Literal\['updated\_channel'\]_)

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

## _class_ `ChannelDeleteEvent` {#ChannelDeleteEvent}

Bases: `iamai.adapter.kook.event.ChannelNoticeEvent`

删除频道

- **Attributes**

  - **notice\_type** (_Literal\['deleted\_channel'\]_)

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

## _class_ `ChannelPinnedMessageEvent` {#ChannelPinnedMessageEvent}

Bases: `iamai.adapter.kook.event.ChannelNoticeEvent`

新增频道置顶消息

- **Attributes**

  - **notice\_type** (_Literal\['pinned\_message'\]_)

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

## _class_ `ChannelUnpinnedMessageEvent` {#ChannelUnpinnedMessageEvent}

Bases: `iamai.adapter.kook.event.ChannelNoticeEvent`

取消频道置顶消息

- **Attributes**

  - **notice\_type** (_Literal\['unpinned\_message'\]_)

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

## _class_ `PrivateNoticeEvent` {#PrivateNoticeEvent}

Bases: `iamai.adapter.kook.event.NoticeEvent`

私聊消息事件

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

## _class_ `PrivateUpdateMessageEvent` {#PrivateUpdateMessageEvent}

Bases: `iamai.adapter.kook.event.PrivateNoticeEvent`

私聊消息更新

- **Attributes**

  - **notice\_type** (_Literal\['updated\_private\_message'\]_)

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

## _class_ `PrivateDeleteMessageEvent` {#PrivateDeleteMessageEvent}

Bases: `iamai.adapter.kook.event.PrivateNoticeEvent`

私聊消息删除

- **Attributes**

  - **notice\_type** (_Literal\['deleted\_private\_message'\]_)

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

## _class_ `PrivateAddReactionEvent` {#PrivateAddReactionEvent}

Bases: `iamai.adapter.kook.event.PrivateNoticeEvent`

私聊内用户添加 reaction

- **Attributes**

  - **notice\_type** (_Literal\['private\_added\_reaction'\]_)

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

## _class_ `PrivateDeleteReactionEvent` {#PrivateDeleteReactionEvent}

Bases: `iamai.adapter.kook.event.PrivateNoticeEvent`

私聊内用户取消 reaction

- **Attributes**

  - **notice\_type** (_Literal\['private\_deleted\_reaction'\]_)

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

## _class_ `GuildNoticeEvent` {#GuildNoticeEvent}

Bases: `iamai.adapter.kook.event.NoticeEvent`

服务器相关事件

- **Attributes**

  - **group\_id** (_int_)

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

### _method_ `get_guild_id(self)` {#GuildNoticeEvent.get\_guild\_id}

## _class_ `GuildMemberNoticeEvent` {#GuildMemberNoticeEvent}

Bases: `iamai.adapter.kook.event.GuildNoticeEvent`

服务器成员相关事件

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

## _class_ `GuildMemberIncreaseNoticeEvent` {#GuildMemberIncreaseNoticeEvent}

Bases: `iamai.adapter.kook.event.GuildMemberNoticeEvent`

新成员加入服务器

- **Attributes**

  - **notice\_type** (_Literal\['joined\_guild'\]_)

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

## _class_ `GuildMemberDecreaseNoticeEvent` {#GuildMemberDecreaseNoticeEvent}

Bases: `iamai.adapter.kook.event.GuildMemberNoticeEvent`

服务器成员退出

- **Attributes**

  - **notice\_type** (_Literal\['exited\_guild'\]_)

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

## _class_ `GuildMemberUpdateNoticeEvent` {#GuildMemberUpdateNoticeEvent}

Bases: `iamai.adapter.kook.event.GuildMemberNoticeEvent`

服务器成员信息更新(修改昵称)

- **Attributes**

  - **notice\_type** (_Literal\['updated\_guild\_member'\]_)

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

## _class_ `GuildMemberOnlineNoticeEvent` {#GuildMemberOnlineNoticeEvent}

Bases: `iamai.adapter.kook.event.GuildMemberNoticeEvent`

服务器成员上线

- **Attributes**

  - **notice\_type** (_Literal\['guild\_member\_online'\]_)

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

## _class_ `GuildMemberOfflineNoticeEvent` {#GuildMemberOfflineNoticeEvent}

Bases: `iamai.adapter.kook.event.GuildMemberNoticeEvent`

服务器成员下线

- **Attributes**

  - **notice\_type** (_Literal\['guild\_member\_offline'\]_)

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

## _class_ `GuildRoleNoticeEvent` {#GuildRoleNoticeEvent}

Bases: `iamai.adapter.kook.event.GuildNoticeEvent`

服务器角色相关事件

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

## _class_ `GuildRoleAddNoticeEvent` {#GuildRoleAddNoticeEvent}

Bases: `iamai.adapter.kook.event.GuildRoleNoticeEvent`

服务器角色增加

- **Attributes**

  - **notice\_type** (_Literal\['added\_role'\]_)

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

## _class_ `GuildRoleDeleteNoticeEvent` {#GuildRoleDeleteNoticeEvent}

Bases: `iamai.adapter.kook.event.GuildRoleNoticeEvent`

服务器角色增加

- **Attributes**

  - **notice\_type** (_Literal\['deleted\_role'\]_)

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

## _class_ `GuildRoleUpdateNoticeEvent` {#GuildRoleUpdateNoticeEvent}

Bases: `iamai.adapter.kook.event.GuildRoleNoticeEvent`

服务器角色增加

- **Attributes**

  - **notice\_type** (_Literal\['updated\_role'\]_)

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

## _class_ `GuildUpdateNoticeEvent` {#GuildUpdateNoticeEvent}

Bases: `iamai.adapter.kook.event.GuildNoticeEvent`

服务器信息更新

- **Attributes**

  - **notice\_type** (_Literal\['updated\_guild'\]_)

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

## _class_ `GuildDeleteNoticeEvent` {#GuildDeleteNoticeEvent}

Bases: `iamai.adapter.kook.event.GuildNoticeEvent`

服务器删除

- **Attributes**

  - **notice\_type** (_Literal\['deleted\_guild'\]_)

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

## _class_ `GuildAddBlockListNoticeEvent` {#GuildAddBlockListNoticeEvent}

Bases: `iamai.adapter.kook.event.GuildNoticeEvent`

服务器封禁用户

- **Attributes**

  - **notice\_type** (_Literal\['added\_block\_list'\]_)

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

## _class_ `GuildDeleteBlockListNoticeEvent` {#GuildDeleteBlockListNoticeEvent}

Bases: `iamai.adapter.kook.event.GuildNoticeEvent`

服务器取消封禁用户

- **Attributes**

  - **notice\_type** (_Literal\['deleted\_block\_list'\]_)

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

## _class_ `UserNoticeEvent` {#UserNoticeEvent}

Bases: `iamai.adapter.kook.event.NoticeEvent`

用户相关事件列表

- **Attributes**

  - **group\_id** (_int_)

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

## _class_ `UserJoinAudioChannelNoticeEvent` {#UserJoinAudioChannelNoticeEvent}

Bases: `iamai.adapter.kook.event.UserNoticeEvent`

用户加入语音频道

- **Attributes**

  - **notice\_type** (_Literal\['joined\_channel'\]_)

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

## _class_ `UserJoinAudioChannelEvent` {#UserJoinAudioChannelEvent}

Bases: `iamai.adapter.kook.event.UserNoticeEvent`

用户退出语音频道

- **Attributes**

  - **notice\_type** (_Literal\['exited\_channel'\]_)

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

## _class_ `UserInfoUpdateNoticeEvent` {#UserInfoUpdateNoticeEvent}

Bases: `iamai.adapter.kook.event.UserNoticeEvent`

用户信息更新

该事件与服务器无关, 遵循以下条件:
    - 仅当用户的 用户名 或 头像 变更时
    - 仅通知与该用户存在关联的用户或 Bot
        a. 存在聊天会话
        b. 双方好友关系

- **Attributes**

  - **notice\_type** (_Literal\['user\_updated'\]_)

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

## _class_ `SelfJoinGuildNoticeEvent` {#SelfJoinGuildNoticeEvent}

Bases: `iamai.adapter.kook.event.NoticeEvent`

自己新加入服务器

当自己被邀请或主动加入新的服务器时, 产生该事件

- **Attributes**

  - **notice\_type** (_Literal\['self\_joined\_guild'\]_)

  - **user\_id** (_str_)

  - **group\_id** (_int_)

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

## _class_ `SelfExitGuildNoticeEvent` {#SelfExitGuildNoticeEvent}

Bases: `iamai.adapter.kook.event.NoticeEvent`

自己退出服务器

当自己被踢出服务器或被拉黑或主动退出服务器时, 产生该事件

- **Attributes**

  - **notice\_type** (_Literal\['self\_exited\_guild'\]_)

  - **user\_id** (_str_)

  - **group\_id** (_int_)

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

## _class_ `CartBtnClickNoticeEvent` {#CartBtnClickNoticeEvent}

Bases: `iamai.adapter.kook.event.NoticeEvent`

Card 消息中的 Button 点击事件

- **Attributes**

  - **notice\_type** (_Literal\['message\_btn\_click'\]_)

  - **user\_id** (_str_)

  - **group\_id** (_int_)

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

## _class_ `MetaEvent` {#MetaEvent}

Bases: `iamai.adapter.kook.event.OriginEvent`

元事件

- **Attributes**

  - **post\_type** (_Literal\['meta\_event'\]_)

  - **meta\_event\_type** (_str_)

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

## _class_ `LifecycleMetaEvent` {#LifecycleMetaEvent}

Bases: `iamai.adapter.kook.event.MetaEvent`

生命周期元事件

- **Attributes**

  - **meta\_event\_type** (_Literal\['lifecycle'\]_)

  - **sub\_type** (_str_)

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

## _class_ `HeartbeatMetaEvent` {#HeartbeatMetaEvent}

Bases: `iamai.adapter.kook.event.MetaEvent`

心跳元事件

- **Attributes**

  - **meta\_event\_type** (_Literal\['heartbeat'\]_)

  - **sub\_type** (_str_)

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

## _function_ `get_event_class(post_type, event_type, sub_type = None)` {#get\_event\_class}

根据接收到的消息类型返回对应的事件类。

- **Arguments**

  - **post\_type** (_str_) - 请求类型。

  - **event\_type** (_str_) - 事件类型。

  - **sub\_type** (_Optional\[str\]_) - 子类型。

- **Returns**

  Type: _Type\[~T\_KookEvent\]_

  对应的事件类。
