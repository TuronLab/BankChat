import pytest

from core.session_manager.custom_exceptions import UnknownSessionIdException
from core.session_manager.models import Client
from core.session_manager.session import Session
from core.session_manager.session_repository import NoStorageRepository


def test_save_and_get_session():
    repo = NoStorageRepository()
    dummy_client = Client(client_name="test_client")

    session = Session(client=dummy_client)

    repo.save(session)

    assert repo.get(session.session_id) == session


def test_delete_session():
    repo = NoStorageRepository()
    dummy_client = Client(client_name="test_client")
    session = Session(client=dummy_client)

    repo.save(session)
    repo.delete(session.session_id)

    with pytest.raises(UnknownSessionIdException):
        repo.get(session.session_id)


def test_get_all_sessions():
    repo = NoStorageRepository()

    dummy_client1 = Client(client_name="test_client1")
    dummy_client2 = Client(client_name="test_client2")
    session1 = Session(client=dummy_client1)
    session2 = Session(client=dummy_client2)

    repo.save(session1)
    repo.save(session2)

    all_sessions = repo.get_all()

    assert len(all_sessions) == 2
    assert session1.session_id in all_sessions
    assert session2.session_id in all_sessions
    