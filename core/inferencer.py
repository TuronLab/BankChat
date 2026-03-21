import json
from abc import abstractmethod, ABC
from typing import Optional, Dict, Any, List

from core.session_manager.models import ChatMessage, Role
from core.session_manager.session import Session


class BaseInferencer(ABC):
    """
    Abstract base class for LLM inference backends.

    This interface is based on a chat-oriented, role-based message format,
    where inputs are provided as a sequence of `ChatMessage` objects
    (e.g., system, user, assistant, tool).

    Implementations (OpenAI, Hugging Face, vLLM, etc.) must convert these
    messages into the provider-specific format.
    """

    @abstractmethod
    def format_messages(self, message: ChatMessage) -> Dict[str, Any]:
        """
        Convert a single ChatMessage into the provider-specific message format.

        Args:
            message (ChatMessage): Internal message representation.

        Returns:
            Dict[str, Any]: Provider-compatible message dict.
        """
        pass

    @abstractmethod
    def build_conversation(
        self, conversation: List[ChatMessage]
    ) -> List[Dict[str, Any]]:
        """
        Convert a list of ChatMessage objects into a provider-specific
        message sequence.

        Args:
            conversation (List[ChatMessage]): Ordered chat messages.

        Returns:
            List[Dict[str, Any]]: Provider-compatible message list.
        """
        pass

    @abstractmethod
    def generate_text(
        self,
        conversation: List[ChatMessage],
        max_tokens: int = 256,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> str:
        """
        Generate free-form text from a conversation.

        Args:
            conversation (List[ChatMessage]): Chat-based prompt.
            max_tokens (int): Maximum number of tokens to generate.
            temperature (float): Sampling temperature.
            **kwargs: Backend-specific parameters.

        Returns:
            str: Generated assistant response.
        """
        raise NotImplementedError

    @abstractmethod
    def generate_structured(
        self,
        conversation: List[ChatMessage],
        output_schema: Optional[Dict[str, Any]] = None,
        max_tokens: int = 256,
        temperature: float = 0.0,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Generate structured output from a conversation.

        Args:
            conversation (List[ChatMessage]): Chat-based prompt.
            output_schema (Optional[Dict[str, Any]]): Optional schema describing
                the expected output structure.
            max_tokens (int): Maximum tokens to generate.
            temperature (float): Sampling temperature (low recommended).
            **kwargs: Backend-specific parameters.

        Returns:
            Dict[str, Any]: Parsed structured output.
        """
        raise NotImplementedError

    @abstractmethod
    def generate_with_tools(
        self,
        conversation: List[ChatMessage],
        session: Session = None,
        tools: list = [],
        **kwargs: Any,
    ) -> str:
        """
        Run a tool-augmented inference loop.

        The model may request tool calls, whose results are fed back into
        the conversation until a final response is produced.

        Args:
            conversation (List[ChatMessage]): Initial conversation.
            session (Session, optional): Session state manager.
            tools (list): Tool definitions available to the model.
            **kwargs: Backend-specific parameters.

        Returns:
            Dict[str, Any]:
                - final_response (str)
                - tool_calls (optional list)
        """
        raise NotImplementedError


class OpenAIInferencer(BaseInferencer):
    """
    OpenAI implementation using chat-based message format.
    """

    def __init__(
        self,
        model: str = "gpt-4.1-mini",
        api_key: Optional[str] = None,
    ):
        from openai import OpenAI

        self.client = OpenAI(api_key=api_key)
        self.model = model

    # -------------------------
    # Message formatting
    # -------------------------

    def format_messages(self, message: ChatMessage) -> Dict[str, Any]:
        if message.role != Role.TOOL:
            return {
                "role": message.role.value,
                "content": message.message,
            }
        else:
            return {
                "role": message.role.value,
                "content": message.message,
                "tool_call_id": message.tool_call_id,
            }

    def build_conversation(
        self, conversation: List[ChatMessage]
    ) -> List[Dict[str, Any]]:
        return [self.format_messages(m) for m in conversation]

    # -------------------------
    # Text generation
    # -------------------------

    def generate_text(
        self,
        conversation: List[ChatMessage],
        max_tokens: int = 256,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> str:

        messages = self.build_conversation(conversation)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs,
        )

        return response.choices[0].message.content

    # -------------------------
    # Structured output
    # -------------------------

    def generate_structured(
        self,
        conversation: List[ChatMessage],
        output_schema: Optional[Dict[str, Any]] = None,
        max_tokens: int = 256,
        temperature: float = 0.0,
        **kwargs: Any,
    ) -> Dict[str, Any]:

        messages = self.build_conversation(conversation)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs,
        )

        content = response.choices[0].message.content

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON output:\n{content}")

    # -------------------------
    # Tool calling
    # -------------------------

    def generate_with_tools(
        self,
        conversation: List[ChatMessage],
        session: Session = None,
        tools: list = [],
        **kwargs: Any,
    ) -> str:

        messages = self.build_conversation(conversation)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            **kwargs,
        )

        message = response.choices[0].message

        if message.tool_calls:
            tool_results = []

            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                arguments = tool_call.function.arguments

                result = self.execute_tool(tool_name, arguments)

                tool_results.append(
                    ChatMessage(
                        role=Role.TOOL,
                        message=str(result),
                        tool_call_id=tool_call.id
                    )
                )

            # Recurse with updated conversation
            new_conversation = conversation + [
                ChatMessage(role=Role.ASSISTANT, message=message.content or ""),
            ] + tool_results

            return self.generate_with_tools(
                new_conversation,
                session=session,
                tools=tools,
                **kwargs,
            )

        return message.content