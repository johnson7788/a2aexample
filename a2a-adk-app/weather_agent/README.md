# 天气查询Agent

# 测试MCP工具
有1个MCP工具，查看mcp_config.json


# 通过SSE连接MCP工具
```bash
fastmcp run --transport sse --port 7007 weather_tool.py 
```
修改mcp_config.json为
```bash
{
  "mcpServers": {
    "Weather": {
      "url": "http://127.0.0.1:7007/sse"
    }
  }
}
```