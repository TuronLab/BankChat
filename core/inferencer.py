import inspect
import json
from abc import abstractmethod, ABC
from copy import deepcopy
from typing import Optional, Dict, Any, List, Callable

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
        session: Session,
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
        """Converts ChatMessage to OpenAI format, handling both Enums and strings."""

        # Check if role has a .value (Enum), otherwise use it as is (string)
        role_name = message.role.value if hasattr(message.role, "value") else message.role

        payload = {
            "role": role_name,
            "content": message.message,
        }

        # Assistant messages MUST include tool_calls if they exist
        if message.tool_calls:
            payload["tool_calls"] = message.tool_calls

        # Tool messages MUST include the tool_call_id
        if message.tool_call_id:
            payload["tool_call_id"] = message.tool_call_id

        return payload

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
            response_format=output_schema,
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
    def _function_to_schema(self, func: Callable) -> Dict[str, Any]:
        """
        Converts a Python function into an OpenAI-compatible tool schema.
        Automatically excludes the 'session' argument from the LLM's view.
        """
        sig = inspect.signature(func)
        doc = inspect.getdoc(func) or "No description provided."

        parameters = {
            "type": "object",
            "properties": {},
            "required": []
        }

        for name, param in sig.parameters.items():
            # We skip 'session' because the LLM shouldn't try to provide it
            if name == "session":
                continue

            # Simple type mapping
            ptype = "string"
            if param.annotation == int:
                ptype = "integer"
            elif param.annotation == float:
                ptype = "number"
            elif param.annotation == bool:
                ptype = "boolean"
            elif param.annotation == list:
                ptype = "array"
            elif param.annotation == dict:
                ptype = "object"

            parameters["properties"][name] = {
                "type": ptype,
                "description": f"The {name} parameter."  # Enhancement: parse from docstring
            }

            if param.default is inspect.Parameter.empty:
                parameters["required"].append(name)

        return {
            "type": "function",
            "function": {
                "name": func.__name__,
                "description": doc,
                "parameters": parameters,
            }
        }

    def generate_with_tools(
            self,
            conversation: List[ChatMessage],
            session: Any = None,
            tools: List[Callable] = [],
            **kwargs: Any,
    ) -> str:
        """Executes a tool-augmented loop with automated session injection."""
        conversation = deepcopy(conversation)
        tool_map = {f.__name__: f for f in tools}
        openai_tools = [self._function_to_schema(f) for f in tools]

        messages = self.build_conversation(conversation)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=openai_tools if openai_tools else None,
            tool_choice="auto" if openai_tools else None,
            **kwargs,
        )

        message_obj = response.choices[0].message

        if message_obj.tool_calls:
            # 1. Store the Assistant's request (including tool_calls)
            conversation.append(ChatMessage(
                role=Role.ASSISTANT,
                message=message_obj.content,
                tool_calls=message_obj.tool_calls
            ))

            # 2. Execute the tools
            tool_messages = []
            for tool_call in message_obj.tool_calls:
                func_name = tool_call.function.name
                func_obj = tool_map.get(func_name)

                if not func_obj:
                    result = f"Error: Tool {func_name} not found."
                else:
                    args = json.loads(tool_call.function.arguments)

                    # Inject session if required
                    sig = inspect.signature(func_obj)
                    if "session" in sig.parameters:
                        args["session"] = session

                    try:
                        result = func_obj(**args)
                    except Exception as e:
                        result = f"Error: {str(e)}"

                tool_messages.append(ChatMessage(
                    role=Role.TOOL,
                    message=json.dumps(result) if not isinstance(result, str) else result,
                    tool_call_id=tool_call.id
                ))

            # 3. Recurse with the full history (Assistant Call + Tool Responses)
            return self.generate_with_tools(
                conversation + tool_messages,
                session=session,
                tools=tools,
                **kwargs
            )

        return message_obj.content