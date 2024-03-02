"""iamai message module.

Implemented the commonly used basic message ``Message`` and message field ``MessageSegment`` models for adapter use.
Adapter developers can implement subclasses of the message classes in this module or define different message types as needed, but it is recommended that subclasses of the message classes in this module be used if possible.
"""

from abc import ABC, abstractmethod
from typing import (
    Any,
    Dict,
    Generic,
    ItemsView,
    Iterator,
    KeysView,
    List,
    Mapping,
    Optional,
    SupportsIndex,
    Type,
    TypeVar,
    Union,
    ValuesView,
    overload,
)
from typing_extensions import Self

from pydantic import BaseModel, Field, GetCoreSchemaHandler
from pydantic_core import core_schema

__all__ = [
    "MessageT",
    "MessageSegmentT",
    "BuildMessageType",
    "Message",
    "MessageSegment",
]

MessageT = TypeVar("MessageT", bound="Message[Any]")
MessageSegmentT = TypeVar("MessageSegmentT", bound="MessageSegment[Any]")

# Type that can be converted to Message
BuildMessageType = Union[List[MessageSegmentT], MessageSegmentT, str, Mapping[str, Any]]


class Message(ABC, List[MessageSegmentT]):
    """Message.

    This class is a subclass of ``List`` and overrides the ``__init__()`` method.
    Can handle `str`, ``Mapping``, ``MessageSegment``, ``List[MessageSegment]`` directly.
    This class overloads the ``+`` and ``+=`` operators, and can directly perform sum operations with objects of ``Message``, ``MessageSegment`` and other types of objects.
    Adapter developers need to inherit this class and override the ``get_segment_class()`` method.
    """

    def __init__(self, *messages: BuildMessageType[MessageSegmentT]) -> None:
        """initialization.

        Args:
            *messages: Data that can be converted into messages.
        """
        segment_class = self.get_segment_class()
        for message in messages:
            if isinstance(message, list):
                self.extend(message)
            elif isinstance(message, segment_class):
                self.append(message)
            elif isinstance(message, str):
                self.append(segment_class.from_str(message))
            elif isinstance(message, Mapping):
                self.append(segment_class.from_mapping(message))
            else:
                raise TypeError(
                    f"message type error, expect List[{segment_class}], "
                    f"{segment_class}, str or Mapping, get {type(message)}"
                )

    @classmethod
    @abstractmethod
    def get_segment_class(cls) -> Type[MessageSegmentT]:
        """Get the message field class.

        Returns:
            Message field class.
        """

    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source: Type[Any], handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        """Pydantic custom mode."""
        return core_schema.union_schema(
            [
                core_schema.is_instance_schema(cls),
                core_schema.no_info_after_validator_function(
                    cls,
                    handler.generate_schema(
                        List[cls.get_segment_class()]  # type: ignore[misc, index]
                    ),
                ),
            ]
        )

    def __repr__(self) -> str:
        """Return the description of the message.

        Returns:
            Description of the message.
        """
        return f"Message:[{','.join(map(repr, self))}]"

    def __str__(self) -> str:
        """Returns the textual representation of the message.

        Returns:
            The textual representation of the message.
        """
        return "".join(map(str, self))

    def __contains__(self, item: object) -> bool:
        """Determine whether the message contains the specified text or message field.

        Args:
            item: text or message field.

        Returns:
            Whether the specified text or message field is included in the message.
        """
        if isinstance(item, str):
            return item in str(self)
        return super().__contains__(item)

    def __add__(self, other: BuildMessageType[MessageSegmentT]) -> Self:  # type: ignore
        """Method for adding custom messages to other objects.

        Args:
            other: other objects.

        Returns:
            The result of the addition.
        """
        return self.__class__(self).__iadd__(other)

    def __radd__(self, other: BuildMessageType[MessageSegmentT]) -> Self:
        """Method for adding custom messages to other objects.

        Args:
            other: other objects.

        Returns:
            The result of the addition.
        """
        return self.__class__(other).__iadd__(self)

    def __iadd__(self, other: BuildMessageType[MessageSegmentT]) -> Self:  # type: ignore
        """Method for adding custom messages to other objects.

        Args:
            other: other objects.

        Returns:
            The result of the addition.
        """
        try:
            self.extend(self.__class__(other))
        except TypeError as e:
            raise TypeError(
                f"unsupported operand type(s) for +: '{type(self)}' and '{type(other)}'",
            ) from e
        return self

    def is_text(self) -> bool:
        """Whether it is a plain text message."""
        return all(x.is_text() for x in self)

    def get_plain_text(self) -> str:
        """Get the plain text part of the message.

        Returns:
            The plain text portion of the message.
        """
        return "".join(map(str, filter(lambda x: x.is_text(), self)))

    def copy(self) -> Self:
        """Return a shallow copy of itself.

        Returns:
            A shallow copy of itself.
        """
        return self.__class__(self)

    def startswith(
        self,
        prefix: Union[str, MessageSegmentT],
        start: Optional[SupportsIndex] = None,
        end: Optional[SupportsIndex] = None,
    ) -> bool:
        """Implement string-like ``startswith()`` method.

        When the ``prefix`` type is ``str``, it will convert itself to the ``str`` type, and then call the ``startswith()`` method of the ``str`` type.
        When the ``prefix`` type is ``MessageSegment``, the ``start`` and `end` parameters will have no effect,
            It will be judged whether the first message field of the list is equal to ``prefix``.

        Args:
            prefix: prefix.
            start: Start checking the position.
            end: Stop checking the position.

        Returns:
            test result.
        """  # noqa: D402
        if isinstance(prefix, str):
            return str(self).startswith(prefix, start, end)
        if isinstance(prefix, self.get_segment_class()):
            return False if len(self) == 0 else self[0] == prefix
        raise TypeError(
            f"first arg must be str or {self.get_segment_class()}, not {type(prefix)}"
        )

    def endswith(
        self,
        suffix: Union[str, MessageSegmentT],
        start: Optional[SupportsIndex] = None,
        end: Optional[SupportsIndex] = None,
    ) -> bool:
        """Implement string-like ``endswith()`` method.

        When the ``suffix`` type is `str`, it will convert itself to the ``str`` type, and then call the ``endswith()`` method of the ``str`` type.
        When the ``suffix`` type is MessageSegment, the `start` and ``end`` parameters will have no effect.
            Will determine whether the last message field in the list is equal to `suffix`.

        Args:
            suffix: suffix.
            start: Start checking the position.
            end: Stop checking the position.

        Returns:
            test result.
        """  # noqa: D402
        if isinstance(suffix, str):
            return str(self).endswith(suffix, start, end)
        if isinstance(suffix, self.get_segment_class()):
            return False if len(self) == 0 else self[-1] == suffix
        raise TypeError(
            f"first arg must be str or {self.get_segment_class()}, not {type(suffix)}"
        )

    @overload
    def replace(self, old: str, new: str, count: int = -1) -> Self: ...

    @overload
    def replace(
        self, old: MessageSegmentT, new: Optional[MessageSegmentT], count: int = -1
    ) -> Self: ...

    def replace(
        self,
        old: Union[str, MessageSegmentT],
        new: Optional[Union[str, MessageSegmentT]],
        count: int = -1,
    ) -> Self:
        """Implement string-like ``replace()`` method.

        When ``old`` is of type ``str``, ``new`` must also be ``str``, and this method will only process the message fields where ``is_text()`` is ``True``.
        When ``old`` is of MessageSegment type, ``new`` can be ``MessageSegment`` or ``None``, and this method will process all message fields.
            And replace the message fields that meet the criteria. ``None`` means to delete the matching message field.

        Args:
            old: The matched string or message field.
            new: The string or message field to be replaced.
            count: the number of replacements.

        Returns:
            The replaced message object.
        """  # noqa: D402
        if isinstance(old, str):
            if not isinstance(new, str):
                raise TypeError("when type of old is str, type of new must be str.")
            return self._replace_str(old, new, count)
        if isinstance(old, self.get_segment_class()):
            if not (isinstance(new, self.get_segment_class()) or new is None):
                raise TypeError(
                    "when type of old is MessageSegment, "
                    "type of new must be MessageSegment or None."
                )
            new_msg = self.__class__()
            for item in self:
                if count != 0 and item == old:
                    count -= 1
                    if new is not None:
                        new_msg.append(new)
                else:
                    new_msg.append(item)
            return new_msg
        raise TypeError("type of old must be str or MessageSegment")

    def _replace_str(self, old: str, new: str, count: int = -1) -> Self:
        """Implement string-like ``replace()`` method.

        This method will be called by the ``replace()`` method to handle replacement of type ``str``,
        By default, the ``data['text']`` of the ``MessageSegment`` object is treated as a location to store plain text.
        Adapter developers can override this method to adapt to other situations.

        Args:
            old: The matched string or message field.
            new: The string or message field to be replaced.
            count: the number of replacements.

        Returns:
            The replaced message object.
        """
        temp_msg = self.__class__(*(x.model_copy(deep=True) for x in self))
        for index, item in enumerate(temp_msg):
            if count == 0:
                break
            if item.is_text() and old in item.data["text"]:
                if count == -1:
                    temp_msg[index].data["text"] = item.data["text"].replace(old, new)
                else:
                    replace_times = min(count, item.data["text"].count(old))
                    temp_msg[index].data["text"] = item.data["text"].replace(
                        old, new, replace_times
                    )
                    count -= replace_times
        return temp_msg


