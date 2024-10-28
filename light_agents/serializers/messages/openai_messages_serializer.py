from typing import Any, Dict, List, MutableSequence

from light_agents.core.logger_config import setup_logger
from light_agents.exceptions.messages_exceptions import (
    MessageRoleNotSupportedException,
    MessageSupportException,
    MessageTypeNotSupportedException,
)
from light_agents.schemas.messages_schemas import (
    Message,
    MessageBase,
    MessageRole,
    MessageType,
)

logger = setup_logger(__name__)


def openai_text_message_serializer(
    text_message: Message, **kwargs: Any
) -> Dict[str, Any]:
    """Serialize a single text message to OpenAI's API format.

    Warning:
        Handles only text messages.

    The openAI serialized message is a json:
    ```json
    {
        "role": "user/assistant/system",
        "content": [
            {
                "type": "text",
                "text": "Content of the message"
            }
        ]
    }
    ```

    Arguments:
        text_message: The message to be serialized.
        **kwargs: Additional arguments.

    Returns:
        serialized_message: The serialized message

    Examples:
        >>> from light_agents.schemas.messages_schemas import Message, MessageType, MessageRole
        >>> message = Message(
        ...     role=MessageRole.USER,
        ...     type=MessageType.TEXT,
        ...     content="Hello, how are you?"
        ... )
        >>> openai_text_message_serializer(message)
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Hello, how are you?"
                }
            ]
        }

    """  # noqa: E501
    if not isinstance(text_message, Message):
        raise MessageSupportException("Only Message type is supported.")
    if text_message.type != MessageType.TEXT:
        raise MessageTypeNotSupportedException(
            text_message.type, [MessageType.TEXT]
        )

    role_mapping = {
        MessageRole.USER.value: "user",
        MessageRole.AI.value: "assistant",
        MessageRole.SYSTEM.value: "system",
    }
    if "roles_mapping" in kwargs:
        role_mapping = kwargs["roles_mapping"]
    
    message_converted_role = role_mapping.get(text_message.role)
    supported_roles = ["user", "assistant", "system"]
    if message_converted_role not in supported_roles:
        raise MessageRoleNotSupportedException(
            text_message.role, supported_roles
        )

    serialized_message = {
        "role": message_converted_role,
        "content": [
            {
                "type": "text",
                "text": text_message.content,
            }
        ],
    }

    return serialized_message


def openai_messages_list_serializer(
    messages: MutableSequence[MessageBase], **kwargs: Any
) -> List[Dict[str, Any]]:
    """Serialize a series of messages for OpenAI API.

    Handles text messages only.
    """
    serialized_messages = []
    for message in messages:
        if isinstance(message, Message):
            if message.type == MessageType.TEXT:
                serialized_message = openai_text_message_serializer(message)
                serialized_messages.append(serialized_message)
            else:
                logger.warning(
                    f"'{message.type}' message type is not supported."
                    "Message will be ignored."
                )
        else:
            logger.warning(
                f"'{message}' message type is not yet supported."
                "Message will be ignored."
            )
    return serialized_messages
