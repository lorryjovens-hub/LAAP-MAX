"""
LAAP Agent v3 — Token 优化基准测试（干净版）
=============================================

直接测试：缓存友好 prompt + 精简 schema 到底省多少 token。
"""

import sys, json, time, os, httpx

sys.path.insert(0, "D:/LAAP/laap_agent")

# ── 读 API key ──
key = open("D:/LAAP/.deepseek_key").read().strip()
client = httpx.Client(timeout=120.0)

# ── 1. 缓存友好的 System Prompt ──
STATIC = "You are LAAP Agent, an AI coding assistant. Be precise and concise."
TOOL_NAMES = ["terminal", "file_read", "file_write", "glob", "grep"]

system_prompt = f"{STATIC}\n\nTools: {', '.join(TOOL_NAMES)}\n\nUse tools when needed."

# ── 2. 精简工具 Schema（5个，355 tokens） ──
SCHEMAS = [
    {"type":"function","function":{"name":"terminal","description":"Run shell cmd",
     "parameters":{"type":"object","properties":{"command":{"type":"string"},"timeout":{"type":"integer"}},"required":["command"]}}},
    {"type":"function","function":{"name":"file_read","description":"Read file",
     "parameters":{"type":"object","properties":{"path":{"type":"string"},"limit":{"type":"integer"}},"required":["path"]}}},
    {"type":"function","function":{"name":"file_write","description":"Write file",
     "parameters":{"type":"object","properties":{"path":{"type":"string"},"content":{"type":"string"}},"required":["path","content"]}}},
    {"type":"function","function":{"name":"glob","description":"Find files",
     "parameters":{"type":"object","properties":{"pattern":{"type":"string"}},"required":["pattern"]}}},
    {"type":"function","function":{"name":"grep","description":"Search files",
     "parameters":{"type":"object","properties":{"pattern":{"type":"string"},"path":{"type":"string"}},"required":["pattern"]}}},
]

schema_json = json.dumps(SCHEMAS)
schema_tokens = len(schema_json) // 4
print(f"System prompt: {len(system_prompt)} chars ≈ {len(system_prompt)//4} tokens")
print(f"Tool schemas: {schema_tokens} tokens ({len(SCHEMAS)} tools)")

# ── 3. DeepSeek 调用 ──
def call_llm(messages, tools=None):
    payload = {"model": "deepseek-v4-flash", "messages": messages,
               "temperature": 0.3, "max_tokens": 4096}
    if tools:
        payload["tools"] = tools
    r = client.post("https://api.deepseek.com/v1/chat/completions",
                    json=payload, headers={"Authorization": f"Bearer {key}",
                                           "Content-Type": "application/json"})
    data = r.json()
    choice = data["choices"][0]
    usage = data.get("usage", {})
    msg = choice["message"]
    return {
        "content": msg.get("content", ""),
        "tool_calls": msg.get("tool_calls", []),
        "prompt": usage.get("prompt_tokens", 0),
        "completion": usage.get("completion_tokens", 0),
        "total": usage.get("total_tokens", 0),
        "cache_hit": usage.get("prompt_cache_hit_tokens", 0),
    }

# ── 4. 测试 ──
print(f"\n{'='*60}")
print("  LAAP Agent v3 — Token 实测")
print(f"{'='*60}")

# 测试: 三轮对话
messages = [{"role": "system", "content": system_prompt}]
total_tokens = 0

for i, msg in enumerate(["用 Python 写 Hello World", "改成 Rust 版本", "再改成 Go 版本"]):
    messages.append({"role": "user", "content": msg})
    result = call_llm(messages, tools=SCHEMAS)
    messages.append({"role": "assistant", "content": result["content"]})
    
    cache_pct = (result["cache_hit"] / max(1, result["prompt"])) * 100
    total_tokens += result["total"]
    
    print(f"\n─── 第{i+1}轮: {msg} ───")
    print(f"  Prompt: {result['prompt']:>5} | Completion: {result['completion']:>4} | "
          f"Total: {result['total']:>5} | Cache: {cache_pct:>5.0f}%")
    print(f"  累积: {total_tokens} tokens")
    if i == 0:
        print(f"  首轮基准: system={len(system_prompt)//4}t + schemas={schema_tokens}t")

print(f"\n{'='*60}")
print(f"  Hermes 基准: ~5700 token/轮  ×3轮 = ~17100")
print(f"  OpenClaw 基准: ~1400 token/轮 ×3轮 = ~4200")
print(f"  LAAP v3: {total_tokens} tokens (3轮)")
print(f"  对比 Hermes: {(1-total_tokens/17100)*100:.0f}% 节省")
print(f"  对比 OpenClaw: {(1-total_tokens/4200)*100:.0f}% 节省")
print(f"{'='*60}")
