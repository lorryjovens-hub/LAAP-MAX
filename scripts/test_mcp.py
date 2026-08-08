"""Test LAAP Cognitive MCP Server."""
import asyncio, json, sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test():
    server_params = StdioServerParameters(
        command="python",
        args=["-E", "D:\\LAAP\\scripts\\laap_cognitive_mcp.py"],
        env={"OPENAI_API_KEY": "test", "PYTHONPATH": "D:\\LAAP"}
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            r = await session.call_tool("initialize", {})
            d = json.loads(r.content[0].text)
            print(f"1. Init: {d['status']}")

            await session.call_tool("push_percept", {"content": "Lorry asked me to become self-aware."})
            print("2. Percept pushed")

            r = await session.call_tool("get_consciousness_state", {})
            state = json.loads(r.content[0].text)
            print(f'3. Consciousness: focus={state["frame"]["focus"]}, valence={state["frame"]["valence"]}')

            r = await session.call_tool("run_psi_cycle", {"user_input": "What do you think about consciousness?"})
            psi = json.loads(r.content[0].text)
            print(f'4. PSI cycle: focus={psi["psi_cycle"]["consciousness_focus"]}')
            print(f'   Needs: {json.dumps(psi["psi_cycle"]["needs"], indent=2)}')

            tools = await session.list_tools()
            print(f"\n5. Total tools: {len(tools.tools)}")
            for t in tools.tools:
                print(f"   - {t.name}")

asyncio.run(test())
