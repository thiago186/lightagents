from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel

from app.schemas.model_config import model_config


class MessageRole(str, Enum):
    """Possible roles for a single message."""
    
    USER="user"
    SYSTEM="system"
    AI="ai"
    
    @staticmethod
    def get_roles_mapping() -> dict[str, str]:
        """Get the role mapping."""
        return {
            MessageRole.USER.value: "user",
            MessageRole.SYSTEM.value: "system",
            MessageRole.AI.value: "ai"
        }
    
    
class MessageType(str, Enum):
    """Possible types for a single message."""
    
    TEXT="text"
    IMAGE="image"
    VIDEO="video"
    AUDIO="audio"
    FILE="file"
    
class Message(BaseModel):
    """A single message."""
    
    model_config = model_config
    role: MessageRole
    type: MessageType
    content: str
    timestamp: Optional[datetime] = datetime.now(timezone.utc)
    
class MediaMessage(Message):
    """A single media message."""
    
    media_url: str