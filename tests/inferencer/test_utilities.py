from core.session_manager.models import ChatMessage, Role
from core.inferencer import OpenAIInferencer

def test_format_messages_user():
    inferencer = OpenAIInferencer(api_key="fake")

    msg = ChatMessage(role=Role.USER, message="hello")

    formatted = inferencer.format_messages(msg)

    assert formatted == {
        "role": "user",
        "content": "hello",
    }

def test_format_tool_message():
    inferencer = OpenAIInferencer(api_key="fake")

    msg = ChatMessage(
        role=Role.TOOL,
        message="result",
        tool_call_id="123"
    )

    formatted = inferencer.format_messages(msg)

    assert formatted == {
        "role": "tool",
        "content": "result",
        "tool_call_id": "123",
    }