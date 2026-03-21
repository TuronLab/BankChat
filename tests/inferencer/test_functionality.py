import os
import pytest
from dotenv import load_dotenv

from core.session_manager.models import ChatMessage, Role, Client
from core.inferencer import OpenAIInferencer
from core.session_manager.session import Session

# Load environment variables from .env
load_dotenv()


@pytest.fixture(scope="module")
def inferencer():
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        pytest.skip("OPENAI_API_KEY not set")

    return OpenAIInferencer(api_key=api_key)


@pytest.mark.integration
def test_generate_text(inferencer):
    result = inferencer.generate_text([
        ChatMessage(role=Role.USER, message="Say exactly: hello world")
    ])

    assert isinstance(result, str)
    assert len(result) > 0


@pytest.mark.integration
def test_generate_structured_valid_json(inferencer):
    schema = {
        "type": "json_schema",
        "json_schema": {
            "name": "test_schema",
            "schema": {
                "type": "object",
                "properties": {
                    "key": {"type": "string"}
                },
                "required": ["key"],
                "additionalProperties": False
            }
        }
    }

    result = inferencer.generate_structured(
        [
            ChatMessage(
                role=Role.USER,
                message='Return a JSON object with a single key "key" and value "value".'
            )
        ],
        output_schema=schema
    )

    assert isinstance(result, dict)
    assert "key" in result
    assert isinstance(result["key"], str)


@pytest.mark.integration
def test_generate_structured_invalid_json(inferencer):
    with pytest.raises(ValueError, match="Invalid JSON output"):
        inferencer.generate_structured([
            ChatMessage(
                role=Role.USER,
                message="Respond with invalid JSON: this is not json"
            )
        ])


# --- Tools to be used in tests ---
def add_numbers(a: int, b: int) -> int:
    """Adds two numbers together."""
    return a + b

def get_account_balance(account_id: str, session: Session) -> str:
    """
    Retrieves the balance for a given account ID from the session.
    """
    # Accessing the data exactly as defined in your test setup
    balance = session.client.client_data.get("balance", 0)
    return f"The balance for account {account_id} is ${balance}"


@pytest.mark.integration
def test_generate_with_tools_simple_math(inferencer):
    """Tests a basic tool call without session injection."""
    conversation = [
        ChatMessage(role=Role.USER, message="What is 15 plus 27?")
    ]

    # We pass the function directly; the inferencer handles schema generation
    result = inferencer.generate_with_tools(
        conversation=conversation,
        tools=[add_numbers]
    )

    assert "42" in result
    assert isinstance(result, str)


# --- The Fixed Test ---
@pytest.mark.integration
def test_generate_with_tools_session_injection(inferencer):
    """Tests that the session object is correctly injected into the tool."""

    # 1. Setup the session state
    session = Session()
    session.client = Client()
    session.client.client_data = {"balance": 5000}  # Set to 5000

    conversation = [
        ChatMessage(role=Role.USER, message="How much money is in account 12345?")
    ]

    # 2. Run inference
    result = inferencer.generate_with_tools(
        conversation=conversation,
        session=session,
        tools=[get_account_balance]
    )

    # 3. Assertions
    # Check for 5000 (matching the session setup) and the account ID
    assert "5000" in result
    assert "12345" in result
    assert isinstance(result, str)