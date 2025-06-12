import uvicorn
from typing_extensions import override
from typing import Any, Literal, List
from a2a.types import AgentCard,AgentCapabilities
from a2a.server.agent_execution import AgentExecutor,RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message, new_task, new_text_artifact
from a2a.types import AgentSkill
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from collections.abc import AsyncIterable
from a2a.types import (
    TaskArtifactUpdateEvent,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
)

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
    url="http://localhost:9000",
    version="0.0.1",
    defaultInputModes=["text"],
    defaultOutputModes=["text"],
    capabilities=AgentCapabilities(streaming=True, tools=True),
    skills=[skill],
)


class HelloWorldAgent:
    "say hello world Agent"
    def invoke(self):
        return "hello world"

    async def stream(self, query: str, sessionId: str) -> AsyncIterable[Any]:
        """Process a query with streaming responses.

        Args:
            query: The user's query text
            sessionId: A unique session identifier

        Yields:
            Formatted response chunks with status updates
        """
        # Save context per session
        words = ["Hello", "World", "!", "How", "are", "you" , "!"]
        for word in words:
            yield {"is_task_complete": False, "content": word}
        yield {"is_task_complete": True, "content": ""}

class HelloWorldAgentExecutor(AgentExecutor):
    "Test agent executor"
    def __init__(self) -> None:
        self.agent = HelloWorldAgent()

    @override
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        "execute the agent"
        result = self.agent.invoke()
        event_queue.enqueue_event(new_agent_text_message(result))

    # 其它示例，请求其它应用时
    # @override
    # async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
    #     "execute the agent"
    #     query = context.get_user_input()
    #     task = context.current_task
    #     print(f"query: {query}, task: {task}")
    #     async for item in self.agent.stream(query, task.contextId):
    #         is_task_complete = item['is_task_complete']
    #         content = item['content']
    #         if not is_task_complete:
    #             event_queue.enqueue_event(
    #                 TaskStatusUpdateEvent(
    #                     status=TaskStatus(
    #                         state=TaskState.working,
    #                         message=new_agent_text_message(
    #                             content,
    #                             task.contextId,
    #                             task.id,
    #                         ),
    #                     ),
    #                     final=False,
    #                     contextId=task.contextId,
    #                     taskId=task.id,
    #                 )
    #             )
    #         else:
    #             event_queue.enqueue_event(
    #                 TaskArtifactUpdateEvent(
    #                     append=False,
    #                     contextId=task.contextId,
    #                     taskId=task.id,
    #                     lastChunk=True,
    #                     artifact=new_text_artifact(
    #                         name='current_result',
    #                         description='Result of request to agent.',
    #                         text=content,
    #                     ),
    #                 )
    #             )
    #             event_queue.enqueue_event(
    #                 TaskStatusUpdateEvent(
    #                     status=TaskStatus(state=TaskState.completed),
    #                     final=True,
    #                     contextId=task.contextId,
    #                     taskId=task.id,
    #                 )
    #             )
    @override
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise NotImplementedError("HelloWorldAgentExecutor does not support cancel")

#定义处理器请求
request_handler = DefaultRequestHandler(
    agent_executor=HelloWorldAgentExecutor(),
    task_store=InMemoryTaskStore(),  #用于任务状态的管理

)

#构建服务器
server = A2AStarletteApplication(
    agent_card=agent_card,http_handler=request_handler
)

if __name__ == '__main__':
    uvicorn.run(server.build(),host='0.0.0.0', port=9000)