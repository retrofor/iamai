import asyncio
import json
import websockets
from datetime import datetime
from typing import Any, Dict, Optional, List

FIELD_MAPPING = {
    "post_type": "posts",
    "time": "timestamp",
    "self_id": "self_id",
    "message_type": "message_type",
    "sub_type": "sub_type",
    "message_id": "message_id",
    "user_id": "user_id",
    "message": "message",
    "raw_message": "raw_message",
    "font": "font",
    "sender": "sender",
    "group_id": "group_id",
    "anonymous": "anonymous",
    "notice_type": "notice_type",
    "operator_id": "operator_id",
    "duration": "duration",
    "request_type": "request_type",
    "comment": "comment",
    "flag": "flag",
    "meta_event_type": "meta_event_type",
    "status": "status",
    "interval": "interval",
    "retcode": "retcode",
    "data": "data",
    "echo": "echo",
}


class MappedObject:
    def __init__(self, data: Dict[str, Any], mapping: Optional[Dict[str, str]] = None):
        """
        Initialize mapped object.

        :param data: Original data dictionary
        :param mapping: Field mapping dictionary (defaults to FIELD_MAPPING)
        """
        self._data = data
        self._mapping = mapping or FIELD_MAPPING
        self._reverse_mapping = {v: k for k, v in self._mapping.items()}

    def __getattr__(self, name: str) -> Any:
        """
        Get attribute by name.

        Supports both original field names and mapped names.
        """
        if name in self._reverse_mapping:
            original_name = self._reverse_mapping[name]
            if original_name in self._data:
                value = self._data[original_name]
                if isinstance(value, dict):
                    return MappedObject(value, self._mapping)
                elif isinstance(value, list):
                    return [
                        MappedObject(item, self._mapping)
                        if isinstance(item, dict)
                        else item
                        for item in value
                    ]
                return value

        if name in self._data:
            value = self._data[name]
            if isinstance(value, dict):
                return MappedObject(value, self._mapping)
            elif isinstance(value, list):
                return [
                    MappedObject(item, self._mapping)
                    if isinstance(item, dict)
                    else item
                    for item in value
                ]
            return value

        raise AttributeError(
            f"'{type(self).__name__}' object has no attribute '{name}'"
        )

    def __getitem__(self, key: str) -> Any:
        try:
            return self.__getattr__(key)
        except AttributeError:
            raise KeyError(key)

    def get(self, key: str, default: Any = None) -> Any:
        try:
            return self.__getattr__(key)
        except AttributeError:
            return default

    def __repr__(self) -> str:
        return f"MappedObject({self._data})"

    def to_dict(self) -> Dict[str, Any]:
        return self._data.copy()

    def __contains__(self, key: str) -> bool:
        return key in self._data or key in self._reverse_mapping


class MessageMapper:
    @staticmethod
    def map_message(data: Dict[str, Any]) -> MappedObject:
        """
        Map message event.

        :param data: Raw message data
        :return: Mapped message object
        """
        return MappedObject(data)

    @staticmethod
    def map_notice(data: Dict[str, Any]) -> MappedObject:
        """
        Map notice event.

        :param data: Raw notice data
        :return: Mapped notice object
        """
        return MappedObject(data)

    @staticmethod
    def map_request(data: Dict[str, Any]) -> MappedObject:
        """
        Map request event.

        :param data: Raw request data
        :return: Mapped request object
        """
        return MappedObject(data)

    @staticmethod
    def map_meta_event(data: Dict[str, Any]) -> MappedObject:
        """
        Map meta event.

        :param data: Raw meta event data
        :return: Mapped meta event object
        """
        return MappedObject(data)

    @staticmethod
    def map_response(data: Dict[str, Any]) -> MappedObject:
        """
        Map API response.

        :param data: Raw response data
        :return: Mapped response object
        """
        return MappedObject(data)

    @classmethod
    def map_event(cls, data: Dict[str, Any]) -> MappedObject:
        """
        Automatically map event based on post_type.

        :param data: Raw event data
        :return: Mapped event object
        """
        post_type = data.get("post_type")

        if post_type == "message":
            return cls.map_message(data)
        elif post_type == "notice":
            return cls.map_notice(data)
        elif post_type == "request":
            return cls.map_request(data)
        elif post_type == "meta_event":
            return cls.map_meta_event(data)
        elif "retcode" in data:
            return cls.map_response(data)
        else:
            return MappedObject(data)


