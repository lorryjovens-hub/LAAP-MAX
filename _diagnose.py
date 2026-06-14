
import sys, os, json, traceback

sys.path.insert(0, r"D:\LAAP")

# 1. Test basic config loading
print("=== 1. Config Loading ===")
from laap.__main__ import load_config
c = load_config()
print(f"Default provider: {c.get('default_provider', 'N/A')}")
print(f"Model: {c.get('model', 'N/A')}")
print(f"API keys: {list(c.get('api_keys', {}).keys())}")
api_base = {"deepseek":"https://api.deepseek.com/v1","openai":"https://api.openai.com/v1"}.get(c.get("default_provider","deepseek"),"")
print(f"API base URL: {api_base}")
key = c.get("api_keys", {}).get(c.get("default_provider","deepseek"), "")
print(f"Key: {'SET (' + str(len(key)) + ' chars)' if key else 'NOT SET'}")

# 2. Test tool loading
print("\n=== 2. Tool Loading ===")
from laap.agent_core.tools import get_all_tool_defs
all_defs = get_all_tool_defs()
print(f"Tools loaded: {len(all_defs)}")
tool_names = [d["name"] for d in all_defs]
print(f"Tool names: {tool_names[:10]}...")

# 3. Build tool definitions like run_app() does
print("\n=== 3. Tool Definition Building ===")
TOOLS_DEF = []
TOOL_HANDLERS = {}
for td in all_defs:
    name = td["name"]
    params = {"type": "object"}
    if td.get("params"):
        params["properties"] = td["params"]
        if td.get("req"):
            params["required"] = td["req"]
    TOOLS_DEF.append({
        "type": "function",
        "function": {"name": name, "description": td.get("desc", ""), "parameters": params}
    })
    if td.get("fn"):
        TOOL_HANDLERS[name] = td["fn"]
print(f"TOOLS_DEF: {len(TOOLS_DEF)}")
print(f"TOOL_HANDLERS: {len(TOOL_HANDLERS)}")
# Sample a tool def
if TOOLS_DEF:
    print(f"Sample tool: {json.dumps(TOOLS_DEF[0], indent=2, ensure_ascii=False)[:200]}")

# 4. Test creating request body
print("\n=== 4. API Request Test ===")
body = json.dumps({
    "model": c.get("model", "deepseek-v4-flash"),
    "stream": True,
    "messages": [{"role":"system","content":"You are a helpful assistant."}, {"role":"user","content":"Say hello"}],
    "tools": TOOLS_DEF,
    "tool_choice": "auto",
    "max_tokens": 4096,
})
print(f"Request size: {len(body)} bytes")
print(f"Body sample: {body[:200]}...")

# 5. Try API call
print("\n=== 5. Testing API Call ===")
import urllib.request
req = urllib.request.Request(
    f"{api_base}/chat/completions",
    data=body.encode(),
    headers={"Content-Type":"application/json","Authorization":f"Bearer {key}"},
    method="POST"
)
try:
    with urllib.request.urlopen(req, timeout=30) as rsp:
        buf = ""
        token_count = 0
        while True:
            chunk = rsp.read(4096)
            if not chunk: break
            buf += chunk.decode("utf-8", errors="replace")
            while "\n\n" in buf:
                block, buf = buf.split("\n\n", 1)
                for ln in block.strip().split("\n"):
                    if ln.startswith("data: "):
                        d = ln[6:]
                        if d == "[DONE]":
                            print("\n[DONE] received")
                            break
                        try:
                            dd = json.loads(d)
                            delta = dd.get("choices",[{}])[0].get("delta",{})
                            if delta.get("content"):
                                print(delta["content"], end="", flush=True)
                                token_count += 1
                            for tc in delta.get("tool_calls", []):
                                idx_tc = tc.get("index", 0)
                                print(f"\n[TOOL CALL #{idx_tc}: {tc.get('function',{}).get('name','?')}]", end="", flush=True)
                        except json.JSONDecodeError:
                            pass
        print(f"\nTotal tokens: {token_count}")
except urllib.error.HTTPError as e:
    print(f"\nHTTP Error: {e.code}")
    print(f"Response: {e.read().decode()[:500]}")
except Exception as e:
    print(f"\nError: {e}")
    traceback.print_exc()

print("\n=== Diagnostic Complete ===")
