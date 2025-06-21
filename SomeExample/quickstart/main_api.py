import logging
import os

import click
import uvicorn

from adk_agent_executor import ADKAgentExecutor
from dotenv import load_dotenv
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from starlette.routing import Route
from google.adk.agents.run_config import RunConfig,StreamingMode
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from starlette.applications import Starlette
from agent import root_agent

load_dotenv()

logging.basicConfig()


@click.command()
@click.option("--host", "host", default="localhost", help="服务器绑定的主机名（默认为 localhost,可以指定具体本机ip）")
@click.option("--port", "port", default=10002,help="服务器监听的端口号（默认为 10001）")
@click.option("--model", "model_name", default="claude-sonnet-4-20250514",help="使用的模型名称（如 deepseek-chat, claude-3-5-sonnet-20241022, claude-sonnet-4-20250514）")
@click.option("--provider", "provider", default="claude", type=click.Choice(["google","openai", "deepseek", "ali","claude"]),help="模型提供方名称（如 deepseek、openai 等）")
@click.option("--agent_url", "agent_url", default="",help="Agent Card中对外展示和访问的地址")
def main(host, port, model_name, provider, agent_url=""):
    agent_card_name = "Weather Agent"
    agent_name = "weather_agent"
    agent_description = "weather Agent"
    skill = AgentSkill(
        id=agent_name,
        name="weather Agent",
        description="city weather",
        tags=["weather"],
        examples=["weather"],
    )

    agent_card = AgentCard(
        name=agent_card_name,
        description=agent_description,
        url=f"http://{host}:{port}/",
        version="1.0.0",
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        capabilities=AgentCapabilities(streaming=True),
        skills=[skill],
    )
    runner = Runner(
        app_name=agent_card.name,
        agent=root_agent,
        artifact_service=InMemoryArtifactService(),
        session_service=InMemorySessionService(),
        memory_service=InMemoryMemoryService(),
    )
    # 支持流式的SSE模式的输出
    run_config = RunConfig(
        streaming_mode=StreamingMode.SSE,
        max_llm_calls=200
    )
    agent_executor = ADKAgentExecutor(runner, agent_card, run_config)

    request_handler = DefaultRequestHandler(
        agent_executor=agent_executor, task_store=InMemoryTaskStore()
    )

    a2a_app = A2AStarletteApplication(
        agent_card=agent_card, http_handler=request_handler
    )

    uvicorn.run(a2a_app.build(), host=host, port=port)

if __name__ == "__main__":
    main()
