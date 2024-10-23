from typing import Any, Dict, List,MutableSequence

from app.logger_config import setup_logger
from app.schemas.messages_schemas import (
    Message,
    MessageBase,
    MessageRole,
    MessageType,
    ToolUseMessage,
)
from app.serializers.tools.claude_tools_serializer import (
    claude_tool_response_serializer,
)

logger = setup_logger(__name__)


def claude_text_message_serializer(
    message: Message, **kwargs: Any
) -> Dict[str, Any]:
    """Seriliaze a single message for Claude API.

    Handles only text messages.

    Expected return:
    ```json
    {
        "role": "user/assistant",
        "content": [
            {
                "type": "text",
                "text": "message content"
            }
        ]
    }
    ```

    *It works for default claude SDK. Not tested with Bedrock Claude.*

    """
    role_mapping = {
        MessageRole.USER.value: "user",
        MessageRole.AI.value: "assistant",
    }
    if "roles_mapping" in kwargs:
        role_mapping = kwargs["roles_mapping"]

    if message.type != MessageType.TEXT:
        raise ValueError("Only text messages are supported.")

    if not role_mapping.get(message.role):
        raise ValueError(f"Role '{message.role}' is not supported.")

    serialized_message = {
        "user": role_mapping.get(message.role),
        "content": message.content,
    }

    return serialized_message


def claude_messages_serializer(
    messages:MutableSequence[MessageBase], **kwargs: Any
) -> List[Dict[str, Any]]:
    """Serialize a series of messages for Claude API.

    Handles text messages and tool use messages.
    """
    serialized_messages = []
    for message in messages:
        if isinstance(message, Message):
            if message.type == MessageType.TEXT:
                ##TODO: handle text messages
                serialized_message = claude_text_message_serializer(
                    message, **kwargs
                )
                serialized_messages.append(serialized_message)
            else:
                logger.warning(
                    f"'{message.type}' message type is not supported."
                    "Message will be ignored."
                )

        elif isinstance(message, ToolUseMessage):
            serialized_messages.append(claude_tool_response_serializer(message))

        else:
            logger.warning(
                f"'{type(message)}' message type is not supported."
                "Message will be ignored."
            )

    return serialized_messages


def bedrock_claude_messages_serializer(
    messages:MutableSequence[MessageBase], **kwargs: Any
) -> List[Dict[str, str]]:
    """Serialize messages for Bedrock Claude model.

    Return example:
    ```json
    [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "message content
                }
            ]
        }
    ]
    ```

    0. If a roles_mapping is provided, it will be used for role mapping.
    1. The roles must alternate between user and assistant.
        If there is two user messages inMutableSequence, they will be included inside
        "content" list.
    2. If there is any, only the first system message will be considered.
    """
    if not isinstance(messages, list):
        raise ValueError("The messages must be a list.")

    roles_mapping = MessageRole.get_roles_mapping()
    if "roles_mapping" in kwargs:
        roles_mapping = kwargs["roles_mapping"]

    serialized_messages = []
    current_message: Dict[str, Any] = {"role": None, "content": []}
    for message in messages:
        # TODO: Handle when last message is tool use or media message
        if isinstance(message, Message):
            current_role = roles_mapping.get(message.role, None)
            if current_role:
                if current_role == current_message["role"]:
                    if message.type == MessageType.TEXT:
                        current_message["content"].append(
                            {"type": "text", "text": message.content}
                        )
                    else:
                        # TODO: Gracefully handle other message types.
                        print("Only text messages are supported for now.")
                else:
                    if current_message.get("role", None):
                        serialized_messages.append(current_message)
                    current_message = {
                        "role": current_role,
                        "content": [{"type": "text", "text": message.content}],
                    }
    # TODO: Handle when last message is tool use or media message
    if isinstance(message, Message):
        serialized_messages.append(current_message)
    return serialized_messages
