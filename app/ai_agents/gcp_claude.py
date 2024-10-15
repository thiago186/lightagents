from enum import Enum
from typing import Any

from anthropic import AnthropicVertex

from app.config import appSettings
from app.schemas.messages_schemas import Message, MessageRole, MessageType
from app.schemas.thread_agent_schema import ThreadAgent
from app.schemas.thread_schema import ThreadBase
from app.utils.serializers import role_mapping_serializer

client = AnthropicVertex(
    project_id=appSettings.GCP_PROJECT_ID,
    region=appSettings.GCP_REGION
    )

class ModelMessageRoles(Enum):
    """Message roles for the model."""
    
    USER="user"
    AI="assistant"
    
    
    @staticmethod
    def get_role_mapping() -> dict[str, str]:
        """Get the role mapping."""
        return {
            MessageRole.USER.value: ModelMessageRoles.USER.value,
            MessageRole.AI.value: ModelMessageRoles.AI.value
        }
    
    
class ClaudeAgent(ThreadAgent):
    """Claude agent."""

    model: str = "claude-3-5-sonnet@20240620"
    max_tokens: int = 8192
    serializer = role_mapping_serializer
    
    def agent_run(
        self, thread_messages: list[Message], **kwargs: Any
        ) -> Message:
        """Run the agent."""
        serialized_messages = self.serializer(
            thread_messages,
            **{"roles_mapping": ModelMessageRoles.get_role_mapping()}
            )
        
        prompt = {
            "role": ModelMessageRoles.USER.value,
            "content": "Yoiu're a helpfull assistant of payssego. Your name is Guildo."
        }
        
        serialized_messages.insert(0, prompt)
        response = client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=serialized_messages #type: ignore
        )
        message = Message(
            role=MessageRole.AI,
            type=MessageType.TEXT,
            content=response.content[0].text #type: ignore
        )
        return message
        
    def process_tools(self, **kwargs: Any) -> None:
        """Process the tools."""
        
        print("Processing tools.")
        
        for key, value in kwargs.items():
            print(f"Key: {key}, value: {value}")
        
        print("Tools processed.")
        