# Built-in Messages 

iamai has built-in a message class and recommends all adapter developers to use it as much as possible. It provides many useful functionalities 
for conveniently constructing rich-text messages.

iamai has built-in the `Message` and `MessageSegment` classes, which represent messages and message segments, respectively.

Most adapter message classes are subclasses of the built-in message classes, but there are some special use cases that can be referred to in the adapter documentation.

The built-in message classes and message segment classes are essentially implementations of the OneBot protocol message classes.

## Message Class

The message class ( `Message` ) is a subclass of `list` and can be regarded as a list of message segments, but it provides the following additional functionalities:

It overrides the `__init__()` method to allow initialization with objects of types: str, Mapping, Iterable[Mapping], MessageSegment, and Message. 
Note that str is not natively supported and needs to be implemented by the adapter developer. 
When a Message object of the same type is passed in during initialization, a new Message object with the same content will be created. When a MessageSegment object is passed in, it will be added to the list. Mapping and Iterable[Mapping] are mainly for the convenience of using pydantic to process events in the adapter, 
which regular users do not need to be concerned about.

```python
msg_seg = MessageSegment()
mas_seg.type = "text"
msg_seg["text"] = "Hello"
msg = Message(msg_seg)

msg = Message("Hello")  # The native built-in Message does not support this usage.

msg = Message(msg)
```

It implements the `+` and `+=` operators, allowing direct addition with objects of types: `Message`, `MessageSegment`, and `str`.

```python

msg = Message()

msg_seg = MessageSegment()
msg_seg.type = "text"
msg_seg["text"] = "Hello"

msg += msg_seg
msg = msg + "Hello" # The native built-in Message does not support this usage.
```

It implements the `startswith()`, `endswith()`, and `replace()` methods, similar to the corresponding methods for strings, but it can accept `MessageSegment` or `str` objects as arguments. Please refer to the API documentation(/api/message.md) for details.

```python
msg.startswith("a")
```

## Message Segment

The message segment `class (MessageSegment)` is a data class that also inherits from Mapping. The reason for not using pydantic's model class is to facilitate conversion to JSON in the adapter.

It has two fields: `type` and `data`, which represent the type and content of the message segment, respectively. type is of type `str`, and data is a `dict`. You can directly use dictionary-related operations on the `MessageSegment object`, which is equivalent to operating on the data field. For example:

```python
msg_seg = MessageSegment()
msg_seg.type = "text"

msg_seg["text"] = "Hello" # Equivalent to msg_seg.data['text'] = 'Hello'   
print(msg_seg.get("text")) # Equivalent to print(msg_seg.data.get('text'))
```

Message segment objects can also be directly added to other objects, and it will return a message class.

```python

msg_seg_1 = MessageSegment()
msg_seg_2 = MessageSegment()
msg = msg_seg_1 + msg_seg_2
type(msg)  # Message
```

## Example 

```python
from iamai import Plugin
from iamai.adapter.cqhttp.message import CQHTTPMessage, CQHTTPMessageSegment

class Hello(Plugin):
    async def handle(self) -> None:
       msg = CQHTTPMessage()
       msg += CQHTTPMessageSegment.text("Hello")
       msg += CQHTTPMessageSegment.image("file//path/hello.png")
       await self.event.reply(msg)

    async def rule(self) -> bool:
        if self.event.adapter.name != "cqhttp":
            return False
        if self.event.type != "message":
            return False
        return str(self.event.message) == "hello"

```