class OneBot11Client:
    """OneBot11 WebSocket client for testing."""

    def __init__(self, host: str = "127.0.0.1", port: int = 3001, token: str = ""):
        """
        Initialize the OneBot11 client.

        :param host: WebSocket server host
        :param port: WebSocket server port
        :param token: Access token (if required)
        """
        self.host = host
        self.port = port
        self.token = token
        self.ws_url = f"ws://{host}:{port}"
        self.websocket = None

    def _print_message(self, msg_type: str, data: dict, mapped_obj: MappedObject):
        """
        Pretty print received message with mapped object demo.

        :param msg_type: Message type
        :param data: Original message data
        :param mapped_obj: Mapped message object
        """
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] {msg_type}")
        print("Original Data:")
        print(json.dumps(data, indent=2, ensure_ascii=False))

        print(f"\n🔍 Mapped Object Access Examples:")
        print(f"{mapped_obj}")

        if post_type == "message":
            print(f"  • Message Type: {mapped_obj.message_type}")
            print(f"  • User ID: {mapped_obj.user_id}")
            print(f"  • Message: {mapped_obj.message}")
            if hasattr(mapped_obj, "group_id"):
                print(f"  • Group ID: {mapped_obj.group_id}")
            if mapped_obj.get("sender"):
                sender = mapped_obj.sender
                print(f"  • Sender Nickname: {sender.get('nickname', 'N/A')}")
        elif post_type == "notice":
            print(f"  • Notice Type: {mapped_obj.notice_type}")
            print(f"  • User ID: {mapped_obj.get('user_id', 'N/A')}")
        elif post_type == "meta_event":
            print(f"  • Meta Event Type: {mapped_obj.meta_event_type}")
            print(f"  • Sub Type: {mapped_obj.get('sub_type', 'N/A')}")

        print(f"  • Timestamp: {mapped_obj.timestamp}")
        print(f"  • Self ID: {mapped_obj.self_id}")

    async def connect(self):
        """Connect to the OneBot11 WebSocket server."""
        print(f"Connecting to {self.ws_url}...")
        try:
            connect_kwargs = {
                "ping_interval": 30,
                "ping_timeout": 10,
            }

            if self.token:
                connect_kwargs["extra_headers"] = {
                    "Authorization": f"Bearer {self.token}"
                }

            self.websocket = await websockets.connect(self.ws_url, **connect_kwargs)
            print(f"Connected successfully!")
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False

    async def listen(self):
        """Listen for messages from the WebSocket server."""
        if not self.websocket:
            print("Not connected!")
            return

        print("Listening for messages... (Press Ctrl+C to stop)\n")

        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)

                    mapped_obj = MessageMapper.map_event(data)

                    if "post_type" in data:
                        post_type = data.get("post_type")
                        if post_type == "message":
                            msg_type = (
                                f"MESSAGE [{data.get('message_type', 'unknown')}]"
                            )
                        elif post_type == "notice":
                            msg_type = f"NOTICE [{data.get('notice_type', 'unknown')}]"
                        elif post_type == "request":
                            msg_type = (
                                f"REQUEST [{data.get('request_type', 'unknown')}]"
                            )
                        elif post_type == "meta_event":
                            msg_type = (
                                f"META_EVENT [{data.get('meta_event_type', 'unknown')}]"
                            )
                        else:
                            msg_type = f"UNKNOWN POST [{post_type}]"
                    elif "status" in data and "retcode" in data:
                        msg_type = "API RESPONSE"
                    else:
                        msg_type = "RAW DATA"

                    self._print_message(msg_type, data, mapped_obj)

                except json.JSONDecodeError:
                    print(f"Received non-JSON message: {message}")
                except Exception as e:
                    print(f"Error processing message: {e}")
                    import traceback

                    traceback.print_exc()

        except websockets.exceptions.ConnectionClosed:
            print("\nConnection closed by server")
        except KeyboardInterrupt:
            print("\nStopped by user")
        finally:
            await self.close()

    async def close(self):
        """Close the WebSocket connection."""
        if self.websocket:
            await self.websocket.close()
            print("Connection closed")

    async def run(self):
        """Run the client."""
        if await self.connect():
            await self.listen()


async def main():
    """Main entry point."""
    HOST = "127.0.0.1"
    PORT = 3001
    TOKEN = ""

    client = OneBot11Client(host=HOST, port=PORT, token=TOKEN)
    await client.run()


if __name__ == "__main__":
    asyncio.run(main())
