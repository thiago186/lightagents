from typing import Any, Dict, List

from app.schemas.messages_schemas import Message, MessageRole, MessageType


def base_serializer(
    messages: List[Message], **kwargs: Any
    ) -> List[dict[str, str]]:
    """Serialize only messages role and content."""
    if not isinstance(messages, list):
        raise ValueError("The messages must be a list.")

    serialized_messages = []
    for message in messages:
        serialized_messages.append(
                {
                    "content": message.content,
                    "role": message.role.value
                }
            )
    return serialized_messages

def role_mapping_serializer(
    messages: List[Message], **kwargs: Any
    ) -> List[dict[str, str]]:
    """Serialize only messages role and content.
    
    It uses a mapping to change the roles to supported values in outside models.
    If a role is not in the mapping, it will be ignored.
    """
    if "roles_mapping" not in kwargs:
        raise ValueError("'roles_mapping' dict must be provided.")
    
    if not isinstance(messages, list):
        raise ValueError("The messages must be a list.")
    serialized_messages = []
    for message in messages:
        converted_role = kwargs["roles_mapping"].get(message.role, None)
        if converted_role:
            serialized_messages.append(
                        {
                            "content": message.content,
                            "role": converted_role
                        }
                    )
    return serialized_messages

def bedrock_claude_serializer(
    messages: List[Message], **kwargs: Any
    ) -> List[dict[str, str]]:
    """Serialize messages for Bedrock Claude model.
    
    Return example:
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
    
    0. If a roles_mapping is provided, it will be used for role mapping.
    1. The roles must alternate between user and assistant.
        If there is two user messages in sequence, they will be included inside
        "content" list.
    2. If there is any, only the first system message will be considered.
    """
    if not isinstance(messages, list):
        raise ValueError("The messages must be a list.")
    
    roles_mapping = MessageRole.get_roles_mapping()
    if "roles_mapping" in kwargs:
        roles_mapping = kwargs["roles_mapping"]
    
    serialized_messages = []
    current_message: Dict[str, Any] = {
        "role": None,
        "content": []
    }
    for message in messages:
        current_role = roles_mapping.get(message.role, None)
        if current_role:
            if current_role == current_message["role"]:
                if message.type == MessageType.TEXT:
                    current_message["content"].append(
                        {
                            "type": "text",
                            "text": message.content
                        }
                    )
                else:
                    #TODO: Gracefully handle other message types.
                    print(
                        "Only text messages are supported for now."
                    )
            else:
                if current_message.get("role", None):
                    serialized_messages.append(current_message)
                current_message = {
                    "role": current_role,
                    "content": [
                        {
                            "type": "text",
                            "text": message.content
                        }
                    ]
                }
    serialized_messages.append(current_message)
    return serialized_messages