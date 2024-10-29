from ast import literal_eval
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
from openai.types.chat import ChatCompletion, ChatCompletionMessageToolCall
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
from light_agents.serializers.tools.openai_tools_serializer import (
    openai_tool_calling_serializer,
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

    tools_serializer: Callable[..., Any] = openai_tool_calling_serializer
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

        The process of running the agent is separated in the following steps:
        1. Send the messages to the model in `send_to_openai`. Retrieve model
            run response.

        2. Process the model response in `process_model_response`. If the
            response is a simple text message, `_current_run_messages` will be
            a list of `Message` objects.

        3. Process the tools in `process_tools`. Execute all required tools.
            `_current_run_messages` will be a list containing `ToolUseMessage`
            objects with the `tool_outputs` field populated.

        4. If there is any `ToolUseMessage` in the `_current_run_messages`,
            call `agent_run` again with the updated messages in order to get a
            new response from the model based on the tools outputs.

        Args:
            thread_messages: List of messages in the thread.
            **kwargs: Additional arguments.

        Returns:
           messages: List of messages generated by the agent.

        Examples:
        >>> agent = Agent()
        >>> agent.agent_run([Message(content="Hello",type="text", role="user)])
        [Message(content="This is a Response", role="ai", type="text")]

        """
        if not kwargs.get("calling_from_inside_agent_run"):
            self._current_run_messages = []

        logger.debug("Running OpenAI Agent.") if self.verbose else None

        model_response = self.send_to_openai(thread_messages, **kwargs)
        logger.debug(
            f"Model response: {model_response}\nProcessing it"
        ) if self.verbose else None

        run_messages = self.process_model_response(model_response, **kwargs)
        self._current_run_messages.extend(run_messages)
        thread_messages.extend(run_messages)
        logger.debug(
            f"Model response processed: {run_messages}"
        ) if self.verbose else None

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
        completion: ChatCompletion
        if len(self.tools) > 0:
            logger.debug("Calling agent with tools.") if self.verbose else None
            serialized_tools = [
                self.tools_serializer(tool) for tool in self.tools
            ]
            logger.debug(
                f"Serialized tools: {serialized_tools}"
            ) if self.verbose else None
            completion = client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                tools=serialized_tools,
            )
        else:
            completion = client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
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
        for choice in completion.choices:
            if choice.finish_reason == "stop":
                logger.debug(
                    "Model stopped by it's own."
                ) if self.verbose else None
                # natural stop for the model
                if choice.message.content:
                    response_content: str = choice.message.content
                    response_message = Message(
                        content=response_content,
                        role=MessageRole.AI,
                        type=MessageType.TEXT,
                    )
                    response_messages.append(response_message)
                    return response_messages
                
                else:
                    raise AIAgentCompletionError(
                        "Model stopped without generating any content. "
                        f"Response: \n{choice}"
                    )

            elif choice.finish_reason in ["tool_calls", "function_call"]:
                logger.debug(
                    f"Tool call detected: {choice.finish_reason}"
                ) if self.verbose else None

                lightagents_tool_use_messages = []
                openai_tool_calls_messages = choice.message.tool_calls
                if (
                    openai_tool_calls_messages
                    and len(openai_tool_calls_messages) > 0
                ):
                    for tool_call in openai_tool_calls_messages:
                        if not isinstance(
                            tool_call, ChatCompletionMessageToolCall
                        ):
                            raise AIAgentCompletionError(
                                "Unknown message type for tool call. Received "
                                f"'{type(choice)}', expected "
                                "'ChatCompletionMessageToolCall'."
                            )

                        tool_use_message = ToolUseMessage(
                            run_id=tool_call.id,
                            role=MessageRole.TOOL_USE,
                            type=MessageType.TEXT,
                            external_fields=kwargs,
                            name=tool_call.function.name,
                            input_params_dict=tool_call.function.arguments,
                        )
                        lightagents_tool_use_messages.append(tool_use_message)

                    lightagents_tool_use_messages = self.process_tools(
                        lightagents_tool_use_messages, **kwargs
                    )

                    return lightagents_tool_use_messages

                else:
                    raise AIAgentCompletionError(
                        "Model completion contained a tool call, but no tool "
                        "calls were found."
                    )

            elif choice.finish_reason == "length":
                logger.warning("Model reached maximum token limits.")
                # TODO: handle this cas
                ...
                
                return []

            elif choice.finish_reason == "content_filter":
                # TODO: handle this case
                logger.warning("Model content omitted due to content filter.")
                ...
                return []

            else:
                logger.error(
                    f"Unknown finish reason: '{choice.finish_reason}'"
                )
                return []

        raise AIAgentCompletionError(f"No messages were\n{completion}")
        

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
        updated_tool_use_messages = []
        if self.tools_registry:
            for tool_message in tool_use_messages:
                if isinstance(tool_message.input_params_dict, str):
                    try:
                        args_dict = literal_eval(
                            tool_message.input_params_dict
                        )
                    except ValueError:
                        logger.warning(
                            "Could not parse input args. Using as str."
                        )
                        args_dict = {
                            "response": tool_message.input_params_dict
                        }
                else:
                    args_dict = tool_message.input_params_dict

                try:
                    logger.debug(
                        f"Executing tool: '{tool_message.name}' "
                        f"with args: {args_dict}"
                    ) if self.verbose else None

                    tool_response = self.tools_registry.execute_tool(
                        tool_message.name, args_dict, **kwargs
                    )

                    logger.info(
                        f"Tool returned: \n{tool_response}"
                    ) if self.verbose else None

                    tool_message.tool_outputs = tool_response.content
                    if tool_response.external_fields:
                        tool_message.external_fields.update(
                            tool_response.external_fields
                        )
                    updated_tool_use_messages.append(tool_message)
                    
                except Exception as e:
                    tool_message.is_error = True
                    logger.error(
                        f"Error executing tool: '{tool_message.name}'"
                    )
                    raise ValueError(f"Error executing tool: {e}")
                
        return updated_tool_use_messages
