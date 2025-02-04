from dataclasses import dataclass

@dataclass
class Message:
    content: str
    platform: str 
    user_id: str