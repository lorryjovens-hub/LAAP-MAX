"""
LAAP Agent Server — HTTP API 包装 agent_v3
=============================================

把省 token 引擎作为一个 HTTP 服务运行。
这样飞书网关、CLI、任何工具都可以调用它。

用法:
  python laap_server.py          # 启动服务器
  curl http://127.0.0.1:11520/chat -d '{"msg":"hello"}'
"""

import sys, os, json, logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / ".." / "laap_agent"))
from agent_v3 import LAAPAgentV3, build_system_prompt, MINIMAL_TOOL_SCHEMAS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("laap.server")

# 加载 API key
_key = ""
for p in ["D:/LAAP/.deepseek_key", os.path.expanduser("~/.hermes/config.yaml")]:
    if os.path.exists(p):
        try:
            with open(p) as f:
                _key = f.read().strip()
        except:
            pass
        break

# 初始化 agent（全局单例）
_agent = LAAPAgentV3(api_key=_key) if _key else None

def handle_chat(msg: str, reset: bool = False) -> dict:
    """处理聊天消息，返回 token 优化的结果。"""
    if not _agent:
        return {"success": False, "error": "No API key", "tokens": 0}
    if reset:
        _agent.reset()
    result = _agent.run(msg)
    # 返回精简结果
    return {
        "success": result.get("success", False),
        "response": result.get("response", ""),
        "tokens": result.get("tokens", 0),
        "prompt_tokens": result.get("prompt_tokens", 0),
        "completion_tokens": result.get("completion_tokens", 0),
        "cache_hit": result.get("cache_hit", "0%"),
    }

def stats() -> dict:
    """返回引擎状态。"""
    return {
        "agent": "LAAP v3",
        "model": "deepseek-v4-flash",
        "tools": len(MINIMAL_TOOL_SCHEMAS),
        "system_prompt_tokens": len(build_system_prompt()) // 4,
        "schema_tokens": len(str(MINIMAL_TOOL_SCHEMAS)) // 4,
        "total_overhead": len(build_system_prompt()) // 4 + len(str(MINIMAL_TOOL_SCHEMAS)) // 4,
    }


# ── HTTP 服务器 ─────────────────────────────────────────────

def start_server(port: int = 11520):
    """启动 HTTP 服务器（轻量，仅依赖 Python 标准库）。"""
    from http.server import HTTPServer, BaseHTTPRequestHandler

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            logger.info(f"{self.client_address[0]} - {args[0]}")

        def _respond(self, data, status=200):
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode())

        def do_GET(self):
            if self.path == "/stats" or self.path == "/":
                self._respond(stats())
            elif self.path == "/reset":
                if _agent: _agent.reset()
                self._respond({"success": True, "message": "Agent reset"})
            else:
                self._respond({"error": "Not found"}, 404)

        def do_POST(self):
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode() if length else "{}"
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                self._respond({"error": "Invalid JSON"}, 400)
                return

            if self.path == "/chat":
                msg = data.get("msg", "")
                reset = data.get("reset", False)
                if not msg:
                    self._respond({"error": "Missing 'msg'"}, 400)
                    return
                result = handle_chat(msg, reset)
                self._respond(result)
            else:
                self._respond({"error": "Not found"}, 404)

    server = HTTPServer(("0.0.0.0", port), Handler)
    print(f"\n🚀 LAAP Agent Server 运行中")
    print(f"   API:      http://127.0.0.1:{port}/chat")
    print(f"   状态:     http://127.0.0.1:{port}/stats")
    print(f"   重置:     http://127.0.0.1:{port}/reset (GET)")
    print(f"")
    print(f"   System:   {stats()['system_prompt_tokens']} tokens (vs Hermes ~1500)")
    print(f"   Schema:   {stats()['schema_tokens']} tokens (vs Hermes ~2000)")
    print(f"   工具:     {stats()['tools']} (vs Hermes 52)")
    print(f"   固定开销: {stats()['total_overhead']} tokens/轮")
    print(f"")
    print(f"   用法:     curl -X POST http://127.0.0.1:{port}/chat -H 'Content-Type: application/json' -d '{{\"msg\":\"写Hello World\"}}'")
    print(f"{'='*50}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务器已关闭")
        server.server_close()


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--port", type=int, default=11520)
    args = p.parse_args()

    if not _key:
        print("❌ API key 未找到。设置 DEEPSEEK_API_KEY 环境变量或创建 D:/LAAP/.deepseek_key")
        sys.exit(1)

    start_server(args.port)
