import os
from datetime import datetime, timedelta

from session_manager.session_repository import SessionRepository
from session_manager.session import Session


class SessionManager:
    """
    High-level manager for session lifecycle operations.

    This class acts as a facade over the repository and provides
    methods to create, retrieve, and delete sessions.
    """

    def __init__(self, repository: SessionRepository):
        """
        Initialize the session manager.

        Args:
            repository (SessionRepository): The storage backend to use.
        """
        self.repository = repository

    def create_session(self, client) -> Session:
        """
        Create and store a new session.

        Args:
            client (Client): The client associated with the session.

        Returns:
            Session: The newly created session.
        """
        session = Session(client)
        self.repository.save(session)
        return session

    def delete_session(self, session_id) -> None:
        """
        Delete a session by its ID.

        Args:
            session_id (UUID): The identifier of the session to delete.
        """
        self.repository.delete(session_id)

    def get_session(self, session_id) -> Session:
        """
        Retrieve a session by its ID.

        Args:
            session_id (UUID): The identifier of the session.

        Returns:
            Session: The requested session.
        """
        return self.repository.get(session_id)

    def remove_expired_sessions(self) -> None:
        """
        Remove sessions that have expired based on a time threshold.

        The threshold is defined by the environment variable:
        `SESSION_EXPIRE_TIME_THRESHOLD` (in seconds).

        If the variable is not set, no sessions are removed.
        """
        threshold = self._get_threshold()
        if threshold is None:
            return

        now = datetime.now()

        for session_id, session in list(self.repository.get_all().items()):
            if now - session.session_creation > timedelta(seconds=threshold):
                self.repository.delete(session_id)

    def _get_threshold(self):
        """
        Retrieve the expiration threshold from environment variables.

        Returns:
            int | None: The threshold in seconds, or None if not set.

        Raises:
            ValueError: If the environment variable is not a valid integer.
        """
        value = os.getenv("SESSION_EXPIRE_TIME_THRESHOLD")

        if value is None:
            return None

        try:
            return int(value)
        except ValueError:
            raise ValueError(
                "Invalid SESSION_EXPIRE_TIME_THRESHOLD. "
                "It must be an integer."
            )
