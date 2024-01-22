# iamai.adapter.kook.message

Kook 适配器消息。

## _abstract class_ `KookMessage` {#KookMessage}

Bases: `iamai.message.Message`

Kook v3 协议 Message 适配。

### _method_ `__init__(self, *messages)` {#Message.\_\_init\_\_}

初始化。

- **Arguments**

  - **\*messages** (_Union\[List\[~MessageSegmentT\], ~MessageSegmentT, str, Mapping\[str, Any\]\]_) - 可以被转化为消息的数据。

- **Returns**

  Type: _None_

## _abstract class_ `KookMessageSegment` {#KookMessageSegment}

Bases: `iamai.message.MessageSegment[KookMessage]`

Kook 消息字段。

### _method_ `Card(content)` {#KookMessageSegment.Card}

构造卡片消息

- **Returns**

  Type: _KookMessageSegment_

### _method_ `KMarkdown(content, raw_content = None)` {#KookMessageSegment.KMarkdown}

构造KMarkdown消息段

- **Arguments**

  - **raw\_content** (_Optional\[str\]_) - （可选）消息段的纯文本内容

- **Returns**

  Type: _KookMessageSegment_

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

### _method_ `at(user_id)` {#KookMessageSegment.at}

- **Returns**

  Type: _KookMessageSegment_

### _method_ `audio(file_key, title = None, cover_file_key = None)` {#KookMessageSegment.audio}

- **Arguments**

  - **title** (_Optional\[str\]_)

  - **cover\_file\_key** (_Optional\[str\]_)

- **Returns**

  Type: _KookMessageSegment_

### _method_ `file(file_key, title = None)` {#KookMessageSegment.file}

- **Arguments**

  - **title** (_Optional\[str\]_)

- **Returns**

  Type: _KookMessageSegment_

### _method_ `image(file_key)` {#KookMessageSegment.image}

- **Returns**

  Type: _KookMessageSegment_

### _method_ `quote(msg_id)` {#KookMessageSegment.quote}

- **Returns**

  Type: _KookMessageSegment_

### _method_ `text(text)` {#KookMessageSegment.text}

- **Returns**

  Type: _KookMessageSegment_

### _method_ `video(file_key, title = None)` {#KookMessageSegment.video}

- **Arguments**

  - **title** (_Optional\[str\]_)

- **Returns**

  Type: _KookMessageSegment_

## _function_ `escape_kmarkdown(content)` {#escape\_kmarkdown}

将文本中的kmarkdown标识符进行转义

- **Arguments**

  - **content** (_str_)

## _function_ `unescape_kmarkdown(content)` {#unescape\_kmarkdown}

去除kmarkdown中的转义字符

- **Arguments**

  - **content** (_str_)
