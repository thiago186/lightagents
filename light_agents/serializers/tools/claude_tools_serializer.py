from enum import Enum
from typing import Any, Dict

from light_agents.core.logger_config import setup_logger
from light_agents.schemas import ToolBaseSchema, ToolUseMessage
from light_agents.serializers.tools.base_serializers import (
    python_type_to_json_type,
)

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
        if annotation and isinstance(annotation, type) and issubclass(annotation, Enum):
            claude_format["input_schema"]["properties"][param]["enum"] = list(
                annotation.__members__.keys()
            )

    return claude_format


def claude_tool_response_serializer(
    tool: ToolUseMessage, **kwargs: Any
) -> list[Dict[str, Any]]:
    """Serialize a single tool response for the Claude API.

    The function creates both ```assistant``` tool request block and ```user```
    tool response block.

    ```json
    [
        {
            "role": "assistant",
            "content": {
                "type": "tool_use",
                "id": "toolu_XXXXXX",
                "name": "tool_name",
                "input": {"arg1": "value1", "arg2": "value2"}
            }

        },
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
    ]
    ```
    """
    if not isinstance(tool, ToolUseMessage):
        raise ValueError("The tool must be a ToolUseMessage instance.")

    tool_output = tool.tool_outputs
    if not isinstance(tool_output, str):
        logger.warning("The tool output is not a string. Converting to string.")
        tool_output = str(tool.tool_outputs)

    tool_input = tool.input_params_dict
    if not isinstance(tool_input, dict):
        logger.warning("The tool input is not a dictionary. Converting to dictionary.")
        tool_input = {"input": str(tool.input_params_dict)}

    serialized_tool_calling_message = {
        "role": "assistant",
        "content": [
            {
                "type": "tool_use",
                "id": tool.run_id,
                "name": tool.name,
                "input": tool.input_params_dict,
            }
        ],
    }

    serialized_tool_response_message = {
        "role": "user",
        "content": [
            {
                "type": "tool_result",
                "tool_use_id": tool.run_id,
                "content": tool_output,
            }
        ],
    }

    return [serialized_tool_calling_message, serialized_tool_response_message]
