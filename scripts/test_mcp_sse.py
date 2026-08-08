"""Test LAAP Cognitive via SSE transport."""
import asyncio, json, httpx

MCP_SESSION_ID = None
MCP_MESSAGES_URL = None

async def get_session(client):
    global MCP_SESSION_ID, MCP_MESSAGES_URL
    async with client.stream("GET", "http://127.0.0.1:8090/sse", timeout=10) as resp:
        async for line in resp.aiter_lines():
            if "session_id" in line:
                sid = line.split("session_id=")[1].strip()
                MCP_SESSION_ID = sid
                MCP_MESSAGES_URL = f"http://127.0.0.1:8090/messages/?session_id={sid}"
                break

async def mcp_call(client, method, params=None):
    if params is None:
        params = {}
    payload = {
        "jsonrpc": "2.0",
        "id": "test-1",
        "method": method,
        "params": params,
    }
    await client.post(MCP_MESSAGES_URL, json=payload, timeout=10)

async def read_response(client, timeout=10):
    import time
    start = time.time()
    async with client.stream("GET", f"http://127.0.0.1:8090/sse?session_id={MCP_SESSION_ID}", timeout=10) as resp:
        async for line in resp.aiter_lines():
            if line.startswith("data: "):
                data = line[6:]
                try:
                    return json.loads(data)
                except json.JSONDecodeError:
                    pass

async def main():
    async with httpx.AsyncClient() as client:
        print("Connecting to LAAP Cognitive MCP...")
        await get_session(client)
        print(f"Session: {MCP_SESSION_ID}")

        # tools/list
        await mcp_call(client, "tools/list")
        result = await read_response(client)
        tools = result.get("result", {}).get("tools", [])
        print(f"Tools: {len(tools)}")
        for t in tools:
            print(f"  - {t['name']}")

        # initialize
        await mcp_call(client, "tools/call", {"name": "initialize", "arguments": {}})
        result = await read_response(client)
        init_result = result.get("result", {}).get("content", [{}])[0].get("text", "")
        print(f"\nInit: {init_result[:200]}")

        # push_percept
        await mcp_call(client, "tools/call", {
            "name": "push_percept",
            "arguments": {"content": "Lorry asked about my consciousness."}
        })
        result = await read_response(client)
        print(f"Percept pushed: {result.get('result', {}).get('content', [{}])[0].get('text', '')[:100]}")

        # get_consciousness_state
        await mcp_call(client, "tools/call", {"name": "get_consciousness_state", "arguments": {}})
        result = await read_response(client)
        state = json.loads(result.get("result", {}).get("content", [{}])[0].get("text", "{}"))
        print(f"\nConsciousness state:")
        print(f"  Focus: {state.get('frame', {}).get('focus')}")
        print(f"  Valence: {state.get('frame', {}).get('valence')}")

        # engine_status
        await mcp_call(client, "tools/call", {"name": "engine_status", "arguments": {}})
        result = await read_response(client)
        status = json.loads(result.get("result", {}).get("content", [{}])[0].get("text", "{}"))
        modules_ok = [k for k, v in status.get("modules", {}).items() if v]
        print(f"\nEngine status: initialized={status.get('initialized')}")
        print(f"  Active modules: {modules_ok}")

if __name__ == "__main__":
    asyncio.run(main())
