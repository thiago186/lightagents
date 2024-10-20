from app.ai_agents.claude_agent import ClaudeAgent
from app.logger_config import setup_logger
from app.schemas.messages_schemas import Message, MessageRole, MessageType
from app.schemas.thread_schema import ThreadBase, ThreadType
from app.utils.serializers import bedrock_claude_serializer

message1 = Message(
    role=MessageRole.USER,
    type=MessageType.TEXT,
    content="Oi! Meu nome é Thiago."
)

# db = mongoDb()
# numero = message1.from_

# if db.find_one({"numero": numero}):
#     thread = db.find_one({"numero": numero})["thread"]
#     thread.add_message(message1)
#     answer  = thread.process_thread(agent)
#     send_to_user(answer)
#     db.update({"numero": numero}, {"thread": thread})
# else: 
#     thread = ThreadBase(
#         type=ThreadType.BASIC,
#         messages=[message1]
#     )
#     thread.add_message(message1)
#     answer  = thread.process_thread(agent)
#     send_to_user(answer)
#     db.update({"numero": numero}, {"thread": thread})
    

message2 = Message(
    role=MessageRole.AI,
    type=MessageType.TEXT,
    content="Oi! Tudo bem?"
)

message3 = Message(
    role=MessageRole.USER,
    type=MessageType.TEXT,
    content="Sim, e você?"
)

message4 = Message(
    role=MessageRole.USER,
    type=MessageType.TEXT,
    content="Qual é meu nome?"
)

message5 = Message(
    role=MessageRole.USER,
    type=MessageType.TEXT,
    content="Quem é você e qual seu nome?"
)

thread = ThreadBase(
    type=ThreadType.BASIC,
    messages=[message1, message2, message3, message4]
)

bedrock_claude_serializer(thread.messages)

agent = ClaudeAgent(serializer=bedrock_claude_serializer)
thread.process_thread(agent)
# thread.add_message(message5)
# w = agent.agent_run(thread.messages)
