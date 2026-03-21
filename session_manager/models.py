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


class ChatIteration:
    client_message: str = None
    chat_message: str = None
    timestamp: datetime = None

