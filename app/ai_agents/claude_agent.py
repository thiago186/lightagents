from enum import Enum
from typing import Any, Callable

from anthropic import AnthropicBedrock

from app.config import appSettings
from app.logger_config import setup_logger
from app.schemas.messages_schemas import Message, MessageRole, MessageType
from app.schemas.thread_agent_schema import ThreadAgent
from app.schemas.thread_schema import ThreadBase
from app.utils.serializers import role_mapping_serializer

logger = setup_logger(__name__)

# client = AnthropicVertex(
#     project_id=appSettings.GCP_PROJECT_ID,
#     region=appSettings.GCP_REGION
#     )
# MODEL_ID = "claude-3-5-sonnet@20240620"

client = AnthropicBedrock(
    aws_access_key=appSettings.AWS_ACCESS_KEY,
    aws_secret_key=appSettings.AWS_SECRET_KEY,
)
MODEL_ID = "anthropic.claude-3-5-sonnet-20240620-v1:0"


class ModelMessageRoles(Enum):
    """Message roles for the model."""

    USER = "user"
    AI = "assistant"

    @staticmethod
    def get_role_mapping() -> dict[str, str]:
        """Get the role mapping."""
        return {
            MessageRole.USER.value: ModelMessageRoles.USER.value,
            MessageRole.AI.value: ModelMessageRoles.AI.value,
        }


class ClaudeAgent(ThreadAgent):
    """Claude agent."""

    model: str = MODEL_ID
    max_tokens: int = 8192
    serializer: Callable[..., Any] = role_mapping_serializer
    verbose: bool = True

    def agent_run(
        self, thread_messages: list[Message], **kwargs: Any
    ) -> Message:
        """Run the agent."""
        serialized_messages = self.serializer(
            thread_messages,
            **{"roles_mapping": ModelMessageRoles.get_role_mapping()},
        )
        if self.verbose:
            logger.debug(f"Serialized messages: {serialized_messages}")

        response = client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=serialized_messages,
        )
        message = Message(
            role=MessageRole.AI,
            type=MessageType.TEXT,
            content=response.content[0].text,  # type: ignore
        )
        logger.debug(f"Agent response: {message.content}")

        return message

    def process_tools(self, **kwargs: Any) -> None:
        """Process the tools."""
        print("Processing tools.")

        for key, value in kwargs.items():
            print(f"Key: {key}, value: {value}")

        print("Tools processed.")
