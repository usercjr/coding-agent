"""MCP 探路脚本（一次性验证，不是项目正式代码）。

作用：连一个真实的 MCP server，问它有哪些工具，再调用一个，
证明“连接 → list_tools → call_tool”整条 MCP 通路能通。

运行： python mcp_probe.py     （首次会用 npx 下载官方测试 server，稍等片刻）
"""

import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    # 第1步：告诉它怎么启动那个 server（用 npx 跑官方 everything 测试 server）
    params = StdioServerParameters(
        command="npx",
        args=["-y", "@modelcontextprotocol/server-everything"],
    )

    # 第2步：启动 server 子进程并连上它
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()               # 握手

            # 第3步：问 server —— 你有哪些工具？
            resp = await session.list_tools()
            print("=== server 暴露的工具 ===")
            for t in resp.tools:
                print(f"- {t.name}: {t.description}")

            # 第4步：调用其中一个工具试试（echo：把输入原样回显）
            print("\n=== 调用 echo(message='hi mcp') ===")
            result = await session.call_tool("echo", {"message": "hi mcp"})
            print(result.content)


if __name__ == "__main__":
    asyncio.run(main())
