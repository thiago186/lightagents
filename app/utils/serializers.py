from typing import Any, List,MutableSequence

from app.schemas.messages_schemas import (
    MessageBase,
)


def base_serializer(
    messages:MutableSequence[MessageBase], **kwargs: Any
) -> List[dict[str, str]]:
    """Serialize only messages role and content."""
    if not isinstance(messages, list):
        raise ValueError("The messages must be a list.")

    serialized_messages = []
    for message in messages:
        serialized_messages.append(
            {"content": message.content, "role": message.role.value}
        )
    return serialized_messages


def role_mapping_serializer(
    messages:MutableSequence[MessageBase], **kwargs: Any
) -> List[dict[str, str]]:
    """Serialize only messages role and content.

    It uses a mapping to change the roles to supported values for other LLMs.
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
                {"content": message.content, "role": converted_role}
            )
    return serialized_messages
