from enum import Enum
from typing import (
    Any,
    Callable,
    List,
    Literal,
    MutableSequence,
    Optional,
    Sequence,
    Union,
)

# from anthropic import AnthropicBedrock
from anthropic import AnthropicVertex
from anthropic.types import Message as AnthropicMessage
from anthropic.types import TextBlock as AnthropicTextBlock
from pydantic import PrivateAttr

from app.config import appSettings
from app.logger_config import setup_logger
from app.schemas import ToolBaseSchema
from app.schemas.messages_schemas import (
    Message,
    MessageBase,
    MessageRole,
    MessageType,
    ToolUseMessage,
)
from app.schemas.thread_agent_schema import ThreadAgent
from app.serializers.messages.claude_messages_serializers import (
    claude_messages_list_serializer,
)
from app.serializers.tools import claude_tool_calling_serializer
from app.tool_registry import ToolRegistry

logger = setup_logger(__name__)

client = AnthropicVertex(
    project_id=appSettings.GCP_PROJECT_ID,  # type: ignore
    region=appSettings.GCP_REGION,  # type: ignore
)

MODEL_ID = "claude-3-5-sonnet@20240620"

# client = AnthropicBedrock(
#     aws_access_key=appSettings.AWS_ACCESS_KEY,
#     aws_secret_key=appSettings.AWS_SECRET_KEY,
# )
# MODEL_ID = "anthropic.claude-3-5-sonnet-20240620-v1:0"


class ModelMessageRoles(Enum):
    """Message roles for the model."""

    USER = "user"
    AI = "assistant"

    @staticmethod
    def get_role_mapping() -> dict[str, str]:
        """Get the role mapping."""
        return {
            MessageRole.USER.value: ModelMessageRoles.USER.value,
            MessageRole.AI.value: ModelMessageRoles.AI.value,
        }


