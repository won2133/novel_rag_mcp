import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import time

server_params = StdioServerParameters(
    command="[가상환경 위치]/bin/python3",  # 서버 실행 명령
    args=["[폴더 위치]/mcp_server/server.py"],
)

async def call_tool(session, tool_name, args):
    result = await session.call_tool(tool_name, args)
    return result

async def main():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            start = time.perf_counter()
            
            result1, result2, result3, result4, result5, result6, result7, result8, result9, result10 = await asyncio.gather(
                call_tool(session, "novel_rag", {"question": "k선생이 생각한 자신의 단점은?"}),
                call_tool(session, "novel_rag", {"question": "k선생이 생각한 자신의 단점은?"}),
                call_tool(session, "novel_rag", {"question": "k선생이 생각한 자신의 단점은?"}),
                call_tool(session, "novel_rag", {"question": "k선생이 생각한 자신의 단점은?"}),
                call_tool(session, "novel_rag", {"question": "k선생이 생각한 자신의 단점은?"}),
                call_tool(session, "novel_rag", {"question": "k선생이 생각한 자신의 단점은?"}),
                call_tool(session, "novel_rag", {"question": "k선생이 생각한 자신의 단점은?"}),
                call_tool(session, "novel_rag", {"question": "k선생이 생각한 자신의 단점은?"}),
                call_tool(session, "novel_rag", {"question": "k선생이 생각한 자신의 단점은?"}),
                call_tool(session, "novel_rag", {"question": "k선생이 생각한 자신의 단점은?"})
            )
            print("\n\n\n\n\n\nrerank 비동기")
            print("총 소요 시간: ", time.perf_counter()-start)

asyncio.run(main())

