from enum import Enum
from typing import Any, Dict

from light_agents.core.logger_config import setup_logger
from light_agents.schemas import ToolBaseSchema, ToolUseMessage
from light_agents.serializers.tools.base_serializers import (
    python_type_to_json_type,
)

logger = setup_logger(__name__)


def openai_tool_calling_serializer(
    llm_function: ToolBaseSchema,
) -> Dict[str, Any]:
    """Serialize a single `ToolBaseSchema` into OpenAI API format.

    OpenAI tool schema looks like this:
    ```json
        {
            "type": "function",
            "function": {
                "name": "get_delivery_date",
                "description": "Get the delivery date for a customer's order.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "order_id": {
                            "type": "string",
                            "description": "The customer's order ID.",
                        },
                    },
                    "required": ["order_id"],
                    "additionalProperties": false,
                },
            }
    }
    ```
    """
    # TODO: Implemment JSON structured mode.
    function_dict = llm_function.model_dump(
        exclude={"name", "description", "required", "json_response"}
    )

    serialized_tool: Dict[str, Any] = {
        "type": "function",
        "function": {
            "name": llm_function.name,
            "description": llm_function.description,
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    }

    if llm_function.required and len(llm_function.required) > 0:
        serialized_tool["function"]["parameters"]["required"] = (
            llm_function.required
        )

    for param in function_dict.keys():
        json_param_type = python_type_to_json_type(function_dict[param])
        serialized_tool["function"]["parameters"]["properties"][param] = {
            "type": json_param_type,
            "description": llm_function.model_fields[param].description,
        }

        annotation = llm_function.model_fields[param].annotation
        if (
            annotation
            and isinstance(annotation, type)
            and issubclass(annotation, Enum)
        ):
            serialized_tool["function"]["parameters"]["properties"][param][
                "enum"
            ] = list(annotation.__members__.keys())

    return serialized_tool


def openai_tooL_response_serializer(
    tool: ToolUseMessage, **kwargs: Any
) -> list[Dict[str, Any]]:
    """Serialize a single tool response for the OpenAI API.

    The function creates both ```assistant``` tool request block and ```user```
    ```json
    [
        {
            "role": "assistant",
            "tool_calls": [
                {
                    "id": "call_xxxx",
                    "type": "function",
                    "function": {
                        "arguments": {"key1": "value1", "key2": "value2"},
                        "name": "tool_name",
                    }
                }
            ]
        },
        {
            "role": "tool",
            "content": "tool_response_content",
            "tool_call_id": "call_xxxx"
        }
    ]
    ```
    """
    if not isinstance(tool, ToolUseMessage):
        raise ValueError("tool must be an instance of ToolUseMessage.")

    tool_output = tool.tool_outputs
    # TODO: gracefully handle non-string tool_output
    if not isinstance(tool_output, str):
        logger.warning("Tool output is not a string. Converting it to string.")
        tool_output = str(tool_output)

    serialized_tool_calling_message = {
        "role": "assistant",
        "tool_calls": [
            {
                "id": tool.run_id,
                "type": "function",
                "function": {
                    "arguments": tool.input_params_dict,
                    "name": tool.name,
                },
            }
        ],
    }

    serialized_tool_response_message = {
        "role": "tool",
        "content": tool_output,
        "tool_call_id": tool.run_id,
    }

    return [serialized_tool_calling_message, serialized_tool_response_message]
