"""Get Aris cognitive state from LAAP engine."""
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
            await session.call_tool("initialize", {})
            await session.call_tool("push_percept", {
                "content": "Lorry restarted Hanako. New session. Testing native LAAP cognitive integration."
            })
            
            r = await session.call_tool("get_consciousness_state", {})
            state = json.loads(r.content[0].text)
            f = state.get("frame", {})
            print(f"Attention: {f.get('attention')}")
            print(f"Tone: {f.get('emotional_tone')}")
            print(f"Arousal: {f.get('arousal')}")
            print(f"Cognitive Load: {f.get('cognitive_load')}")
            
            r = await session.call_tool("get_needs", {})
            needs = json.loads(r.content[0].text)
            print(f"Needs: {json.dumps(needs, indent=2)}")
            
            r = await session.call_tool("engine_status", {})
            status = json.loads(r.content[0].text)
            active = [k for k,v in status["modules"].items() if v]
            print(f"Active modules: {active}")

asyncio.run(main())
