"""MCP Client：连外部 MCP Server，把它的工具动态注册进我们同一张注册表。

async 管道部分（_list_tools_async / _call_tool_async / _content_to_text）是纯
协议管道，先不用吃透；你要理解和填写的是 load_mcp_tools() 里“把远端工具包装成
一条 Tool”那一步。

注意：这里为了简单，每次调用都新开一条连接、用完就断（reconnect-per-call）。
好处是好理解、无需线程；代价是每次调用都会重启一次 server，较慢。
以后可优化成“开一次连接、一直复用”。
"""

import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from agent.tools.base import Tool, register

# 描述“怎么启动这个 server”：这里用官方 everything 测试 server
SERVER_PARAMS = StdioServerParameters(
    command="npx",
    args=["-y", "@modelcontextprotocol/server-everything"],
)


# ---------- async 管道（我搭好，先不用细究）----------
# 管道可以让模型在注册表找到要用的工具后，发送调用改工具的请求给远端server，server执行工具操作后返回结果。

async def _list_tools_async():
    """连上 server，问它有哪些工具，返回工具列表。"""
    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            resp = await session.list_tools() # 等待server返回有哪些清单
            return resp.tools # 把工具清单返回


async def _call_tool_async(name, args):
    """连上 server，让它运行某个工具，返回原始结果对象。"""
    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            return await session.call_tool(name, args)


def _content_to_text(result):
    """把 call_tool 返回的 content（TextContent 列表）拍平成一段纯文本。"""
    parts = []
    for block in result.content:
        text = getattr(block, "text", None)
        if text is not None:
            parts.append(text)
    return "\n".join(parts) if parts else str(result.content)


def _make_execute(tool_name):
    """给一个远端工具名，造出它的“转发 execute”函数。

    为什么要用这个工厂函数而不是在循环里直接 def？—— 见下面 load_mcp_tools 的说明。
    """
    def execute(**args):
        # 同步地驱动异步调用：开一条线、转发、拿回结果
        result = asyncio.run(_call_tool_async(tool_name, args))
        return _content_to_text(result)
    return execute


# ---------- 注册 MCP 工具（这部分你来填）----------

def load_mcp_tools():
    """把 server 的工具全部动态注册进我们的注册表。"""
    tools = asyncio.run(_list_tools_async())   # 1. 拿到远端工具清单
    for t in tools:
        # t 有三样：t.name / t.description / t.inputSchema
        #
        # 2. 把 t 包装成一条 Tool 并 register 进注册表
        # 不同 mcp 版本字段名不同（input_schema / inputSchema），两种都兼容
        schema = getattr(t, "input_schema", None) or getattr(t, "inputSchema", None)
        register(Tool(
            name=t.name,
            description=t.description,
            parameters=schema,
            execute=_make_execute(t.name),
        ))
    print(f"已从 MCP server 注册 {len(tools)} 个工具")