class MessageSegment(ABC, BaseModel, Mapping[str, Any], Generic[MessageT]):
    """Message field.

    This class implements all ``Mapping`` type methods, all of which operate on the ``data`` attribute.
    This class overrides the ``+`` and ``+=`` operators, and can directly perform sum operations with objects of types such as ``Message``, ``MessageSegment`` and return a ``Message`` object.
    Adapter developers need to inherit this class and override the ``get_message_class()`` method.

    Attributes:
        type: message field type.
        data: message field content.
    """

    type: str
    data: Dict[str, Any] = Field(default_factory=dict)

    @classmethod
    @abstractmethod
    def get_message_class(cls) -> Type[MessageT]:
        """Get the message class.

        Returns:
            Message class.
        """

    @classmethod
    @abstractmethod
    def from_str(cls, msg: str) -> Self:
        """Used to convert ``str`` to a message field, subclasses should override this method.

        Args:
            msg: Data to be parsed into message fields.

        Returns:
            Message fields converted by ``str``.
        """

    @classmethod
    def from_mapping(cls, msg: Mapping[Any, Any]) -> Self:
        """Used to convert ``Mapping`` into message fields.

        Subclasses can override this method to change the default behavior for ``Mapping`` if necessary.

        Args:
            msg: Data to be parsed into message fields.

        Returns:
            Message fields converted by Mapping.
        """
        return cls(**msg)

    def __str__(self) -> str:
        """Returns the text representation of the message field.

        Returns:
            Text representation of the message field.
        """
        return str(self.data)

    def __repr__(self) -> str:
        """Returns the description of the message field.

        Returns:
            Description of message fields.
        """
        return f"MessageSegment<{self.type}>:{self!s}"

    def __getitem__(self, key: str) -> Any:
        """Get the index. It is equivalent to doing this operation on the ``data`` attribute.

        Args:
            key: key.

        Returns:
            `data` The value of the corresponding index in the dictionary.
        """
        return self.data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        """Set the value of the specified index. Equivalent to doing this on the ``data`` attribute.

        Args:
            key: key.
            value: value.
        """
        self.data[key] = value

    def __delitem__(self, key: str) -> None:
        """Delete the index. Equivalent to doing this operation on the ``data`` attribute.

        Args:
            key: key.
        """
        del self.data[key]

    def __len__(self) -> int:
        """Get the length. Equivalent to doing this operation on the ``data` attribute.

        Returns:
            `data` The length of the dictionary.
        """
        return len(self.data)

    def __iter__(self) -> Iterator[str]:  # type: ignore
        """Iterate. Equivalent to doing this operation on the ``data`` attribute.

        Returns:
            ``data`` Iterator for dictionary.
        """
        yield from self.data.__iter__()

    def __contains__(self, key: object) -> bool:
        """Whether the index is included in the object. Equivalent to doing this on the ``data`` attribute.

        Args:
            key: key.

        Returns:
            Whether the index is contained in the ``data`` dictionary.
        """
        return key in self.data

    def __eq__(self, other: object) -> bool:
        """Determine whether they are equal.

        Args:
            other: other objects.

        Returns:
            are equal.
        """
        return (
            type(other) is self.__class__  # pylint: disable=unidiomatic-typecheck
            and self.type == other.type
            and self.data == other.data
        )

    def __ne__(self, other: object) -> bool:
        """Determine whether they are not equal.

        Args:
            other: other objects.

        Returns:
            Whether they are not equal.
        """
        return not self.__eq__(other)

    def __add__(self, other: Any) -> MessageT:
        """Method for adding custom message fields to other objects.

        Args:
            other: other objects.

        Returns:
            The result of the addition.
        """
        return self.get_message_class()(self) + other

    def __radd__(self, other: Any) -> MessageT:
        """Method for adding custom message fields to other objects.

        Args:
            other: other objects.

        Returns:
            The result of the addition.
        """
        return self.get_message_class()(other) + self

    def get(self, key: str, default: Any = None) -> Any:
        """Returns the value of ``key`` if ``key`` exists in the ``data`` dictionary, otherwise returns ``default``."""
        return self.data.get(key, default)

    def keys(self) -> KeysView[str]:
        """Returns a new view consisting of ``data`` dictionary keys."""
        return self.data.keys()

    def values(self) -> ValuesView[Any]:
        """Returns a new view consisting of ``data`` dictionary values."""
        return self.data.values()

    def items(self) -> ItemsView[str, Any]:
        """Returns a new view consisting of ``data`` dictionary items (``(key, value)`` pairs)."""
        return self.data.items()

    def is_text(self) -> bool:
        """is a plain text message field.

        Returns:
            Whether it is a plain text message field.
        """
        return self.type == "text"
