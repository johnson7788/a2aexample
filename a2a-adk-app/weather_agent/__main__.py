import logging
import os

import click
import uvicorn

from adk_agent import create_agent
from adk_agent_executor import ADKAgentExecutor
from dotenv import load_dotenv
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from starlette.routing import Route

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from starlette.applications import Starlette
from load_mcp import load_mcp_tools


load_dotenv()

logging.basicConfig()


@click.command()
@click.option("--host", "host", default="localhost", help="服务器绑定的主机名（默认为 localhost,可以指定具体本机ip）")
@click.option("--port", "port", default=10002,help="服务器监听的端口号（默认为 10002）")
@click.option("--prompt", "agent_prompt_file", default="prompt.txt",help="Agent 的 prompt 文件路径（默认为 prompt.txt）")
@click.option("--model", "model_name", default="deepseek-chat",help="使用的模型名称（如 deepseek-chat）")
@click.option("--provider", "provider", default="deepseek", type=click.Choice(["google","openai", "deepseek", "ali"]),help="模型提供方名称（如 deepseek、openai 等）")
@click.option("--mcp_config", "mcp_config_path", default="mcp_config.json",help="MCP 配置文件路径（默认为 mcp_config.json）")
@click.option("--agent_url", "agent_url", default="",help="Agent Card中对外展示和访问的地址")
def main(host, port, agent_prompt_file, model_name, provider, mcp_config_path, agent_url=""):
    agent_card_name = "Weather Agent"
    agent_name = "weather_agent"
    agent_description = "An agent that can help questions about weather"
    with  open(agent_prompt_file, "r") as f:
        agent_instruction = f.read()
    skill = AgentSkill(
        id="weather_search",
        name="Search weather",
        description="Helps with weather in city, or states",
        tags=["weather"],
        examples=["weather in LA, CA"],
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
    mcptools = load_mcp_tools(mcp_config_path=mcp_config_path)
    adk_agent = create_agent(model_name, provider, agent_name,agent_description,agent_instruction, mcptools=mcptools)
    runner = Runner(
        app_name=agent_card.name,
        agent=adk_agent,
        artifact_service=InMemoryArtifactService(),
        session_service=InMemorySessionService(),
        memory_service=InMemoryMemoryService(),
    )
    agent_executor = ADKAgentExecutor(runner, agent_card)

    request_handler = DefaultRequestHandler(
        agent_executor=agent_executor, task_store=InMemoryTaskStore()
    )

    a2a_app = A2AStarletteApplication(
        agent_card=agent_card, http_handler=request_handler
    )

    uvicorn.run(a2a_app.build(), host=host, port=port)


if __name__ == "__main__":
    main()
