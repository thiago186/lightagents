class AIAgentCompletionError(Exception):
    """Exception raised when an AI agent fails to complete a task."""

    def __init__(self, message: str) -> None:
        """Initialize the exception."""
        super().__init__(message)
        self.message = message
