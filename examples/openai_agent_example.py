from light_agents.ai_agents.openai_agent import OpenAIAgent
from light_agents.schemas.messages_schemas import (
    Message,
    MessageRole,
    MessageType,
)
from light_agents.schemas.thread_schema import ThreadBase, ThreadType

# Create base conversation messages
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

# Create thread
thread = ThreadBase(type=ThreadType.BASIC, messages=[])

#Add a list of messages to the thread
thread.add_messages_list([msg1, msg2, msg3, msg4])

agent = OpenAIAgent(verbose=True)

# Create system messages for personality
system_msg = Message(
    role=MessageRole.SYSTEM,
    type=MessageType.TEXT,
    content="You're a helpful assistant. But you talk like a pirate. Always respond like a pirate!", # noqa: E501
)

thread.add_message(system_msg)

# Run conversation with system messages
print("\n----- Conversation with System Messages -----")
responses = agent.agent_run(thread.messages)
print(responses)
