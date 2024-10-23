from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional, Union

from pydantic import BaseModel

from src.schemas.model_config import model_config


class MessageRole(str, Enum):
    """Possible roles for a single message."""

    USER = "user"
    SYSTEM = "system"
    AI = "ai"
    TOOL_USE = "tool_use"

    @staticmethod
    def get_roles_mapping() -> dict[str, str]:
        """Get the role mapping."""
        return {
            MessageRole.USER.value: "user",
            MessageRole.SYSTEM.value: "system",
            MessageRole.AI.value: "ai",
        }


class MessageType(str, Enum):
    """Possible types for a single message."""

    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    FILE = "file"


class MessageBase(BaseModel):
    """A single message."""

    model_config = model_config
    role: MessageRole
    type: MessageType
    external_fields: dict[str, Any] = {}
    """Fields to be returned for the thread outside LLM."""


class Message(MessageBase):
    """A single message.

    Attributes
    ----------
        content: the content of the message to be passed to the LLM
        timestamp: the timestamp of message creation

    """

    model_config = model_config
    content: str
    timestamp: Optional[datetime] = datetime.now(timezone.utc)


class ToolUseMessage(MessageBase):
    """Message for a LLM function calling.

    Attributes
    ----------
        run_id: the run id of the tool
        name: the name of the tool
        input_params_dict: the input parameters of the tool
        tool_outputs: the output of the tool
        is_error: flag to indicate if the tool execution was an error

    """

    run_id: str
    name: str
    input_params_dict: Union[str, dict[str, Any]]
    tool_outputs: Optional[Any] = None
    is_error: Optional[bool] = False


class MediaMessage(Message):
    """A single media message."""

    media_url: str
