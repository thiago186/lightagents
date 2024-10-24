from enum import Enum
from typing import Any, Dict, MutableSequence, Sequence

from pydantic import BaseModel

from light_agents.schemas.messages_schemas import MessageBase
from light_agents.schemas.model_config import model_config
from light_agents.schemas.thread_agent_schema import ThreadAgent


class ThreadType(str, Enum):
    """Possible types for a single Thread."""

    BASIC = "basic"


class ThreadBase(BaseModel):
    """Base schema for a Thread."""

    model_config = model_config
    type: ThreadType
    messages: MutableSequence[MessageBase] = []
    external_thread_fields: Dict[str, Any] = {}

    def add_message(self, message: MessageBase) -> None:
        """Add a message to the thread."""
        if not isinstance(message, MessageBase):
            raise ValueError("The message must be an instance of MessageBase.")

        self.messages.append(message)

    def add_messages_list(
        self, messages: Sequence[MessageBase]
    ) -> None:
        """Add a list of messages to the thread."""
        if not all(isinstance(message, MessageBase) for message in messages):
            raise ValueError("All messages must be instances of MessageBase.")

        for message in messages:
            self.add_message(message)

    def process_thread(self, thread_agent: ThreadAgent) -> None:
        """Process the thread."""
        if not isinstance(thread_agent, ThreadAgent):
            raise ValueError(
                "The thread agent must be an instance of ThreadAgent."
            )

        ## TODO:
        ## 1. Deal gracefully with exceptions
        ## 2. Update external thread fields based on the agent's output
        messages = thread_agent.agent_run(
            self.messages, **self.external_thread_fields
        )
        self.add_messages_list(messages)
