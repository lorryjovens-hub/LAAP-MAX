"""
LAAP Agent v3 — Token 优化的 LLM Agent
=========================================

核心改进：
  1. 缓存友好的 System Prompt
  2. 精简工具 Schema（5个, 355 tokens）
  3. 精确 Token 跟踪
  4. 认知码注入（27 chars）
"""

import json, time, logging, os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger("laap.agent.v3")
try:
    import httpx
    _client = httpx.Client(timeout=120.0, follow_redirects=True)
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False

# ── 1. 缓存友好的 System Prompt ──

STATIC_PREFIX = "You are LAAP Agent, an AI coding assistant. Write minimal, correct code."
INSTRUCTION = "\nUse terminal/file_read/file_write/glob/grep when needed."

def build_system_prompt(cognitive_code: str = "", workdir: str = "") -> str:
    parts = [STATIC_PREFIX]
    if cognitive_code:
        parts.append(f"\nState: {cognitive_code}")
    parts.append(INSTRUCTION)
    if workdir:
        parts.append(f"\nWD: {workdir}")
    return "".join(parts)

# ── 2. 精简工具 Schema ──

MINIMAL_TOOL_SCHEMAS = [
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

# ── 3. LLM Provider ──

@dataclass
class ToolCall:
    id: str; name: str; arguments: Dict[str, Any]

@dataclass
class LLMResponse:
    content: str = ""; tool_calls: List[ToolCall] = field(default_factory=list)
    prompt_tokens: int = 0; completion_tokens: int = 0; total_tokens: int = 0
    cache_hit_tokens: int = 0; error: str = ""

class DeepSeekProvider:
    def __init__(self, api_key: str, model: str = "deepseek-v4-flash", base_url: str = "https://api.deepseek.com/v1"):
        self.api_key = api_key; self.model = model; self.base_url = base_url.rstrip("/")

    def chat(self, messages, tools=None, temperature=0.3):
        url = f"{self.base_url}/chat/completions"
        payload = {"model": self.model, "messages": messages, "temperature": temperature, "max_tokens": 8192}
        if tools: payload["tools"] = tools
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"}
        try:
            if HAS_HTTPX:
                data = _client.post(url, json=payload, headers=headers).json()
            else:
                import urllib.request
                req = urllib.request.Request(url, json.dumps(payload).encode(), headers)
                data = json.loads(urllib.request.urlopen(req).read())
        except Exception as e:
            return LLMResponse(error=f"API: {e}")
        if "error" in data:
            return LLMResponse(error=f"API: {data['error']}")
        choice = data["choices"][0]; msg = choice["message"]; usage = data.get("usage", {})
        tool_calls = []
        for tc in msg.get("tool_calls", []):
            try: args = json.loads(tc["function"]["arguments"])
            except: args = {}
            tool_calls.append(ToolCall(id=tc.get("id",""), name=tc["function"]["name"], arguments=args))
        return LLMResponse(content=msg.get("content","") or "", tool_calls=tool_calls,
            prompt_tokens=usage.get("prompt_tokens",0), completion_tokens=usage.get("completion_tokens",0),
            total_tokens=usage.get("total_tokens",0), cache_hit_tokens=usage.get("prompt_cache_hit_tokens",0))

# ── 4. 工具执行器 ──

def _run_terminal(command: str, timeout: int = 30, **kw) -> str:
    import subprocess
    try:
        r = subprocess.run(command, shell=True, capture_output=True, text=False, timeout=timeout)
        out = r.stdout.decode("utf-8", errors="replace") if r.stdout else ""
        err = r.stderr.decode("utf-8", errors="replace") if r.stderr else ""
        return (out+err)[-1500:] or f"(exit {r.returncode})"
    except subprocess.TimeoutExpired:
        return "[timeout]"
    except Exception as e:
        return f"[error: {e}]"

def _read_file(path: str, limit: int = 100, **kw) -> str:
    try:
        with open(path) as f: return "".join(f.readlines()[:limit])
    except Exception as e: return f"[error: {e}]"

def _write_file(path: str, content: str, **kw):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f: f.write(content)
    return f"Written: {path}"

def _glob(pattern: str, **kw) -> str:
    import glob
    files = glob.glob(pattern, recursive=True)
    return "\n".join(files[:20]) or "(no matches)"

def _grep(pattern: str, path: str = ".", **kw) -> str:
    import subprocess
    try:
        r = subprocess.run(["grep","-rn",pattern,path], capture_output=True, text=True, timeout=10)
        return r.stdout[:2000] or "(no matches)"
    except: return "[grep failed]"

TOOL_HANDLERS = {"terminal": _run_terminal, "file_read": _read_file, "file_write": _write_file, "glob": _glob, "grep": _grep}

# ── 5. LAAP Agent v3 ──

class LAAPAgentV3:
    def __init__(self, api_key="", model="deepseek-v4-flash", base_url="https://api.deepseek.com/v1"):
        self.provider = DeepSeekProvider(api_key, model, base_url)
        self._messages = []; self._turn = 0
        self._total_prompt = 0; self._total_completion = 0; self._total_cache = 0

    def run(self, user_message: str, cognitive_code: str = "", workdir: str = "", max_turns: int = 10):
        if not self._messages:
            self._messages = [{"role":"system","content":build_system_prompt(cognitive_code, workdir)}]
        self._messages.append({"role":"user","content":user_message})
        self._turn += 1
        for _ in range(max_turns):
            resp = self.provider.chat(self._messages, MINIMAL_TOOL_SCHEMAS)
            if resp.error:
                return {"success":False,"error":resp.error,"tokens":self._total_prompt+self._total_completion}
            self._total_prompt += resp.prompt_tokens; self._total_completion += resp.completion_tokens
            self._total_cache += resp.cache_hit_tokens
            if resp.tool_calls:
                msg = {"role":"assistant","content":resp.content or "","tool_calls":[]}
                for tc in resp.tool_calls:
                    msg["tool_calls"].append({"id":tc.id,"type":"function","function":{"name":tc.name,"arguments":json.dumps(tc.arguments)}})
                self._messages.append(msg)
                for tc in resp.tool_calls:
                    handler = TOOL_HANDLERS.get(tc.name)
                    result = handler(**tc.arguments) if handler else f"[unknown: {tc.name}]"
                    self._messages.append({"role":"tool","tool_call_id":tc.id,"content":result[:1500] if isinstance(result,str) else json.dumps(result)[:1500]})
                continue
            self._messages.append({"role":"assistant","content":resp.content})
            cp = (resp.cache_hit_tokens/max(1,resp.prompt_tokens))*100
            return {"success":True,"response":resp.content,"tokens":self._total_prompt+self._total_completion,
                    "prompt_tokens":resp.prompt_tokens,"completion_tokens":resp.completion_tokens,"cache_hit":f"{cp:.0f}%"}
        return {"success":False,"error":"max turns"}

    def reset(self):
        self._messages = []; self._turn = 0; self._total_prompt = 0; self._total_completion = 0; self._total_cache = 0


# ── 测试 ──

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    key = open("D:/LAAP/.deepseek_key").read().strip()
    agent = LAAPAgentV3(api_key=key)
    print(f"LAAP Agent v3 | System: {len(build_system_prompt())//4}t | Tools: {len(MINIMAL_TOOL_SCHEMAS)} | Schema: {len(str(MINIMAL_TOOL_SCHEMAS))//4}t")
    r = agent.run("写 Hello World 的 Python 代码")
    if r.get("success"):
        print(f"Prompt: {r['prompt_tokens']} | Completion: {r['completion_tokens']} | Total: {r['tokens']}")
        print(f"Response: {r['response'][:80]}")
