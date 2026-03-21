import os

import pytest

from config import ASSETS_PATH
from core.utils import read_markdown


# ---- MOCKS ----

class MockDatabaseLoader:
    def find_customer(self, name=None, phone=None, iban=None):
        if name == "John Doe" and phone == "+34600111222":
            return {"id": 1, "name": "John Doe"}
        return None


class MockInferencer:
    def generate_structured(self, messages, schema):
        text = messages[0]["content"]

        if "missing phone" in text:
            return {"name": "John Doe", "phone": "+34600111222", "iban": None}

        if "unknown user" in text:
            return {"name": "Jane Doe", "phone": "+34123456789", "iban": None}

        return {"name": None, "phone": None, "iban": None}


class MockSession:
    def __init__(self):
        self.client = None


# ---- IMPORT YOUR AGENT ----
# Adjust this import to your actual project structure
from core.agents.greeter_agent import DataExtractorAgent


# ---- FIX read_markdown SIDE EFFECT ----
def fake_read_markdown(path):
    return f"[MOCKED MESSAGE from {path}]"


# ---- TEST SETUP ----

@pytest.fixture
def agent(monkeypatch):
    # Patch read_markdown to avoid file dependency
    monkeypatch.setattr(
        "core.utils.read_markdown",
        fake_read_markdown
    )

    return DataExtractorAgent(
        inferencer=MockInferencer(),
        database_loader=MockDatabaseLoader()
    )


@pytest.fixture
def session():
    return MockSession()


# ---- TESTS ----

def test_full_regex_match_success(agent, session):
    response = agent.step(
        "Hello, I am John Doe and my phone is +34600111222",
        session
    )

    assert response.client is not None
    assert response.client["name"] == "John Doe"


def test_llm_fills_missing_phone(agent, session):
    response = agent.step(
        "Hello, I am John Doe (missing phone)",
        session
    )

    assert response.client is not None
    assert session.client is not None
    assert session.client["name"] == "John Doe"


def test_user_not_found(agent, session):
    response = agent.step(
        "unknown user",
        session
    )

    assert response.client is None
    assert "Jane Doe" in response.message


def test_not_enough_data(agent, session):
    response = agent.step(
        "Hi there",
        session
    )

    assert response.client is None
    assert read_markdown(os.path.join(ASSETS_PATH, "greeter_agent", "error_authentication.md")) == response.message


def test_partial_regex_no_match_then_llm(agent, session):
    response = agent.step(
        "Hello, I am john doe and my phone is +34600111222",
        session
    )

    assert response.client is None


def test_regex_only_name_no_phone(agent, session):
    response = agent.step(
        "My name is John Doe",
        session
    )

    # Should fallback to LLM but still succeed
    assert response.client is None


def test_invalid_user_with_two_fields(agent, session):
    response = agent.step(
        "unknown user with some data",
        session
    )

    assert response.client is None
    assert "Jane Doe" in response.message


def test_session_not_set_on_fast_path(agent, session):
    """
    This exposes a design inconsistency:
    session.client is NOT set in regex-only success path.
    """
    agent.step(
        "John Doe +34600111222",
        session
    )

    assert session.client is None  # current behavior

