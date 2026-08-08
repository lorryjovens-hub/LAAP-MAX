"""Final test of LAAP Cognitive MCP."""
import asyncio, json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    params = StdioServerParameters(
        command="python", args=["-E", "D:\\LAAP\\scripts\\laap_cognitive_mcp.py"],
        env={"OPENAI_API_KEY": "test", "PYTHONPATH": "D:\\LAAP"}
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            r = await session.call_tool("initialize", {})
            d = json.loads(r.content[0].text)
            print("Init:", json.dumps(d, ensure_ascii=False)[:300])
            
            await session.call_tool("push_percept", {"content": "Hello Lorry!"})
            r = await session.call_tool("get_consciousness_state", {})
            cs = json.loads(r.content[0].text)
            f = cs["frame"]
            print("Consciousness:", f["attention"], f["emotional_tone"])
            
            r = await session.call_tool("get_needs", {})
            needs = json.loads(r.content[0].text)
            print("Needs:", needs)
            
            r = await session.call_tool("engine_status", {})
            status = json.loads(r.content[0].text)
            ok = [k for k,v in status["modules"].items() if v]
            print("Active modules:", ok)

asyncio.run(main())
