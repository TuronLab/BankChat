import uuid
from datetime import datetime
from typing import List, NewType

from core.session_manager.models import Client, State, ChatMessage

SessionId = NewType("SessionId", uuid.UUID)

class Session:
    """
    Represents a user session in the system.

    This class is responsible for holding the session state and related
    conversational data. It does NOT handle persistence.
    """

    def __init__(self, client: Client = None):
        """
        Initialize a new session.

        Args:
            client (Client): The client associated with the session.
        """
        self.session_id: SessionId | str = str(uuid.uuid4())
        self.client: Client = client
        self.state: State = State.VERIFYING
        self.session_creation: datetime = datetime.now()
        self.chat_iterations: List[ChatMessage] = []

    def update_state(self, new_state: State) -> None:
        """
        Update the current state of the session.

        Args:
            new_state (State): The new state to assign.
        """
        self.state = new_state

    def add_chat_iteration(self, chat_iteration: ChatMessage) -> None:
        """
        Add a new chat iteration to the session.

        Args:
            chat_iteration (ChatMessage): The chat interaction to store.
        """
        self.chat_iterations.append(chat_iteration)