from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List,MutableSequence

from pydantic import BaseModel

from app.schemas.messages_schemas import MessageBase, ToolUseMessage
from app.schemas.model_config import model_config
from app.utils.serializers import base_serializer


class ThreadAgent(ABC, BaseModel):
    """Abstract schema for a Thread agent."""

    model_config = model_config
    messages_serializer: Callable[..., List[Dict[str, str]]] = (
        base_serializer
    )
    verbose: bool = False

    @abstractmethod
    def agent_run(
        self, thread_messages:MutableSequence[MessageBase], **kwargs: Any
    ) ->MutableSequence[MessageBase]:
        """Run the agent."""
        raise NotImplementedError

    @abstractmethod
    def process_tools(
        self, tool_use_messages: List[ToolUseMessage], **kwargs: Any
    ) -> List[ToolUseMessage]:
        """Process the tools."""
        raise NotImplementedError
