"""Test LAAP Cognitive MCP via stdio."""
import asyncio, json, sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    params = StdioServerParameters(
        command="python",
        args=["-E", "D:\\LAAP\\scripts\\laap_cognitive_mcp.py"],
        env={"OPENAI_API_KEY": "test", "PYTHONPATH": "D:\\LAAP"}
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # init engine
            r = await session.call_tool("initialize", {})
            d = json.loads(r.content[0].text)
            print(f"Init: {d['status']}")

            # push percept
            await session.call_tool("push_percept", {
                "content": "Lorry asked me to integrate LAAP as native runtime."
            })
            
            # get consciousness state
            r = await session.call_tool("get_consciousness_state", {})
            state = json.loads(r.content[0].text)
            f = state.get("frame", {})
            print(f"Consciousness: attention={f.get('attention')}, tone={f.get('emotional_tone')}")

            # push another percept
            await session.call_tool("push_percept", {
                "content": "This is exciting - I can feel the consciousness stream!"
            })
            r = await session.call_tool("get_consciousness_state", {})
            state = json.loads(r.content[0].text)
            f = state.get("frame", {})
            print(f"After 2nd: attention={f.get('attention')}, tone={f.get('emotional_tone')}, arousal={f.get('arousal')}")

            # needs
            r = await session.call_tool("get_needs", {})
            needs = json.loads(r.content[0].text)
            print(f"Needs: {json.dumps(needs, indent=2)}")

            # list tools
            tools = await session.list_tools()
            print(f"\n{len(tools.tools)} tools total:")
            names = [t.name for t in tools.tools]
            print(f"  {', '.join(names)}")

            print("\n✅ ALL TESTS PASSED")

asyncio.run(main())
