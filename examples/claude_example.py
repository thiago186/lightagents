from pydantic import Field

from light_agents.ai_agents.claude_agent import ClaudeAgent
from light_agents.schemas import ToolBaseSchema, ToolResponseSchema
from light_agents.schemas.messages_schemas import (
    Message,
    MessageRole,
    MessageType,
)
from light_agents.schemas.thread_schema import ThreadBase, ThreadType


# Define the weather tool
class GetWeather(ToolBaseSchema):
    """Tool for getting weather information for a specific location."""

    name: str = "get_weather"
    description: str = "Get the weather for a specific location."
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

try:
    # Initialize Claude agent with weather tool
    agent = ClaudeAgent(tools=[weather_tool], verbose=True)

    responses = agent.agent_run(thread.messages)
    if isinstance(responses[-1], Message):
        print(responses[-1].content)

    system_msg = Message(
        role=MessageRole.SYSTEM,
        type=MessageType.TEXT,
        content="You're a helpful assistant. But you talk like a pirate. Always respond like a pirate!",  # noqa: E501
    )

    # Create new user message
    new_user_msg = Message(
        role=MessageRole.USER,
        type=MessageType.TEXT,
        content="Tudo bom? quem é você?",
    )

    # Run conversation with system messages
    print("\n----- Conversation with System Messages -----")
    responses = agent.agent_run([new_user_msg, system_msg])
    if isinstance(responses[-1], Message):
        print(responses[-1].content)

except Exception as e:
    print(f"Error in Claude script: {str(e)}")
