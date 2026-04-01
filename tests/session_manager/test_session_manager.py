import pytest

from core.session_manager.custom_exceptions import UnknownSessionIdException
from core.session_manager.models import Client
from core.session_manager.session_manager import SessionManager
from core.session_manager.session_repository import NoStorageRepository


def test_create_session():
    repo = NoStorageRepository()
    manager = SessionManager(repo)
    dummy_client = Client(client_name="test_client")

    session = manager.create_session(client=dummy_client)

    assert session in repo.get_all().values()


def test_get_session():
    repo = NoStorageRepository()
    manager = SessionManager(repo)
    dummy_client = Client(client_name="test_client")

    session = manager.create_session(client=dummy_client)
    retrieved = manager.get_session(session.session_id)

    assert retrieved == session


def test_delete_session():
    repo = NoStorageRepository()
    manager = SessionManager(repo)
    dummy_client = Client(client_name="test_client")

    session = manager.create_session(client=dummy_client)
    manager.delete_session(session.session_id)

    with pytest.raises(UnknownSessionIdException):
        manager.get_session(session.session_id)