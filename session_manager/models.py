from dataclasses import dataclass
from datetime import datetime
from enum import Enum


@dataclass
class Client:
    client_name: str = None
    iban: str = None
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

