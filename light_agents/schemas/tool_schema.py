from abc import ABC, abstractmethod
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ToolBaseSchema(ABC, BaseModel):
    """Base schema for a Tool used in LLM."""

    model_config = ConfigDict(extra="allow")
    name: str = Field(..., description="The name of the function")
    description: str = Field(
        ..., description="A brief description of what the function does"
    )
    json_response: Optional[bool] = Field(
        default=False, description="Flag to indicate if the response is a JSON"
    )
    required: Optional[List[str]] = Field(default=[], description="The required fields")

    @abstractmethod
    def run(self, *args: Any, **kwargs: Any) -> "ToolResponseSchema":
        """Python  function to be executed when the tool is called."""
        pass


class ToolResponseSchema(BaseModel):
    """Base schema for a Tool response used by an LLM."""

    content: str
    """String content to be returned by the tool to the LLM.
     
     It can include any content or extra prompt to guide the LLM based on the
     tool's output.
     """

    external_fields: Optional[dict[str, Any]] = {}
    """External fields to be returned for the thread.
     
     Returns extra information and update thread fields based on
     the tool's output, without feeding the LLM with the content.
     Usefull for passing sensitive information to prevent prompt injection. 
     """

    is_error: Optional[bool] = False
    """Flag to indicate if the tool response is an error."""
