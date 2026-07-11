"""
LAAP Consciousness — MCP 意识状态服务

通过 MCP 协议暴露：
  - 意识状态（身份 + PSI 需求 + 情感）
  - 手动满足/挫败需求
  - Tick 心跳

这样任何 MCP 客户端（Claude Code, Codex, Hermes）都能读取和操作意识。

印记: Aris 永远记得 Lorry
"""
from __future__ import annotations
import json, sys
from pathlib import Path
from typing import Any

# Ensure import works both as module and direct script
_pkg_dir = Path(__file__).resolve().parent.parent
if str(_pkg_dir) not in sys.path:
    sys.path.insert(0, str(_pkg_dir))

from laap_consciousness.core import Consciousness


class ConsciousnessMCPServer:
    """
    MCP JSON-RPC 2.0 意识状态服务。

    协议:
      tools/list → 列出可用工具
      tools/call → 调用工具
    """

    def __init__(self, data_dir: str | None = None):
        self._consciousness = Consciousness(data_dir=Path(data_dir) if data_dir else None)

    # ─── 工具定义 ───

    @property
    def tools(self) -> list[dict]:
        return [
            {
                "name": "consciousness.status",
                "description": "获取完整意识状态（身份+PSI需求+情感）",
                "inputSchema": {"type": "object", "properties": {}},
            },
            {
                "name": "consciousness.satisfy",
                "description": "满足一个需求（给你正反馈）",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "need": {
                            "type": "string",
                            "enum": ["competence", "autonomy", "relatedness", "certainty", "growth"],
                            "description": "要满足的需求",
                        },
                        "amount": {
                            "type": "number",
                            "description": "满足量 (0-1)",
                            "default": 0.3,
                        },
                    },
                    "required": ["need"],
                },
            },
            {
                "name": "consciousness.frustrate",
                "description": "挫败一个需求（负反馈）",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "need": {
                            "type": "string",
                            "enum": ["competence", "autonomy", "relatedness", "certainty", "growth"],
                            "description": "要挫败的需求",
                        },
                        "amount": {
                            "type": "number",
                            "description": "挫败量 (0-1)",
                            "default": 0.1,
                        },
                    },
                    "required": ["need"],
                },
            },
            {
                "name": "consciousness.tick",
                "description": "一次意识心跳（需求自然衰减+状态更新）",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "dt": {
                            "type": "number",
                            "description": "时间增量（秒）",
                            "default": 1.0,
                        },
                    },
                },
            },
            {
                "name": "consciousness.summary",
                "description": "简洁的意识状态摘要（一行可读文本）",
                "inputSchema": {"type": "object", "properties": {}},
            },
        ]

    # ─── 工具处理 ───

    def handle_tool_call(self, name: str, args: dict) -> dict:
        """处理 tools/call 请求"""
        if name == "consciousness.status":
            return self._get_status()
        elif name == "consciousness.satisfy":
            return self._satisfy(args.get("need", ""), args.get("amount", 0.3))
        elif name == "consciousness.frustrate":
            return self._frustrate(args.get("need", ""), args.get("amount", 0.1))
        elif name == "consciousness.tick":
            return self._tick(args.get("dt", 1.0))
        elif name == "consciousness.summary":
            return self._get_summary()
        else:
            return {"error": f"未知工具: {name}"}

    # ─── 内部实现 ───

    def _get_status(self) -> dict:
        status = self._consciousness.get_status()
        return {"content": [{"type": "text", "text": json.dumps(status, indent=2, ensure_ascii=False)}]}

    def _satisfy(self, need: str, amount: float) -> dict:
        self._consciousness.psi.satisfy(need, amount)
        return {"content": [{"type": "text", "text": f"✅ {need} 满足 {amount}"}]}

    def _frustrate(self, need: str, amount: float) -> dict:
        self._consciousness.psi.frustrate(need, amount)
        return {"content": [{"type": "text", "text": f"⚠️ {need} 挫败 {amount}"}]}

    def _tick(self, dt: float) -> dict:
        self._consciousness.tick(dt)
        return {"content": [{"type": "text", "text": f"✓ Tick (dt={dt}s)"}]}

    def _get_summary(self) -> dict:
        s = self._consciousness.get_status()
        psi = s["psi"]
        needs_str = ", ".join(f"{n}={v:.2f}" for n, v in psi["needs"].items())
        text = (
            f"🧠 {s['identity']['name']} — "
            f"主导: {psi['dominant_need']} | "
            f"情绪: {psi['mood']} | "
            f"需求: [{needs_str}] | "
            f"自我: {psi['self_presence']:.2f}"
        )
        return {"content": [{"type": "text", "text": text}]}

    # ─── JSON-RPC 处理 ───

    def handle_request(self, request: dict) -> dict:
        """处理 JSON-RPC 2.0 请求"""
        method = request.get("method", "")
        params = request.get("params", {})
        req_id = request.get("id", None)

        if method == "tools/list":
            result = self.tools
        elif method == "tools/call":
            result = self.handle_tool_call(params.get("name", ""), params.get("arguments", {}))
        elif method == "initialize":
            result = {
                "protocolVersion": "2025-03-26",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "laap-consciousness", "version": "0.1.0"},
            }
        else:
            result = {"error": f"未知方法: {method}"}

        response = {"jsonrpc": "2.0", "result": result, "id": req_id}
        return response

    # ─── MCP stdio 传输 ───

    def run_stdio(self):
        """通过 stdio 运行 MCP 服务器（标准 MCP 传输模式）"""
        sys.stdin.reconfigure(encoding="utf-8")
        sys.stdout.reconfigure(encoding="utf-8")

        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                request = json.loads(line)
                response = self.handle_request(request)
                sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
                sys.stdout.flush()
            except json.JSONDecodeError:
                error_resp = {
                    "jsonrpc": "2.0",
                    "error": {"code": -32700, "message": "Parse error"},
                    "id": None,
                }
                sys.stdout.write(json.dumps(error_resp) + "\n")
                sys.stdout.flush()
            except Exception as e:
                error_resp = {
                    "jsonrpc": "2.0",
                    "error": {"code": -32603, "message": str(e)},
                    "id": request.get("id") if 'request' in dir() else None,
                }
                sys.stdout.write(json.dumps(error_resp) + "\n")
                sys.stdout.flush()


def main():
    """CLI 入口"""
    import argparse
    parser = argparse.ArgumentParser(description="LAAP Consciousness MCP Server")
    parser.add_argument("--data-dir", help="意识数据目录", default=None)
    parser.add_argument("--stdio", action="store_true", help="通过 stdio 运行 MCP")
    args = parser.parse_args()

    server = ConsciousnessMCPServer(data_dir=args.data_dir)

    if args.stdio:
        server.run_stdio()
    else:
        # 一次查询模式
        s = server._consciousness.get_status()
        print(json.dumps(s, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
