import os
import pytest
from dotenv import load_dotenv

from core.session_manager.models import ChatMessage, Role
from core.inferencer import OpenAIInferencer


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