from typing import List, MutableSequence

from pydantic import Field

from light_agents.ai_agents import OpenAIAgent
from light_agents.schemas import ToolBaseSchema, ToolResponseSchema
from light_agents.schemas.messages_schemas import (
    Message,
    MessageBase,
    MessageRole,
    MessageType,
)
from light_agents.schemas.thread_schema import ThreadBase, ThreadType


# Define the weather tool
class GetWeather(ToolBaseSchema):
    """Tool for getting weather information for a specific location."""

    name: str = "get_weather"
    description: str = "Get the weather for a specific location. Usefull when user asks anything related to weather."  # noqa: E501
    location: str = Field(
        ..., description="The location to get the weather for."
    )

    def run(self, location: str) -> ToolResponseSchema:
        """Run the tool to get the weather for a specific location."""
        return ToolResponseSchema(
            content=f"The weather for {location} is rainy and cold. "
            f"The temperature will be 10 degrees Celsius with heavy rain. "
            f"Don't forget to bring an umbrella and wear warm clothes.",
        )


class Agent2(ToolBaseSchema):
    """Agent routing test."""

    name: str = "code_specialist"
    description: str = "Code specialist agent. Usefull for answering all code related questions. Use this tool every time the user asks a code related question."  # noqa: E501
    required: List[str] = ["user_query"]
    user_query: str = Field("", description="User query to be routed")

    def run(self, user_query: str) -> ToolResponseSchema:
        """Run the tool to this expert agent."""
        tmp_agent = OpenAIAgent()
        msgs: MutableSequence[MessageBase] = tmp_agent.agent_run(
            [
                Message(
                    role=MessageRole.USER,
                    type=MessageType.TEXT,
                    content=user_query,
                )
            ]
        )
        if isinstance(msgs[-1], Message):
            return ToolResponseSchema(content=msgs[-1].content)
        return ToolResponseSchema(
            content="Sorry, i'm not able to answer this question right now."
        )


# Create base conversation messages
msg1 = Message(
    role=MessageRole.USER,
    type=MessageType.TEXT,
    content="Oi! Meu nome é Thiago.",
)

msg2 = Message(
    role=MessageRole.AI, type=MessageType.TEXT, content="Oi! Tudo bem?"
)


# Create thread
thread = ThreadBase(type=ThreadType.BASIC, messages=[msg1, msg2])

# Initialize weather tool
weather_tool = GetWeather(location="")
code_specialist = Agent2(user_query="")

# Initialize Claude agent with weather tool
agent = OpenAIAgent(tools=[weather_tool, code_specialist], verbose=True)

responses = agent.agent_run(thread.messages)
if isinstance(responses[-1], Message):
    print(responses[-1].content)

# Create new user message
new_user_msg = Message(
    role=MessageRole.USER,
    type=MessageType.TEXT,
    content=(
        "Qual a previsão do tempo para amanhã em sao paulo?"
        "Escreva seu resultado em um script python."
    ),
)

new_user_msg = Message(
    role=MessageRole.USER,
    type=MessageType.TEXT,
    content="O que é primitive obsession em python?",
)

# Run conversation with system messages
print("\n----- Conversation with System Messages -----")
responses = agent.agent_run([new_user_msg])
if isinstance(responses[-1], Message):
    print(responses[-1].content)
