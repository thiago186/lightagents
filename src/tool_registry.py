from typing import Any, Callable, Dict, List

from src.logger_config import setup_logger
from src.schemas.tool_schema import ToolBaseSchema, ToolResponseSchema

logger = setup_logger(__name__)


class ToolRegistry:
    """Registry for tools that can be used by AI agents.

    This registry converts tools defined in the Pydantic model into
    callables that can be used by AI agents.
    """

    def __init__(self) -> None:
        """Initialize the ToolRegistry class."""
        self.tools: Dict[str, Callable[..., ToolResponseSchema]] = {}

    def register(self, tool: ToolBaseSchema) -> None:
        """Register a tool using its name and run method."""
        self.tools[tool.name] = tool.run

    def register_tools(self, tools: List[ToolBaseSchema]) -> None:
        """Register a list of tools."""
        for tool in tools:
            self.register(tool)

    def execute_tool(
        self, tool_name: str, args: Dict[str, Any], **kwargs: Any
    ) -> ToolResponseSchema:
        """Execute a tool with arguments given inside a dict.

        If any kwargs are given and they overlap with args, the args will be
        updated with the kwargs.
        """
        if tool_name not in self.tools:
            # To prevent error, tells the LLM that the tool wasn't available
            return ToolResponseSchema(
                content="<INTERNAL> This tool was not available </INTERNAL>",
                is_error=True,
            )

        tool = self.tools[tool_name]
        args.update(kwargs)

        if kwargs.get("verbose"):
            logger.debug(f"Executing tool '{tool_name}' with args: {args}")

        try:
            result = tool(**args)

            if not isinstance(result, ToolResponseSchema):
                raise ValueError(
                    f"Tool '{tool_name}' should return a ToolResponseSchema"
                )

            return result
        except Exception as e:
            logger.error(f"Error executing tool '{tool_name}': {e}")
            raise ValueError(f"Error executing tool '{tool_name}': {e}")
