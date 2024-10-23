from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, MutableSequence, Sequence

from pydantic import BaseModel

from light_agents.schemas.messages_schemas import MessageBase, ToolUseMessage
from light_agents.schemas.model_config import model_config
from light_agents.utils.serializers import base_serializer


class ThreadAgent(ABC, BaseModel):
    """Abstract schema for a Thread agent."""

    model_config = model_config
    messages_serializer: Callable[..., List[Dict[str, str]]] = base_serializer
    verbose: bool = False

    @abstractmethod
    def agent_run(
        self, thread_messages: MutableSequence[MessageBase], **kwargs: Any
    ) -> Sequence[MessageBase]:
        """Run the agent."""
        raise NotImplementedError

    @abstractmethod
    def process_tools(
        self, tool_use_messages: List[ToolUseMessage], **kwargs: Any
    ) -> MutableSequence[ToolUseMessage]:
        """Process the tools."""
        raise NotImplementedError