class ClaudeAgent(ThreadAgent):
    """Claude agent responsible for interacting with the Anthropic model.

    If any system message is passed inside the messages, the system message
    will be picked based on ```system_message_method```. The rest will be
    ignored.

    Attributes
    ----------
        model: The model identifier to be used for processing messages.
        max_tokens: Maximum number of tokens to be generated.
        serializer: Function used to serialize conversation messages.
        verbose: Whether to log detailed information for debugging.
        tools: List of tools available for the agent to use.
        tools_serializer: Function used to serialize the tools information.
        system_message_method: ```first``` or ```last``` to choose the system
            message inside messages.

    """

    model: str = MODEL_ID
    max_tokens: int = 8192
    messages_serializer: Callable[..., Any] = claude_messages_list_serializer
    verbose: bool = True
    tools: List[ToolBaseSchema] = []
    tools_serializer: Callable[..., Any] = claude_tool_calling_serializer
    tools_registry: Optional[ToolRegistry] = None
    system_message_selector: Literal["first", "last"] = "first"
    _current_run_messages: List[MessageBase] = PrivateAttr(default=[])
    """List of messages generated by the agent during the current run."""

    def __init__(self, **data: Any) -> None:
        """Initialize the Claude agent."""
        super().__init__(**data)
        self.tools_registry = ToolRegistry()
        if len(self.tools) > 0:
            self.tools_registry.register_tools(self.tools)

    def agent_run(
        self, thread_messages: MutableSequence[MessageBase], **kwargs: Any
    ) -> Sequence[MessageBase]:
        """Execute agent's workflow entirely.

        Args:
        ----
            thread_messages: List of messages forming the conversation thread.
            **kwargs: Additional arguments for processing the response.

        Returns:
        -------
            - List of messages generated by the agent. Including tool uses.

        """
        if not kwargs.get("calling_from_inside_agent_run"):
            self._current_run_messages = []

        if self.verbose:
            logger.debug(f"Runnig agent with messages: {thread_messages}")

        response = self.send_to_claude(thread_messages, **kwargs)

        logger.debug(f"------------------\n{response}\n------------------")

        run_messages = self.process_model_response(response, **kwargs)
        self._current_run_messages.extend(run_messages)

        thread_messages.extend(run_messages)

        if any(
            isinstance(message, ToolUseMessage) for message in run_messages
        ):
            kwargs["calling_from_inside_agent_run"] = True
            logger.debug(
                "Tools were used. Feeding agent with results"
            ) if self.verbose else None
            self.agent_run(thread_messages, **kwargs)

        return self._current_run_messages

    def send_to_claude(
        self, thread_messages: MutableSequence[MessageBase], **kwargs: Any
    ) -> AnthropicMessage:
        """Send thread's messages to the model and return the raw response.

        Args:
        ----
            thread_messages: List of messages forming the conversation thread.
            **kwargs: Additional arguments for the serialization process.

        Returns:
        -------
            AnthropicMessage: The response message from the Claude model.

        """
        serialized_messages = self.messages_serializer(
            thread_messages,
            **{"roles_mapping": ModelMessageRoles.get_role_mapping()},
        )
        if self.verbose:
            logger.debug(f"Serialized messages: {serialized_messages}")

        if self.system_message_selector == "first":
            system_message = next(
                (
                    message
                    for message in thread_messages
                    if message.role == MessageRole.SYSTEM
                ),
                None,
            )

        elif self.system_message_selector == "last":
            system_message = next(
                (
                    message
                    for message in reversed(thread_messages)
                    if message.role == MessageRole.SYSTEM
                ),
                None,
            )

        serialized_tools = [self.tools_serializer(tool) for tool in self.tools]
        logger.debug(
            f"Serialized tools: {serialized_tools}"
        ) if self.verbose else None

        if system_message and isinstance(system_message, Message):
            logger.debug(
                f"Calling agent with {self.system_message_selector} "
                "system prompt."
            ) if self.verbose else None

            response = client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=serialized_messages,
                tools=serialized_tools,
                system=system_message.content,
            )

        else:
            logger.debug(
                "Calling agent without system prompt."
            ) if self.verbose else None

            response = client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=serialized_messages,
                tools=serialized_tools,
            )

        return response

    def process_model_response(
        self, response: AnthropicMessage, **kwargs: Any
    ) -> Sequence[MessageBase]:
        """Process the model response."""
        stop_reason = response.stop_reason
        if stop_reason in ["end_turn", "max_tokens", "stop_sequence"]:
            logger.debug("stop reason doesn't require tools processing.")
            if stop_reason == "max_tokens":
                logger.warning("The response reached the max tokens limit.")

            first_message = response.content[0]
            if isinstance(first_message, AnthropicTextBlock):
                messages: List[MessageBase] = [
                    Message(
                        role=MessageRole.AI,
                        type=MessageType.TEXT,
                        content=first_message.text,
                    )
                ]
                return messages
            else:
                raise ValueError(
                    f"Unexpected response content: {first_message}"
                )

        elif stop_reason == "tool_use":
            logger.debug("The response requires tools processing.")
            tool_use_messages: List[ToolUseMessage] = []
            # if the content blocks are not ToolUseBlocks, ignore them
            for block in response.content:
                if block.type == "tool_use":
                    if isinstance(block.input, dict) or isinstance(
                        block.input, str
                    ):
                        block_input = block.input
                    else:
                        block_input = str(block.input)

                    tool_use_message = ToolUseMessage(
                        run_id=block.id,
                        name=block.name,
                        type=MessageType.TEXT,
                        role=MessageRole.TOOL_USE,
                        input_params_dict=block_input,
                    )
                    tool_use_messages.append(tool_use_message)
                else:
                    logger.warning(
                        f"Ignoring '{block.type}' block since a tool"
                        "will be used."
                    ) if self.verbose else None
                    # raise ValueError(f"Unexpected tool use block: {block}")
            logger.debug(f"Passing to process_tools: {tool_use_messages}")
            tool_use_messages = self.process_tools(tool_use_messages)

            return tool_use_messages

        else:
            raise ValueError(f"Unexpected stop reason: {stop_reason}")

    def process_tools(
        self, tool_use_messages: List[ToolUseMessage], **kwargs: Any
    ) -> List[ToolUseMessage]:
        """Process the tools."""
        updated_tool_use_messages = []
        if self.tools_registry:
            for tool_message in tool_use_messages:
                if isinstance(tool_message.input_params_dict, str):
                    args_dict = {"response": tool_message}
                else:
                    args_dict = tool_message.input_params_dict

                try:
                    logger.debug(
                        f"Executing tool: '{tool_message.name}' "
                        f"with args: {args_dict}"
                    )
                    tool_response = self.tools_registry.execute_tool(
                        tool_message.name,
                        args_dict,
                        **kwargs,
                    )
                    logger.info(
                        f"Tool returned:\n{tool_response}"
                    ) if self.verbose else None

                    tool_message.tool_outputs = tool_response.content
                    if tool_response.external_fields:
                        tool_message.external_fields.update(
                            tool_response.external_fields
                        )
                    updated_tool_use_messages.append(tool_message)

                except Exception:
                    tool_message.is_error = True
                    logger.error(
                        f"Error executing tool: {tool_message.name}"
                        f"with args: {args_dict}"
                    )
                    raise ValueError(f"Error executing tool: {tool_message}")

        return updated_tool_use_messages
