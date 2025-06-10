import logging
import os
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm

def create_model(model:str, provider: str):
    """
    创建模型，返回字符串或者LiteLlm
    LiteLlm(model="deepseek/deepseek-chat", api_key="xxx", api_base="")
    :return:
    """
    if provider == "google":
        # google的模型直接使用名称
        assert os.environ.get("GOOGLE_API_KEY"), "GOOGLE_API_KEY is not set"
        return model
    elif provider == "openai":
        # openai的模型需要使用LiteLlm
        assert os.environ.get("OPENAI_API_KEY"), "OPENAI_API_KEY is not set"
        if not model.startswith("openai/"):
            # 表示兼容openai的模型请求
            model = "openai/" + model
        return LiteLlm(model=model, api_key=os.environ.get("OPENAI_API_KEY"), api_base="https://api.openai.com/v1")
    elif provider == "deepseek":
        # deepseek的模型需要使用LiteLlm
        assert os.environ.get("DEEPSEEK_API_KEY"),  "DEEPSEEK_API_KEY is not set"
        if not model.startswith("openai/"):
            # 表示兼容openai的模型请求
            model = "openai/" + model
        return LiteLlm(model=model, api_key=os.environ.get("DEEPSEEK_API_KEY"), api_base="https://api.deepseek.com/v1")
    elif provider == "ali":
        # huggingface的模型需要使用LiteLlm
        assert os.environ.get("ALI_API_KEY"), "ALI_API_KEY is not set"
        if not model.startswith("openai/"):
            # 表示兼容openai的模型请求
            model = "openai/" + model
        return LiteLlm(model=model, api_key=os.environ.get("ALI_API_KEY"), api_base="https://dashscope.aliyuncs.com/compatible-mode/v1")
    else:
        raise ValueError(f"Unsupported provider: {provider}")

def create_agent(model, provider, mcptools=[]) -> LlmAgent:
    """Constructs the ADK agent."""
    logging.info(f"使用的模型供应商是: {provider}，模型是: {model}")
    model = create_model(model, provider)
    return LlmAgent(
        model=model,
        name="weather_agent",
        description="An agent that can help questions about weather",
        instruction=f"""You are a specialized weather forecast assistant. Your primary function is to utilize the provided tools to retrieve and relay weather information in response to user queries. You must rely exclusively on these tools for data and refrain from inventing information. Ensure that all responses include the detailed output from the tools used and are formatted in Markdown""",
        tools=mcptools,
    )
