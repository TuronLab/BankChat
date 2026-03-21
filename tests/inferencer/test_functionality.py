import pytest
from unittest.mock import MagicMock

from session_manager.models import ChatMessage, Role
from core.inferencer import OpenAIInferencer


# -----------------------------
# Helpers
# -----------------------------

def make_openai_mock(first_response, second_response=None):
    client_mock = MagicMock()

    if second_response:
        client_mock.chat.completions.create.side_effect = [
            first_response,
            second_response,
        ]
    else:
        client_mock.chat.completions.create.return_value = first_response

    return client_mock


# -----------------------------
# Tests
# -----------------------------

def test_generate_text(monkeypatch):
    fake_response = MagicMock()
    fake_response.choices = [
        MagicMock(message=MagicMock(content="hello world"))
    ]

    client_mock = make_openai_mock(fake_response)

    monkeypatch.setattr(
        "openai.OpenAI",
        lambda api_key=None: client_mock,
    )

    inferencer = OpenAIInferencer(api_key="fake")

    result = inferencer.generate_text([
        ChatMessage(role=Role.USER, message="hi")
    ])

    assert result == "hello world"

    client_mock.chat.completions.create.assert_called_once()

    # Verify message format
    _, kwargs = client_mock.chat.completions.create.call_args
    assert kwargs["messages"][0]["role"] == "user"
    assert kwargs["messages"][0]["content"] == "hi"


def test_generate_structured_invalid_json(monkeypatch):
    fake_response = MagicMock()
    fake_response.choices = [
        MagicMock(message=MagicMock(content="not json"))
    ]

    client_mock = make_openai_mock(fake_response)

    monkeypatch.setattr(
        "openai.OpenAI",
        lambda api_key=None: client_mock,
    )

    inferencer = OpenAIInferencer(api_key="fake")

    with pytest.raises(ValueError):
        inferencer.generate_structured([
            ChatMessage(role=Role.USER, message="give json")
        ])


def test_generate_structured_valid_json(monkeypatch):
    fake_response = MagicMock()
    fake_response.choices = [
        MagicMock(message=MagicMock(content='{"key": "value"}'))
    ]

    client_mock = make_openai_mock(fake_response)

    monkeypatch.setattr(
        "openai.OpenAI",
        lambda api_key=None: client_mock,
    )

    inferencer = OpenAIInferencer(api_key="fake")

    result = inferencer.generate_structured([
        ChatMessage(role=Role.USER, message="give json")
    ])

    assert result == {"key": "value"}
