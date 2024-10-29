from typing import Any


class MessageSupportException(ValueError):
    """Exception raised for unsupported messages.

    Usefull for every error that involves message types or roles.
    """
    
    def __init__(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Initialize the exception."""
        super().__init__(message)


class MessageTypeNotSupportedException(MessageSupportException):
    """Exception raised for unsupported message types."""

    def __init__(self, message_type: str, supported_types: list[Any]) -> None:
        """Initialize the exception."""
        self.message_type = message_type
        self.supported_types = supported_types
        super().__init__(
            f"Message type '{message_type}' is not supported. "
            f"Supported types are: {supported_types}"
        )


class MessageRoleNotSupportedException(MessageSupportException):
    """Exception raised for unsupported message roles."""

    def __init__(self, message_role: str, supported_roles: list[Any]) -> None:
        """Initialize the exception."""
        self.message_role = message_role
        self.supported_roles = supported_roles
        super().__init__(
            f"Message role '{message_role}' is not supported. "
            f"Supported roles are: {supported_roles}"
        )
