import json

from pydantic import Field

from light_agents.ai_agents.claude_agent import ClaudeAgent
from light_agents.schemas import ToolBaseSchema, ToolResponseSchema
from light_agents.schemas.messages_schemas import (
    Message,
    MessageRole,
    MessageType,
)
from light_agents.schemas.thread_schema import ThreadBase, ThreadType
from light_agents.serializers.tools import claude_tool_calling_serializer


class GetWeather(ToolBaseSchema):
    """Get the weather for a specific location."""
    
    name: str = "get_weather"
    description: str = "Get the weather for a specific location."
    # required: list[str] = ["location"]
    location: str = Field(
        ..., description="The location to get the weather for."
    )

    def run(self, location: str) -> ToolResponseSchema:
        """Get the weather for a specific location."""
        return ToolResponseSchema(
            content=f"The weather for {location} is rainy and cold. The temperature will be 10 degrees Celsius with heavy rain. Don't forget to bring an umbrella and wear warm clothes.",  # noqa: E501
        )


msg1 = Message(
    role=MessageRole.USER,
    type=MessageType.TEXT,
    content="Oi! Meu nome é Thiago.",
)

msg2 = Message(
    role=MessageRole.AI, type=MessageType.TEXT, content="Oi! Tudo bem?"
)

msg3 = Message(
    role=MessageRole.USER, type=MessageType.TEXT, content="Sim, e você?"
)

msg4 = Message(
    role=MessageRole.USER, type=MessageType.TEXT, content="Qual é meu nome?"
)

thread = ThreadBase(type=ThreadType.BASIC, messages=[msg1, msg2, msg3, msg4])

get_weather_tool = GetWeather(location="")


print(json.dumps(claude_tool_calling_serializer(get_weather_tool), indent=4))
if __name__ == "__main__":
    agent = ClaudeAgent(tools=[get_weather_tool], verbose=True)
    # agent = ClaudeAgent(verbose = True)
    # agent.agent_run([message1])
    # thread.process_thread(agent)
    # w = agent.agent_run(thread.messages)

    msg6 = Message(
        role=MessageRole.USER,
        content="Eu moro em são paulo, qual a previsão do tempo?",
        type=MessageType.TEXT,
    )

    system_msg = Message(
        role=MessageRole.SYSTEM,
        content="You're a helpfull assistant. keep your answers short and direct. try to use maximum 3 words.", # noqa: E501
        type=MessageType.TEXT,
    )

    system_msg2 = Message(
        role=MessageRole.SYSTEM,
        content="You're a helpfull assistant. But you talks like a pirate. Always respond like a pirate!", # noqa: E501
        type=MessageType.TEXT,
    )

    run_msgs = agent.agent_run([msg6, system_msg2, system_msg])
    print(run_msgs[-1])
    # agent.agent_run([msg1])
    # thread.add_message(msg6)
    # thread.process_thread(agent)
    # print("----- Conversation ------")
    # for message in thread.messages:
    #     print(f"{message.role}: {message.content}")
