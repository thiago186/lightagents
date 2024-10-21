from enum import Enum
from typing import Any


def python_type_to_json_type(value: Any) -> str:
    """Convert a Python type to a JSON type."""
    if isinstance(value, str):
        return "string"
    elif isinstance(value, (int, float)):
        return "number"
    elif isinstance(value, bool):
        return "boolean"
    elif isinstance(value, (list, tuple)):
        return "array"
    elif isinstance(value, dict):
        return "object"
    elif isinstance(value, Enum):
        return "enum"
    elif value is None:
        return "null"
    else:
        return "string"

