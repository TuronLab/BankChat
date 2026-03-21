from dataclasses import dataclass

from core.session_manager.models import Client


@dataclass
class GreeterAgentResponse:
    client: Client | None = None
    message: str = None