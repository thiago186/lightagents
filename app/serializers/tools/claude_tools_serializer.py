from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from app.serializers.tools.base_serializers import python_type_to_json_type


class Tool(BaseModel):
    name: str = Field(..., description="The name of the function")
    description: str = Field(
        ..., description="A brief description of what the function does"
    )
    required: list[str] = Field(default=[], description="The required fields")

    class Config:
        extra = "allow"


def claude_serializer(llm_function: Tool) -> Dict[str, Any]:
    function_dict = llm_function.model_dump(
        exclude={"name", "description", "required"}
    )

    claude_format: Dict[str, Any] = {
        "name": llm_function.name,
        "description": llm_function.description,
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": llm_function.required,
        },
    }

    for param in function_dict.keys():
        param_type = python_type_to_json_type(function_dict[param])
        claude_format["input_schema"]["properties"][param] = {
            "type": param_type,
            "description": llm_function.model_fields[param].description,
        }

        annotation = llm_function.model_fields[param].annotation
        if annotation and issubclass(annotation, Enum):  # mypy: ignore
            claude_format["input_schema"]["properties"][param]["enum"] = list(
                llm_function.model_fields[param].annotation.__members__.keys()
            ) # mypy: ignore

    return claude_format


class Approximate(str, Enum):
    YES = "yes"
    NO = "no"


# Exemplo de uso
class GetWeather(Tool):
    name: str = "get_weather"
    description: str = "Get the current weather in a given location"
    location: str = Field(
        default="", description="The city and state, e.g. San Francisco, CA"
    )
    apprx: Approximate = Field(
        default=Approximate.NO, description="Approximate the weather"
    )


get_weather = GetWeather()

# Serializar para o formato do Claude
claude_format = claude_serializer(get_weather)
print(claude_format)
