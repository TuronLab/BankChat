import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

from core.agents.greeter_agent import GreeterAgent
from core.data.load_data import JSONCustomerDataLoader
from core.inferencer import OpenAIInferencer
from core.session_manager.models import Client
from core.session_manager.session import Session
from config import ASSETS_PATH, PROJECT_PATH

# Load environment variables from .env
load_dotenv()

@pytest.fixture(scope="module")
def real_inferencer():
    """
    Initialize your real inferencer here.
    Ensure your .env has the necessary API_KEY.
    """
    # Example for a OpenAI-based inferencer:
    return OpenAIInferencer(api_key=os.getenv("OPENAI_API_KEY"))


@pytest.fixture(scope="module")
def real_db_loader():
    """Initialize your real database connector."""
    loader = JSONCustomerDataLoader(Path(os.path.join(PROJECT_PATH, "database_example", "dataset_example.json")))

    loader.data = [
        Client(client_name="John Doe", phone="+34600111222", mentioned_iban="ES1200001111222233334444", client_data={"accounts": [{"iban": "ES1200001111222233334444"}]}),
        Client(client_name="Jane Smith", phone="+44123456789", mentioned_iban="GB12345678901234567890", client_data={"accounts": [{"iban": "GB12345678901234567890"}]}),
    ]
    return loader


@pytest.fixture
def agent(real_inferencer, real_db_loader):
    return GreeterAgent(
        inferencer=real_inferencer,
        database_loader=real_db_loader
    )


@pytest.fixture
def session():
    # Using a real session object
    return Session()


# ---- LIVE INTEGRATION TESTS ----

def test_regex_path_live(agent, session):
    """Verifies the regex still works without LLM interference for a known user."""
    # NOTE: Ensure this user exists in your real DB or use a known test record
    message = "My name is John Doe and my phone is +34600111222"
    response = agent.step(message, session)

    assert response is not None
    # If the user isn't in your DB, this will fail; adjust name/phone to a real record.
    assert response.client is not None


def test_llm_extraction_live(agent, session):
    """Verifies the real Token API can extract structured data from messy text."""
    message = "hey... it's Sarah Connor, call me at 555-9000. My bank thing is ES9912341234123412341234"

    response = agent.step(message, session)

    # Check that the API actually returned a response and didn't crash
    assert response is not None
    assert isinstance(response.message, str)

    # Even if Sarah isn't in your DB, the agent logic should have
    # identified her name from the LLM and included it in the 'not found' message.
    if response.client is None:
        assert "Sarah Connor" in response.message


def test_insufficient_data_live(agent, session):
    """Ensures the real LLM correctly identifies a lack of info."""
    message = "I just want to know what time you open."
    response = agent.step(message, session)

    # Should result in the error_authentication message
    assert response.client is None
    # Check if the returned message matches your error asset text
    from core.utils import read_markdown
    expected_error = read_markdown(os.path.join(ASSETS_PATH, "greeter_agent", "error_authentication.md"))
    assert response.message == expected_error


def test_iban_extraction_live(agent, session):
    """Tests the IBAN regex/LLM logic with a realistic string."""
    message = "Transfer to ES1200001111222233334444. Name is Peter Parker."
    response = agent.step(message, session)

    # We verify the agent reached the DB lookup stage (meaning 2+ fields found)
    # by checking that the message isn't the 'insufficient data' error.
    from core.utils import read_markdown
    error_msg = read_markdown(os.path.join(ASSETS_PATH, "greeter_agent", "error_authentication.md"))
    assert response.message != error_msg