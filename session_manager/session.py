import uuid
from datetime import datetime
from typing import List, NewType

from session_manager.models import Client, State, ChatIteration

SessionId = NewType("SessionId", uuid.UUID)

class Session:
    """
    Represents a user session in the system.

    This class is responsible for holding the session state and related
    conversational data. It does NOT handle persistence.
    """

    def __init__(self, client: Client):
        """
        Initialize a new session.

        Args:
            client (Client): The client associated with the session.
        """
        self.session_id: SessionId = SessionId(uuid.uuid4())
        self.client: Client = client
        self.state: State = State.VERIFYING
        self.session_creation: datetime = datetime.now()
        self.chat_iterations: List[ChatIteration] = []

    def update_state(self, new_state: State) -> None:
        """
        Update the current state of the session.

        Args:
            new_state (State): The new state to assign.
        """
        self.state = new_state

    def add_chat_iteration(self, chat_iteration: ChatIteration) -> None:
        """
        Add a new chat iteration to the session.

        Args:
            chat_iteration (ChatIteration): The chat interaction to store.
        """
        self.chat_iterations.append(chat_iteration)