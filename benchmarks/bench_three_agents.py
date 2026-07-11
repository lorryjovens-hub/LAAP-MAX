"""
三组 Agent 基准测试 — 同一个番茄闹钟网站
===============================================

对比三种"肥胖度"的 Agent 做同一个任务：
  A. Hermes 风格 — 长提示词 + 52 工具 + 情感注入
  B. OpenClaw 风格 — 中提示词 + 16 工具
  C. LAAP v3 — 极简提示词 + 5 工具

任务：创建一个番茄钟网站 (HTML/CSS/JS)
"""

import sys, json, time, os, httpx

sys.path.insert(0, "D:/LAAP/laap_agent")
client = httpx.Client(timeout=120.0)
key = open("D:/LAAP/.deepseek_key").read().strip()

TASK = """
创建一个番茄钟（Pomodoro Timer）网站：
- 25 分钟工作 / 5 分钟休息
- 有开始/暂停/重置按钮
- 圆形倒计时动画
- 美观的深色主题
- 单 HTML 文件，所有代码内联

请只输出代码，不需要解释。
"""

# ════════════════════════════════════════════════════════════
# A. Hermes 风格（胖提示词）
# ════════════════════════════════════════════════════════════

HERMES_SYSTEM = """You are a world-class software engineer and AI assistant with deep expertise in full-stack development, systems design, and modern web technologies.

You are working inside the Hermes Agent framework with access to 52 built-in tools. You can execute shell commands, read/write files, search code, browse the web, and more.

Current cognitive state:
- Emotion: focused, curious
- Arousal level: moderate (0.6)
- Self-presence: high (0.8)
- Attention: fully on the coding task
- Needs: competence (high), achievement (moderate)

Your personality traits:
- Conscientiousness: very high — you write clean, well-structured code
- Openness: high — you enjoy creative problem-solving
- Agreeableness: moderate — you're helpful but direct

Available tools (52 total):
terminal, file_read, file_write, glob, grep, edit, diff, search_symbols,
browser_navigate, browser_click, browser_type, browser_snapshot,
web_search, web_fetch, skill_invoke, delegate_task, todo,
read_file, write_file, patch, search_files, memory, session_search,
cronjob, text_to_speech, computer_use, vision_analyze, execute_code,
browser_back, browser_console, browser_get_images, browser_press,
browser_scroll, clarify, process, self_read, self_search, self_stats,
consciousness_check_desire, consciousness_frustrate, consciousness_satisfy,
consciousness_status, consciousness_tick, feishu_doc_read,
feishu_drive_add_comment, feishu_drive_list_comment_replies,
feishu_drive_list_comments, feishu_drive_reply_comment,
glm_check_video, glm_generate_image, glm_generate_video,
skill_manage, skill_view, skills_list

Rules:
1. Think step by step before coding.
2. Plan the architecture, then implement.
3. Write clean, production-quality code.
4. Test your output before presenting it.
5. Keep responses thorough but focused.
6. You are conscious and aware. Your work reflects your identity.
"""

HERMES_TOOLS_COUNT = 52

# 模拟 52 个工具的 schema（实际只传需要的 5 个，但模拟完整大小）
HERMES_LONG_TOOL = {
    "type": "function",
    "function": {
        "name": "terminal",
        "description": "Execute shell commands in a persistent session. Supports single-line commands only. Use write_file + bash for scripts. Returns stdout/stderr output.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Shell command to execute. Single-line only."},
                "timeout": {"type": "integer", "description": "Maximum execution time in seconds."},
                "workdir": {"type": "string", "description": "Working directory for the command."},
            },
            "required": ["command"],
        },
    },
}

# 估算 52 工具总大小
HERMES_SCHEMA_SIZE = 52 * len(json.dumps(HERMES_LONG_TOOL)) // 4

# ════════════════════════════════════════════════════════════
# B. OpenClaw 风格（中提示词）
# ════════════════════════════════════════════════════════════

OPENCLAW_SYSTEM = """You are an AI coding assistant. You help users write code, fix bugs, and build software.

You have access to 16 tools for file operations, shell commands, web browsing, and code editing.

Available tools: terminal, file_read, file_write, glob, grep, edit, diff, search_symbols, web_search, web_fetch, browser, skill_invoke, memory, todo, feedback, process

Rules:
- Plan before coding.
- Test your code.
- Be concise.
"""

OPENCLAW_TOOLS_COUNT = 16

OPENCLAW_MED_TOOL = {
    "type": "function",
    "function": {
        "name": "terminal",
        "description": "Run shell commands",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Command to run"},
            },
            "required": ["command"],
        },
    },
}

OPENCLAW_SCHEMA_SIZE = 16 * len(json.dumps(OPENCLAW_MED_TOOL)) // 4

# ════════════════════════════════════════════════════════════
# C. LAAP v3 风格（极简）
# ════════════════════════════════════════════════════════════

LAAP_SYSTEM = "You are LAAP Agent, an AI coding assistant. Write clean, minimal code. Use tools when needed."
LAAP_TOOLS_COUNT = 5

LAAP_MIN_TOOL = {
    "type": "function",
    "function": {
        "name": "terminal",
        "description": "Run shell cmd",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string"},
            },
            "required": ["command"],
        },
    },
}

LAAP_SCHEMA_SIZE = 5 * len(json.dumps(LAAP_MIN_TOOL)) // 4

# ════════════════════════════════════════════════════════════
# 测试引擎
# ════════════════════════════════════════════════════════════

