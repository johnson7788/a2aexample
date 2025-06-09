#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date  : 2025/6/9 21:08
# @File  : load_mcp.py.py
# @Author: johnson
# @Contact : github: johnson7788
# @Desc  : 加载mcp工具
import os
import json
import sys
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters, SseServerParams


def load_mcp_config_from_file(config_path="mcp_config.json") -> dict:
    """
    Load MCP configuration from a JSON file.

    Args:
        config_path: Path to the configuration file

    Returns:
        Dict containing the configuration

    Raises:
        SystemExit: If the file is not found or contains invalid JSON
    """
    try:
        with open(config_path, "r", encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: {config_path} not found.")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in {config_path}.")
        sys.exit(1)

def load_mcp_tools(mcp_config_path):
    """
    读取mcp工具
    :param mcp_config_path:
    :return:
    """
    assert os.path.exists(mcp_config_path),  f"{mcp_config_path}配置文件不存在，请检查"
    config = load_mcp_config_from_file(mcp_config_path)
    servers_cfg = config.get("mcpServers", {})
    mcp_tools = []
    for server_name, conf in servers_cfg.items():
        if "url" in conf:  # SSE server
            client = MCPToolset(
                connection_params=SseServerParams(
                    url=conf["url"],
                    headers=conf.get("headers"),
                    timeout=conf.get("timeout", 5),
                    sse_read_timeout=conf.get("sse_read_timeout", 300)
                )
            )
        elif "command" in conf:  # Local process-based server
            client = MCPToolset(
                connection_params=StdioServerParameters(
                    command=conf.get("command"),
                    args=conf.get("args", []),
                    env=conf.get("env", {})
                )
            )
        else:
            raise ValueError(f"无效的MCP配置, {server_name}")
        mcp_tools.append(client)
    return mcp_tools