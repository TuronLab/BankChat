from dataclasses import dataclass
from enum import Enum
from typing import Optional, List, Any


@dataclass
class Client:
    client_name: str = None
    mentioned_iban: Optional[str] = None
    phone: str = None
    type_client: str = None
    client_data: dict = None


class State(Enum):
    VERIFYING = "VERIFYING"
    VERIFIED = "VERIFIED"

class Role(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"

@dataclass
class ChatMessage:
    role: Role
    message: str
    tool_call_id: str = None
    tool_calls: Optional[List[Any]] = None