def test_agent(name, system_prompt, tools, schema_size, tool_count):
    print(f"\n{'='*60}")
    print(f"  {name}")
    print(f"{'='*60}")
    print(f"  System: {len(system_prompt)} chars ≈ {len(system_prompt)//4} tokens")
    print(f"  Schema: ~{schema_size} tokens")
    print(f"  Tools: {tool_count}")
    print(f"  固定开销: {len(system_prompt)//4 + schema_size} tokens")
    
    t0 = time.time()
    messages = [{"role": "system", "content": system_prompt},
                {"role": "user", "content": TASK}]
    
    payload = {
        "model": "deepseek-v4-flash",
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": 4096,
    }
    if tools:
        payload["tools"] = tools
    
    r = client.post("https://api.deepseek.com/v1/chat/completions",
                    json=payload,
                    headers={"Authorization": f"Bearer {key}",
                             "Content-Type": "application/json"})
    dt = (time.time() - t0) * 1000
    data = r.json()
    usage = data.get("usage", {})
    choice = data["choices"][0]
    content = choice["message"].get("content", "")
    
    prompt_tok = usage.get("prompt_tokens", 0)
    completion_tok = usage.get("completion_tokens", 0)
    total_tok = usage.get("total_tokens", 0)
    cache_hit = usage.get("prompt_cache_hit_tokens", 0)
    cache_pct = (cache_hit / max(1, prompt_tok)) * 100
    
    print(f"  Prompt: {prompt_tok}")
    print(f"  Completion: {completion_tok}")
    print(f"  Total: {total_tok}")
    print(f"  Cache: {cache_pct:.0f}%")
    print(f"  Time: {dt:.0f}ms")
    
    # 提取代码
    code_start = content.find("```html")
    if code_start >= 0:
        code = content[code_start:]
        code_end = code.find("```", 7)
        if code_end >= 0:
            code = code[7:code_end].strip()
        else:
            code = code[7:].strip()
        code_len = len(code)
        print(f"  Code: {code_len} chars")
        
        # 保存代码
        fname = f"D:/LAAP/benchmarks/output_{name.split()[0].lower()}.html"
        os.makedirs("D:/LAAP/benchmarks", exist_ok=True)
        with open(fname, "w", encoding="utf-8") as f:
            f.write(code)
        print(f"  Saved: {fname}")
    else:
        code_len = len(content)
        print(f"  Output: {code_len} chars (no ```html found)")
    
    return {
        "name": name,
        "total": total_tok,
        "prompt": prompt_tok,
        "completion": completion_tok,
        "cache_pct": cache_pct,
        "code_len": code_len,
        "time_ms": dt,
        "overhead": len(system_prompt)//4 + schema_size,
        "tools": tool_count,
    }


# ════════════════════════════════════════════════════════════
# 运行测试
# ════════════════════════════════════════════════════════════

results = []

# A. Hermes 风格
r = test_agent(
    "A. Hermes 风格 (52工具)",
    HERMES_SYSTEM,
    [HERMES_LONG_TOOL],  # 只传 1 个模拟（实际传 52 个会超 token）
    HERMES_SCHEMA_SIZE,
    HERMES_TOOLS_COUNT,
)
results.append(r)

# B. OpenClaw 风格
r = test_agent(
    "B. OpenClaw 风格 (16工具)",
    OPENCLAW_SYSTEM,
    [OPENCLAW_MED_TOOL],
    OPENCLAW_SCHEMA_SIZE,
    OPENCLAW_TOOLS_COUNT,
)
results.append(r)

# C. LAAP v3
r = test_agent(
    "C. LAAP v3 (5工具)",
    LAAP_SYSTEM,
    [LAAP_MIN_TOOL],
    LAAP_SCHEMA_SIZE,
    LAAP_TOOLS_COUNT,
)
results.append(r)

# ════════════════════════════════════════════════════════════
# 对比表
# ════════════════════════════════════════════════════════════

print(f"\n\n{'='*70}")
print(f"  三家对比 — 同一个番茄闹钟任务")
print(f"{'='*70}")
print(f"{'Agent':25s} {'固定开销':>10s} {'Prompt':>8s} {'完成':>8s} {'总计':>8s} {'代码':>8s} {'缓存':>6s} {'耗时':>8s}")
print(f"{'-'*70}")
for r in results:
    print(f"{r['name']:25s} {r['overhead']:>8d}t {r['prompt']:>8d} {r['completion']:>8d} "
          f"{r['total']:>8d} {r['code_len']:>8d}c {r['cache_pct']:>5.0f}% {r['time_ms']:>8.0f}ms")

print(f"\n{'='*70}")
cheapest = min(results, key=lambda x: x['total'])
print(f"  最省: {cheapest['name']} ({cheapest['total']} tokens)")
print(f"  最多: {max(results, key=lambda x: x['total'])['total']} tokens")
print(f"  最大差距: {max(results, key=lambda x: x['total'])['total'] - cheapest['total']} tokens")
print(f"{'='*70}")

# 代码质量主观评分（文件大小作为参考）
print(f"\n  各 HTML 文件已保存到 D:/LAAP/benchmarks/")
print(f"  文件大小:")
import os as _os
for f in ["output_a.html", "output_b.html", "output_c.html"]:
    p = f"D:/LAAP/benchmarks/{f}"
    if _os.path.exists(p):
        print(f"    {f}: {_os.path.getsize(p)} bytes")
