from enum import Enum
from typing import Any, Dict

from pydantic import BaseModel

from app.schemas.messages_schemas import Message
from app.schemas.model_config import model_config
from app.schemas.thread_agent_schema import ThreadAgent


class ThreadType(str, Enum):
    """Possible types for a single Thread."""

    BASIC = "basic"


class ThreadBase(BaseModel):
    """Base schema for a Thread."""

    model_config=model_config
    type: ThreadType
    messages: list[Message] = []
    external_thread_fields: Dict[str, Any] = {}
    
    def add_message(self, message: Message) -> None:
        """Add a message to the thread."""
        self.messages.append(message)

    def process_thread(self, thread_agent: ThreadAgent) -> None:
        """Process the thread."""
        if not isinstance(thread_agent, ThreadAgent):
            raise ValueError("The thread agent must be an instance of ThreadAgent.")
        
        thread_agent.agent_run(self.messages, **self.external_thread_fields)
