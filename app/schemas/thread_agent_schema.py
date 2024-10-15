from typing import Any, Callable, Dict, List

from pydantic import BaseModel

from app.schemas.messages_schemas import Message
from app.schemas.model_config import model_config
from app.utils.serializers import base_serializer


class ThreadAgent(BaseModel):
    """Abstract schema for a Thread agent."""

    model_config=model_config
    serializer: Callable[[List[Message]], List[Dict[str, str]]] = (
        base_serializer
    )

    def agent_run(
        self, thread_messages: List[Message], **kwargs: Any
    ) -> Message:
        """Run the agent."""
        raise NotImplementedError

    def process_tools(self, **kwargs: Any) -> None:
        """Process the tools."""
        raise NotImplementedError
