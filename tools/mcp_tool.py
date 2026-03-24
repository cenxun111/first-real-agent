import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


class MCPClient:
    """MCP 客户端管理器，用于连接服务器并执行工具。"""

    def __init__(self, server_script: str):
        self.server_script = server_script
        self.server_params = StdioServerParameters(
            command=sys.executable, args=[server_script], env=None
        )

    async def _call_tool_async(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """异步调用 MCP 工具。"""
        # 将 stderr 重定向到 devnull 以减少日志噪音
        import os

        with open(os.devnull, "w") as devnull:
            async with stdio_client(self.server_params, errlog=devnull) as (
                read,
                write,
            ):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.call_tool(tool_name, arguments)

                    # 处理结果，提取文本内容
                    if hasattr(result, "content"):
                        texts = [c.text for c in result.content if hasattr(c, "text")]
                        return "\n".join(texts)
                    return str(result)

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """同步包装器，用于在同步 Agent 中调用异步 MCP 工具。"""
        try:
            return asyncio.run(self._call_tool_async(tool_name, arguments))
        except Exception as e:
            return f"MCP Error: {str(e)}"

    async def _get_tools_async(self) -> List[Dict[str, Any]]:
        """异步获取服务器提供的所有工具定义。"""
        import os

        with open(os.devnull, "w") as devnull:
            async with stdio_client(self.server_params, errlog=devnull) as (
                read,
                write,
            ):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    tools_list = await session.list_tools()

                    formatted_tools = []
                    for tool in tools_list.tools:
                        # 为 MCP 工具添加前缀，防止与本地工具冲突
                        tool_name = f"mcp_{tool.name}"
                        formatted_tools.append(
                            {
                                "type": "function",
                                "function": {
                                    "name": tool_name,
                                    "description": f"[MCP] {tool.description}",
                                    "parameters": tool.inputSchema,
                                },
                            }
                        )
                return formatted_tools

    def get_tools(self) -> List[Dict[str, Any]]:
        """同步获取工具定义。"""
        try:
            return asyncio.run(self._get_tools_async())
        except Exception as e:
            print(f"MCP Discovery Error: {str(e)}")
            return []


def load_mcp_server(server_path: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    加载指定的 MCP 服务器并返回工具定义和处理器。
    """
    client = MCPClient(server_path)
    mcp_tools = client.get_tools()

    handlers = {}
    for tool in mcp_tools:
        # tool["function"]["name"] 已经包含了 mcp_ 前缀
        full_name = tool["function"]["name"]
        # 原始工具名称（去掉了 mcp_ 前缀）
        original_name = full_name[4:]
        # 使用闭包捕获正确的工具名称和客户端实例
        handlers[full_name] = (
            lambda n=original_name: lambda **kw: client.call_tool(n, kw)
        )()

    return mcp_tools, handlers
