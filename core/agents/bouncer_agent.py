from core.session_manager.session import Session
from core.agents.agent_base import AgentBase


class BouncerAgent(AgentBase):
    """
    Agent that extracts the type of client just from the extracted field in the database
    """

    def step(self, message: str, session: Session) -> str:
        return session.client.type_client
