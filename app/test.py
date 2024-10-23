from pydantic import Field

from app.ai_agents.claude_agent import ClaudeAgent
from app.logger_config import setup_logger
from app.schemas import ToolBaseSchema, ToolResponseSchema
from app.schemas.messages_schemas import Message, MessageRole, MessageType
from app.schemas.thread_schema import ThreadBase, ThreadType
from app.serializers.tools import claude_tool_calling_serializer

message1 = Message(
    role=MessageRole.USER,
    type=MessageType.TEXT,
    content="Oi! Meu nome é Thiago.",
)

message2 = Message(
    role=MessageRole.AI, type=MessageType.TEXT, content="Oi! Tudo bem?"
)

message3 = Message(
    role=MessageRole.USER, type=MessageType.TEXT, content="Sim, e você?"
)

message4 = Message(
    role=MessageRole.USER, type=MessageType.TEXT, content="Qual é meu nome?"
)

thread = ThreadBase(
    type=ThreadType.BASIC, messages=[message1, message2, message3, message4]
)


class GetWeather(ToolBaseSchema):
    name: str = "get_weather"
    description: str = "Get the weather for a specific location."
    # required: list[str] = ["location"]
    location: str = Field(
        ..., description="The location to get the weather for."
    )

    def run(self, location: str) -> ToolResponseSchema:
        """Get the weather for a specific location."""
        
        return ToolResponseSchema(
            content=f"The weather for {location} is sunny.",
        )

get_weather_tool = GetWeather(location="")

import json

print(json.dumps(claude_tool_calling_serializer(get_weather_tool), indent=4))

agent = ClaudeAgent(tools = [get_weather_tool], verbose = True)
# agent.agent_run([message1])
# thread.process_thread(agent)
# w = agent.agent_run(thread.messages)

msg6 = Message(
    role = MessageRole.USER,
    content = "Eu moro em são paulo, qual a previsão do tempo?",
    type = MessageType.TEXT
)
agent.agent_run([msg6])
# thread.add_message(msg6)
# thread.process_thread(agent)
# print("----- Conversation ------")
# for message in thread.messages:
#     print(f"{message.role}: {message.content}")