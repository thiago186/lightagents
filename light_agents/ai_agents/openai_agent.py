from enum import Enum
from typing import (
    Any,
    Callable,
    List,
    Literal,
    MutableSequence,
    Optional,
    Sequence,
)

from openai import OpenAI
from openai.types.chat.chat_completion import ChatCompletion
from pydantic import PrivateAttr

from light_agents.config import appSettings
from light_agents.core.logger_config import setup_logger
from light_agents.core.tool_registry import ToolRegistry
from light_agents.exceptions.thread_agent_exceptions import (
    AIAgentCompletionError,
)
from light_agents.schemas import ToolBaseSchema
from light_agents.schemas.messages_schemas import (
    Message,
    MessageBase,
    MessageRole,
    MessageType,
    ToolUseMessage,
)
from light_agents.schemas.thread_agent_schema import ThreadAgent
from light_agents.serializers.messages.openai_messages_serializer import (
    openai_messages_list_serializer,
)

logger = setup_logger(__name__)

client = OpenAI(api_key=appSettings.OPENAI_API_KEY)


class OpenAIMessageRoles(str, Enum):
    """OpenAI Message Roles."""

    USER = "user"
    AI = "assistant"
    SYSTEM = "system"

    def get_role_mapping(self) -> dict[str, str]:
        """Get role mapping from OpenAI roles to Light Agent roles."""
        role_mapping = {
            MessageRole.AI.value: OpenAIMessageRoles.AI.value,
            MessageRole.USER.value: OpenAIMessageRoles.USER.value,
            MessageRole.SYSTEM.value: OpenAIMessageRoles.SYSTEM.value,
        }
        return role_mapping


class OpenAIAgent(ThreadAgent):
    """OpenAI Agent.

    Interacts with OpenAI model's API.

    Attributes:
        model: OpenAI model identifier. Default is `gpt-4o`.
        max_tokens: Maximum number of tokens to generate.
        messages_serializer: Messages serializer function for the model.
        verbose: Flag to indicate if the agent should print messages.
        tools: List of tools available for the agent.
        tools_serializer: Tools serializer function for the model.
        tools_registry: Registry of tools available for the agent.
        system_message_selector: Selector for system messages.

    """

    model: str = "gpt-4o"
    """OpenAI model identifier. Default is `gpt-4o`."""

    max_tokens: int = 8192
    """Maximum number of tokens to generate."""

    messages_serializer: Callable[..., Any] = openai_messages_list_serializer
    """Messages serializer function for the model."""

    verbose: bool = True
    """Flag to indicate if the agent should print messages."""

    tools: List[ToolBaseSchema] = []
    """List of tools available for the agent."""

    tools_serializer: Callable[..., Any] = lambda x: None
    """Tools serializer function for the model."""

    tools_registry: Optional[ToolRegistry] = None
    """Registry of tools available for the agent. at
    [light_agents.core.tool_registry.ToolRegistry]"""

    system_message_selector: Literal["first", "last", "all"] = "all"
    """Selector for system messages."""

    _current_run_messages: List[MessageBase] = PrivateAttr(default=[])
    """List of messages generated in the current run."""

    def __init__(self, **data: Any) -> None:
        """Initialize OpenAI Agent."""
        super().__init__(**data)
        self.tools_registry = ToolRegistry()
        if len(self.tools) > 0:
            self.tools_registry.register_tools(self.tools)

    def agent_run(
        self, thread_messages: MutableSequence[MessageBase], **kwargs: Any
    ) -> MutableSequence[MessageBase]:
        """Run the agent on the thread messages.

        Args:
            thread_messages: List of messages in the thread.
            **kwargs: Additional arguments.

        Returns:
           messages: List of messages generated by the agent.
           
        """
        if not kwargs.get("calling_from_inside_agent_run"):
            self._current_run_messages = []

        if self.verbose:
            logger.debug("Running OpenAI Agent.")

        model_response = self.send_to_openai(thread_messages, **kwargs)

        run_messages = self.process_model_response(model_response, **kwargs)
        self._current_run_messages.extend(run_messages)

        thread_messages.extend(run_messages)

        if any(
            isinstance(message, ToolUseMessage) for message in run_messages
        ):
            kwargs["calling_from_inside_agent_run"] = True
            logger.debug(
                "Tools were used in the response. Processing tools."
            ) if self.verbose else None
            self.agent_run(thread_messages, **kwargs)
            
        return self._current_run_messages


    def send_to_openai(
        self, thread_messages: MutableSequence[MessageBase], **kwargs: Any
    ) -> ChatCompletion:
        """Send messages to OpenAI model.

        Args:
            thread_messages: List of messages in the thread.
            **kwargs: Additional arguments.

        Returns:
            completion: OpenAI completion object.

        """
        messages = self.messages_serializer(thread_messages)
        completion: ChatCompletion = client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=self.max_tokens,
            **kwargs,
        )
        return completion

    def process_model_response(
        self, completion: ChatCompletion, **kwargs: Any
    ) -> Sequence[MessageBase]:
        """Process the model response.

        If the response contains a tool calling, calls `execute_tool` method.
        Otherwise returns the first generated message.

        Args:
            completion: OpenAI completion object.
            **kwargs: Additional arguments.

        Returns:
            messages: List of messages generated by the agent.

        """
        response_messages = []
        # tool_responses = []
        for message in completion.choices:
            if message.finish_reason == "stop":
                # natural stop for the model
                if message.message.content:
                    response_content: str = message.message.content
                    response_message = Message(
                        content=response_content,
                        role=MessageRole.AI,
                        type=MessageType.TEXT,
                    )
                    response_messages.append(response_message)
                else:
                    raise AIAgentCompletionError(
                        "Model stopped without generating any content. "
                        f"Response: \n{message}"
                    )

            elif message.finish_reason in ["tool_calls", "function_call"]:
                # TODO: process tool call into ToolUseMessage
                # and call process_tools
                # tool_use_message =
                # tool_response = self.process_tools([])
                ...

            elif message.finish_reason == "length":
                logger.warning("Model reached maximum token limits.")
                # TODO: handle this cas
                ...

            elif message.finish_reason == "content_filter":
                # TODO: handle this case
                logger.warning("Model content omitted due to content filter.")
                ...

            else:
                logger.error(
                    f"Unknown finish reason: '{message.finish_reason}'"
                )

        if len(response_messages) == 0:
            raise AIAgentCompletionError(f"No messages were\n{completion}")

        return response_messages

    def process_tools(
        self, tool_use_messages: List[ToolUseMessage], **kwargs: Any
    ) -> List[ToolUseMessage]:
        """Process tool use messages.

        Args:
            tool_use_messages: List of tool use messages.
            **kwargs: Additional arguments.

        Returns:
            tool_use_messages: List of tool use messages.

        """
        ##TODO: implement tool processing
        ...
        return []
