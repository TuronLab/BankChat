import abc
from typing import Dict
from core.session_manager.session import Session, SessionId


class SessionRepository(abc.ABC):
    """
    Abstract base class for session storage implementations.

    This defines the contract that all storage backends must follow,
    such as in-memory, Redis, database, etc.
    """

    @abc.abstractmethod
    def save(self, session: Session) -> None:
        """
        Persist a session.

        Args:
            session (Session): The session to store.
        """
        pass

    @abc.abstractmethod
    def delete(self, session_id) -> None:
        """
        Delete a session by its ID.

        Args:
            session_id (UUID): The identifier of the session to delete.
        """
        pass

    @abc.abstractmethod
    def get(self, session_id) -> Session:
        """
        Retrieve a session by its ID.

        Args:
            session_id (UUID): The identifier of the session.

        Returns:
            Session: The requested session.
        """
        pass

    @abc.abstractmethod
    def get_all(self) -> Dict:
        """
        Retrieve all stored sessions.

        Returns:
            Dict[UUID, Session]: Mapping of session IDs to sessions.
        """
        pass


class NoStorageRepository(SessionRepository):
    """
    In-memory implementation of SessionRepository.

    This class simulates a storage system with no persistence.
    It is useful for testing or lightweight usage scenarios.
    """

    def __init__(self):
        """
        Initialize an empty in-memory session storage.
        """
        self._sessions: Dict[SessionId | str, Session] = {}

    def save(self, session: Session) -> None:
        """
        Save a session in memory.

        Args:
            session (Session): The session to store.
        """
        self._sessions[session.session_id] = session

    def delete(self, session_id: str) -> None:
        """
        Delete a session from memory if it exists.

        Args:
            session_id (UUID): The session identifier.
        """
        self._sessions.pop(session_id, None)

    def get(self, session_id: str) -> Session:
        """
        Retrieve a session by its ID.

        Args:
            session_id (UUID): The session identifier.

        Returns:
            Session: The requested session.

        Raises:
            KeyError: If the session does not exist.
        """
        return self._sessions[session_id]

    def get_all(self) -> Dict:
        """
        Retrieve all sessions stored in memory.

        Returns:
            Dict[UUID, Session]: All sessions.
        """
        return self._sessions
