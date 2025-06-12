from pydoc import describe
from typing import override
from a2a.types import AgentCard,AgentCapabilities

from a2a.types import AgentSkill
skill = AgentSkill(
    id="hello-world",
    name="Hello World Skill",
    description="Just a hello world skill",
    tags = ["hello world"],
    examples=["hi","hello world"]
)

agent_card = AgentCard(
    name="Hello World Agent",
    description="Just a hello world agent",
    url="http:/0.0.0.0:9000",
    version="0.0.1",
    defaultInputModes=["text"],
    defaultOutputModes=["text"],
    capabilities=AgentCapabilities(streams=True, tools=True),
    skills=[skill],
)


class HelloWorldAgent:
    "say hello world Agent"
    def invoke(self):
        return "hello world"


from a2a.server.agent_execution import AgentExecutor,RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message

class HelloWorldAgentExecutor(AgentExecutor):
    "Test agent executor"
    def __init__(self) -> None:
        self.agent = HelloWorldAgent()

    @override
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        "execute the agent"
        result = self.agent.invoke()
        await event_queue.enqueue_event(new_agent_text_message(result))   

    @override
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise NotImplementedError("HelloWorldAgentExecutor does not support cancel")


from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore



if __name__ == '__main__':
    #1.定义技能
    skill = skill

    #2.定义智能体名片
    agent_card = agent_card

    #定义处理器请求
    request_handler = DefaultRequestHandler(
        agent_executor=HelloWorldAgentExecutor(),
        task_store=InMemoryTaskStore(),  #用于任务状态的管理

    )

    #构建服务器
    server = A2AStarletteApplication(
        agent_card=agent_card,http_handler=request_handler
    )

    import uvicorn
    uvicorn.run(server.build(),host='0.0.0.0', port=9000)