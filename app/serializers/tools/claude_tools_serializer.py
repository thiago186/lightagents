from enum import Enum
from typing import Any, Dict

from app.logger_config import setup_logger
from app.schemas import ToolBaseSchema, ToolUseMessage
from app.serializers.tools.base_serializers import python_type_to_json_type

logger = setup_logger(__name__)


def claude_tool_calling_serializer(
    llm_function: ToolBaseSchema,
) -> Dict[str, Any]:
    """Serialize a ToolBaseSchema into Claude API format."""
    function_dict = llm_function.model_dump(
        exclude={"name", "description", "required", "json_response"}
    )

    claude_format: Dict[str, Any] = {
        "name": llm_function.name,
        "description": llm_function.description,
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    }

    if llm_function.required and len(llm_function.required) > 0:
        claude_format["input_schema"]["required"] = llm_function.required

    for param in function_dict.keys():
        param_type = python_type_to_json_type(function_dict[param])
        claude_format["input_schema"]["properties"][param] = {
            "type": param_type,
            "description": llm_function.model_fields[param].description,
        }

        annotation = llm_function.model_fields[param].annotation
        if (
            annotation
            and isinstance(annotation, type)
            and issubclass(annotation, Enum)
        ):
            claude_format["input_schema"]["properties"][param]["enum"] = list(
                annotation.__members__.keys()
            )

    return claude_format


def claude_tool_response_serializer(
    tool: ToolUseMessage, **kwargs: Any
) -> Dict[str, Any]:
    """Serialize a single tool response for the Claude API.

    ```json
    {
        "role": "user",
        "content": [
            {
                "type": "tool_result",
                "tool_use_id": "toolu_XXXXXX",
                "content": "the content to be passed to LLM"
            }
        ]
    }
    ```
    """
    if not isinstance(tool, ToolUseMessage):
        raise ValueError("The tool must be a ToolUseMessage instance.")

    tool_output = tool.tool_outputs
    if not isinstance(tool_output, str):
        logger.warning(
            "The tool output is not a string. Converting to string."
        )
        tool_output = str(tool.tool_outputs)

    serialized_tool_message = {
        "role": "user",
        "content": [
            {
                "type": "tool_result",
                "tool_use_id": tool.run_id,
                "content": tool_output,
            }
        ],
    }

    return serialized_tool_message
